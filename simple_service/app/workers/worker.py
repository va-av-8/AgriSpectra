import pika
import json
import os, glob, logging
import io
import time
import requests
from PIL import Image
import torch
import torchvision.transforms as T
import wandb
from sqlmodel import Session
from typing import Dict

from database.database import engine
from database.config import get_settings
from models.ml_task import MLTasks
from models.prediction import Predictions
from models.model import Models
from models.user_images import UserImages
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
    session = Session(engine)
    try:
        msg = json.loads(body)
        task = session.get(MLTasks, msg["task_id"])
        user = UserService.get_user_by_id(msg["user_id"], session)
        model_ent = session.get(Models, msg["model_id"])
        raw_id = msg.get("image_id")
        image_id = int(raw_id)
        logging.info(f"Loading UserImages[{image_id}]")
        user_img = session.get(UserImages, image_id)

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
        # если out — не dict, приводим к единственной голове
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

        pred_rec = Predictions(
            user_id=user.user_id,
            model_id=model_ent.model_id,
            input_data=user_img.input_data,
            input_photo_url=user_img.image_url,
            prediction_result=readable,
            cost=model_ent.cost,
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

        # списываем баланс
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
