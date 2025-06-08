import pika
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from database.config import get_settings


# Настройка логирования (перед сдачей финального проекта настрою в отдельном модуле)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

settings = get_settings()


# Подключениe
def get_connection_params() -> pika.ConnectionParameters:
    """Возвращает параметры подключения к RabbitMQ."""
    return pika.ConnectionParameters(
        host=settings.RMQ_HOST,
        port=settings.RMQ_PORT,
        virtual_host='/',
        credentials=pika.PlainCredentials(
            username=settings.RMQ_USERNAME,
            password=settings.RMQ_PASSWORD,
        ),
        heartbeat=60,
        blocked_connection_timeout=60
    )


# Установка соединения
# С библиотекой tenacity ретраи стали гораздо удобнее
@retry(
    stop=stop_after_attempt(10),  # Останов после 10 попыток
    wait=wait_exponential(multiplier=2, min=2, max=30),  # Экспоненциальная задержка от 2 до 30 сек
    reraise=True  # Проброс исключения после исчерпания попыток
)
def connect_to_rabbitmq() -> pika.BlockingConnection:
    """Подключается к RabbitMQ с автоматическими ретраями."""
    logging.info("Попытка подключения к RabbitMQ...")
    connection = pika.BlockingConnection(get_connection_params())
    logging.info("Успешное подключение к RabbitMQ")
    return connection
