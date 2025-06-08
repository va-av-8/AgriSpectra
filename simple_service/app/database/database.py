from sqlmodel import SQLModel, Session, create_engine
from .config import get_settings
from models.user import Users
from models.model import Models
from services.crud.user import create_user
from services.crud.service import create_model
from webui.auth.hash_password import HashPassword


engine = create_engine(url=get_settings().DATABASE_URL_psycopg,
                       echo=True, pool_size=15, max_overflow=20)


def get_session():
    """Генератор сессий для FastAPI"""
    with Session(engine) as session:
        yield session


hash_password = HashPassword()


def init_db():
    """Инициализирует БД, создаёт записи о тестовых пользователях и моделях"""
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

# Initialise some start data in database:
    hashed_password = hash_password.create_hash('test')
    test_user_1 = Users(email='test1@example.com', username='Adam',
                        password=hashed_password, balance=50)
    test_user_2 = Users(email='test2@mail.ru', username='Adam1',
                        password=hashed_password, balance=5)
    test_user_3 = Users(email='test3@mail.ru', username='Adam2',
                        password=hashed_password)
    admin = Users(email='admin@example.com', username='Ana',
                  password=hashed_password, is_admin=True)
    test_model_1 = Models(
        artifact_path='a-gapeeva/eotg-multilabel/resnet18_bsl_cpu:latest',
        name='resnet18_baseline',
        description='Predicts damage type, damage extent \
                      and grow stagw for maize, based on ResNet18',
        cost=8
        )
    test_model_2 = Models(
        artifact_path='a-gapeeva/eotg-multilabel/effb0_bsl_cpu:latest',
        name='effb0_baseline',
        description='Predicts damage type, damage extent \
                      and grow stagw for maize, based on EfficientNet-B0',
        cost=15
        )

    with Session(engine) as session:
        create_user(test_user_1, session)
        create_user(test_user_2, session)
        create_user(test_user_3, session)
        create_user(admin, session)
        create_model(test_model_1, session)
        create_model(test_model_2, session)


if __name__ == "__main__":
    init_db()
