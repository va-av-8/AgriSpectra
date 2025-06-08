import os
import uuid
import io
import logging
import pika
import json
from minio import Minio
from datetime import timedelta
from sqlalchemy import select, desc
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from typing import List, Dict, Any, Annotated

from database.database import get_session
from database.config import get_settings
from models.model import ModelArtifactRead, Models
from models.prediction import PredictionResponse, PredictionRequest
from models.user_images import UserImages
from models.ml_task import MLTasks
from services.crud import service as PredictService
from services.crud import user as UserService
from workers.connect import connect_to_rabbitmq
from webui.auth.authenticate import authenticate_user

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

service_route = APIRouter(tags=['Service'], prefix='/service')

settings = get_settings()

# Инициализация MinIO-клиента
_secure = os.getenv('MINIO_SECURE', 'false').lower() == 'true'

minio_client = Minio(
    endpoint=os.getenv('MINIO_ENDPOINT'),
    access_key=os.getenv('MINIO_ACCESS_KEY'),
    secret_key=os.getenv('MINIO_SECRET_KEY'),
    secure=_secure
)
bucket_name = os.getenv('MINIO_BUCKET_NAME')

logging.info(f"MINIO_SECURE raw: {os.getenv('MINIO_SECURE')} → secure flag: {_secure}")

# Проверяем наличие бакета, если нет — создаём
try:
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)
except Exception as e:
    raise RuntimeError(f"Cannot access or create MinIO bucket '{bucket_name}': {e}")


@service_route.get('/models', response_model=List[ModelArtifactRead])
async def get_all_models(session=Depends(get_session)):
    return session.query(Models).all()


@service_route.post('/upload', status_code=status.HTTP_201_CREATED)
async def upload_image(
    user_id: Annotated[int, Depends(authenticate_user)],
    session=Depends(get_session),
    file: UploadFile = File(...),
        ) -> List[Dict[str, Any]]:
    """
    Принимает изображение, загружает его в MinIO
    и сохраняет информацию в таблицу UserImages.
    """
    # Читаем содержимое файла
    data = await file.read()
    ext = os.path.splitext(file.filename)[1]
    object_name = f"{uuid.uuid4().hex}{ext}"

    # Загружаем в MinIO
    try:
        minio_client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=io.BytesIO(data),
            length=len(data),
            content_type=file.content_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка загрузки в хранилище: {e}"
        )

    # Генерируем presigned URL на чтение (например, сроком на 1 час)
    try:
        public_url = f"http://localhost:9000/{bucket_name}/{object_name}"   # доступен в браузере
        internal_url = f"http://minio:9000/{bucket_name}/{object_name}"     # доступен из контейнера
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось сформировать presigned URL: {e}"
        )

    # Сохраняем запись в БД
    user_image = UserImages(
    user_id=user_id,
    image_url=public_url,
    internal_url=internal_url,
    input_data=object_name
    )
    session.add(user_image)
    session.commit()
    session.refresh(user_image)

    return [{
        "image_id": user_image.image_id,
        "image_url": user_image.image_url
    }]


@service_route.post(
    "/prediction",
    response_model=PredictionResponse,
    status_code=status.HTTP_202_ACCEPTED
)
def send_data_to_predict(
    req: PredictionRequest,
    user_id: int = Depends(authenticate_user),
    session=Depends(get_session),
) -> PredictionResponse:
    # Проверяем пользователя
    user = UserService.get_user_by_id(user_id, session)
    if not user:
        raise HTTPException(404, "User not found")

    # Если image_id не указан — берём последнюю загруженную
    if req.image_id is None:
        stmt = (
            select(UserImages)
            .where(UserImages.user_id == user_id)
            .order_by(desc(UserImages.timestamp))
            .limit(1)
        )
        last_img = session.execute(stmt).scalars().first()
        if not last_img:
            raise HTTPException(404, "No uploaded images found for user")
        img = last_img
    else:
        img = session.get(UserImages, req.image_id)
        if not img:
            raise HTTPException(404, "Image not found")

    # Берём модель
    model_ent = session.get(Models, req.model_id)
    if not model_ent:
        raise HTTPException(404, "Model not found")

    # Проверяем баланс
    if user.balance < model_ent.cost:
        diff = model_ent.cost - user.balance
        raise HTTPException(
            403, f"Insufficient balance, top up for {diff}"
        )

    # Создаём задачу
    task = MLTasks(
        user_id=user_id,
        model_id=req.model_id,
        input_data=str(img.image_id),
        task_status="created",
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Публикуем в очередь
    payload = {
        "task_id": task.task_id,
        "user_id": user_id,
        "model_id": req.model_id,
        "artifact_path": model_ent.artifact_path,
        "image_id": img.image_id,
    }
    conn = connect_to_rabbitmq()
    ch = conn.channel()
    ch.queue_declare(queue=settings.RMQ_QUEUE, durable=True)
    ch.basic_publish(
        exchange="",
        routing_key=settings.RMQ_QUEUE,
        body=json.dumps(payload),
        properties=pika.BasicProperties(delivery_mode=2),
    )
    conn.close()

    return PredictionResponse(
        task_id=task.task_id,
        cost=model_ent.cost,
        message="Task queued"
    )


@service_route.get('/tasks/{task_id}/')
async def check_task_status(
        task_id: int,
        user_id: Annotated[int, Depends(authenticate_user)],
        session=Depends(get_session)):
    """Возвращает все таски в RabbitMQ для пользователя с их статусом"""
    user = UserService.get_user_by_id(user_id, session)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User with this email does not exist")
    task = PredictService.get_task_by_id(task_id, session)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Task with this id does not exist")
    return [
            {
                "id": task.task_id,
                "model_id": task.model_id,
                "input_data": task.input_data,
                "status": task.task_status,
                "prediction_id": task.prediction_id,
                "prediction_result": task.prediction_result,
                "created_at": task.timestamp.isoformat(),
            }
        ]
