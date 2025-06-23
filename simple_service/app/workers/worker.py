import pika
import json
import os, glob, logging
import io
import time
import joblib
import ee
import requests
import numpy as np
import torch
import wandb
import torchvision.transforms as T
from PIL import Image
from sqlmodel import Session, select
from typing import Dict
from datetime import datetime, timedelta

from database.database import engine
from database.config import get_settings
from models.ml_task import MLTasks
from models.prediction import Predictions
from models.model import Models
from models.user_images import UserImages
from models.recommendation import Recommendation
from services.crud import user as UserService
from workers.connect import connect_to_rabbitmq


# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.info("Worker starting up, connecting to RabbitMQ…")

settings = get_settings()
device = torch.device("cpu")

image_size = (256, 256)
mean = (0.4536, 0.4510, 0.3253)
std = (0.2462, 0.2511, 0.2887)

preprocess = T.Compose([
        T.Resize(image_size),
        T.ToTensor(),
        T.Normalize(mean=mean, std=std)
    ])

def ml_task(ch, method, properties, body):
    try:
        with Session(engine) as session:
            msg = json.loads(body)
            task = session.get(MLTasks, msg["task_id"])
            user = UserService.get_user_by_id(msg["user_id"], session)
            model_ent = session.get(Models, msg["model_id"])
            raw_id = msg.get("image_id")
            image_id = int(raw_id)
            logging.info(f"Loading UserImages[{image_id}]")
            user_img = session.get(UserImages, image_id)

            raw_latitude = msg.get("latitude")
            raw_longitude = msg.get("longitude")
            
            # Конвертируем в float, обрабатывая различные случаи
            latitude = None
            longitude = None
            
            try:
                if raw_latitude is not None and raw_latitude != "" and raw_latitude != "null":
                    latitude = float(raw_latitude)
                    logging.info(f'Converted latitude: {raw_latitude} -> {latitude}')
            except (ValueError, TypeError) as e:
                logging.warning(f'Failed to convert latitude "{raw_latitude}": {e}')
                
            try:
                if raw_longitude is not None and raw_longitude != "" and raw_longitude != "null":
                    longitude = float(raw_longitude)
                    logging.info(f'Converted longitude: {raw_longitude} -> {longitude}')
            except (ValueError, TypeError) as e:
                logging.warning(f'Failed to convert longitude "{raw_longitude}": {e}')
            
            # Логируем финальные координаты
            logging.info(f'Final coordinates - latitude: {latitude}, longitude: {longitude}')

            if not user_img:
                raise RuntimeError(f"Image with id={image_id} not found in UserImages")

            # Скачиваем модель-артефакт из WandB
            logging.info(f"Task {msg['task_id']}: downloading model/artifact")
            api = wandb.Api()
            artifact = api.artifact(msg["artifact_path"], type="model")
            art_dir = artifact.download()
            raw = artifact.metadata["inverse_label_maps"]
            label_maps = {
                head: {int(k): v for k, v in mapping.items()}
                for head, mapping in raw.items()
            }

            # Ищем скриптованный файл
            scripted_candidates = glob.glob(os.path.join(art_dir, "*_scripted.pt"))
            if not scripted_candidates:
                raise FileNotFoundError(f"No *_scripted.pt in {art_dir}")
            scripted_path = scripted_candidates[0]
            logging.info("Using scripted model file: %s", scripted_path)

            # Загружаем скриптованную модель на CPU
            model = torch.jit.load(scripted_path, map_location="cpu")
            model.eval()

            # Скачиваем изображение из MinIO (public URL)
            logging.info(f"Task {msg['task_id']}: model loaded, downloading image")
            resp = requests.get(user_img.internal_url)
            resp.raise_for_status()
            img = Image.open(io.BytesIO(resp.content)).convert("RGB")

            # Препроцессинг
            x = preprocess(img).unsqueeze(0).to(device)
            logging.info(f"Shape before model: {tuple(x.shape)}")  # ожидаем (1, 3, 256, 256)
            logging.info(f"Task {msg['task_id']}: start inference")
            t0 = time.time()

            # Инференс
            with torch.no_grad():
                out = model(x)  # ожидаем dict: head_name -> logits Tensor

            elapsed = time.time() - t0
            logging.info(f"Task {msg['task_id']}: inference done in {elapsed:.3f}s")

            preds: Dict[str, float] = {}
            # Если out — не dict, приводим к единственной голове
            if isinstance(out, dict):
                for head_name, logits in out.items():
                    if torch.is_tensor(logits):
                        # для классификации: argmax
                        val = logits.argmax(dim=1).item()
                    else:
                        val = float(logits)
                    preds[head_name] = val
            else:
                # один выход
                val = out.argmax(dim=1).item() if torch.is_tensor(out) else float(out)
                preds = {"default": val}

            # Сохраняем предсказание в БД
            readable = {h: label_maps[h][v] for h, v in preds.items()}

            # Severity (предполагаем, что в prediction_result есть ключ 'extent')
            extent = float(readable["extent"])
            if 10 <= extent < 40:
                sev = "low"
            elif 40 <= extent < 70:
                sev = "medium"
            elif 70 <= extent <= 100:
                sev = "high"
            else:
                sev = "low"

            if latitude is not None and longitude is not None:
                logging.info(f'Processing valid coordinates - latitude: {latitude}, longitude: {longitude}')
                # Подключаемся к Google Earth Engine
                service_account = 'earthengine-service@agrispectra.iam.gserviceaccount.com'
                credentials = ee.ServiceAccountCredentials(service_account, '/app/workers/earthengine-key.json')
                ee.Initialize(credentials)
                point = ee.Geometry.Point([longitude, latitude])
                end_date = datetime.now()
                start_date = end_date - timedelta(days=10)
                end_date_str = end_date.strftime('%Y-%m-%d')
                start_date_str = start_date.strftime('%Y-%m-%d')

                # Определяем стадию роста, Sentinel-1
                # Загружаем артефакт модели с wandb
                logging.info(f"Task {msg['task_id']}: loading growth stage model")
                run = wandb.init(project="growth-and-moisture-kmeans", job_type="inference")
                artifact = run.use_artifact('a-gapeeva/growth-and-moisture-kmeans/growth-kmeans:latest', type='model')
                artifact_dir = artifact.download()

                # Загружаем модель K-means для стадии роста
                model_files = glob.glob(os.path.join(artifact_dir, "*.pkl"))
                if not model_files:
                    model_files = glob.glob(os.path.join(artifact_dir, "*.joblib"))

                if model_files:
                    model_sent = joblib.load(model_files[0])
                    class_labels_growth = ["S", "V", "F", "M"]  # Seedling, Vegetative, Flowering, Maturity

                    # Получаем данные Sentinel-1 для точки
                    sentinel1 = ee.ImageCollection('COPERNICUS/S1_GRD') \
                        .filterBounds(point) \
                        .filterDate(start_date_str, end_date_str) \
                        .select(['VH']) \
                        .median()

                    # Извлекаем значения для точки
                    sentinel_data = sentinel1.reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=point,
                        scale=10,
                        maxPixels=1e9
                    ).getInfo()
                    
                    # Подготавливаем данные для модели (пример признаков)
                    if 'VH' in sentinel_data and sentinel_data['VH'] is not None:
                        vh = sentinel_data['VH']
                        # Создаем одномерный признак для модели
                        features_growth = np.array([[vh]])
                        
                        # Получаем предсказание
                        growth_prediction = model_sent.predict(features_growth)[0]
                        predicted_growth_stage = class_labels_growth[growth_prediction]
                        logging.info(f"Predicted growth stage: {predicted_growth_stage}")
                    else:
                        predicted_growth_stage = "unknown"
                        logging.warning("Failed to get Sentinel-1 data")
                else:
                    predicted_growth_stage = "unknown"
                    logging.warning("Growth model file not found")
                
                wandb.finish()

                # Проверяем, если предсказанная стадия роста отличается от исходной
                original_growth_stage = readable.get("growth_stage", "unknown")
                if predicted_growth_stage != "unknown" and predicted_growth_stage != original_growth_stage:
                    logging.info(f"Updating growth stage from {original_growth_stage} to {predicted_growth_stage}")
                    readable["growth_stage"] = predicted_growth_stage
            else:
                logging.info(f"Invalid or missing coordinates (lat: {latitude}, lon: {longitude}), skipping satellite data processing")

            # Берём рекомендацию
            rec_obj = session.exec(
                select(Recommendation)
                .where(
                    Recommendation.damage_type == readable["damage"],
                    Recommendation.growth_stage == readable["growth_stage"],
                    Recommendation.severity == sev
                )
            ).one_or_none()

            if rec_obj:
                severity = sev
                recommendation = rec_obj.recommendation
                source = rec_obj.source
            else:
                severity = sev
                recommendation = "Рекомендации не найдены для данного сочетания"
                source = None
                
            logging.info(f"⛳️ Saving to DB with coordinates: lat={latitude}, lon={longitude} (types: {type(latitude)}, {type(longitude)})")
            pred_rec = Predictions(
                user_id=user.user_id,
                model_id=model_ent.model_id,
                input_data=user_img.input_data,
                input_photo_url=user_img.image_url,
                input_latitude=latitude,
                input_longitude=longitude,
                prediction_result=readable,
                cost=model_ent.cost,
                recommendation=recommendation,
                severity=severity,
                source=source
            )

            session.add(pred_rec)
            session.commit()
            session.refresh(pred_rec)

            # Обновляем задачу
            task.prediction_id = pred_rec.prediction_id
            task.task_status = "complete"
            task.prediction_result = readable
            session.add(task)
            session.commit()

            # Списываем баланс
            UserService.deduct_balance(user.user_id, model_ent.cost, session)

        ch.basic_ack(method.delivery_tag)

    except Exception as e:
        logging.error(f"Worker error: {e}", exc_info=True)
        ch.basic_nack(method.delivery_tag)


connection = connect_to_rabbitmq()
channel = connection.channel()

channel.queue_declare(queue=settings.RMQ_QUEUE,
                      durable=True
                      )
channel.basic_consume(queue=settings.RMQ_QUEUE,
                      on_message_callback=ml_task,
                      auto_ack=False
                      )

try:
    logging.info("Waiting for messages. For exit press Ctrl+C")
    logging.info(f"Declaring queue '{settings.RMQ_QUEUE}' and starting consume loop")
    channel.start_consuming()
except KeyboardInterrupt:
    logging.info(" [INFO] Остановка по Ctrl+C")
except Exception as e:
    logging.info(f"[ERROR] Consumer crashed: {e}")
