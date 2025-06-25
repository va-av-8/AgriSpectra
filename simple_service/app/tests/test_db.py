from sqlmodel import Session
from database.database import get_session
from models.user import Users
from models.model import Models
from services.crud.user import get_user_by_id
from services.crud.service import get_model_by_id


def test_database_connection():
    if get_session() is not None:
        assert True


def test_create_user(session: Session):
    user = Users(email="test_2@mail.ru", password="123", username="Adamas")
    session.add(user)
    session.commit()
    user_created = get_user_by_id(1, session)
    assert user_created.email == user.email


def test_create_model(session: Session):
    model_record = Models(
        artifact_path='a-gapeeva/eotg-multilabel/resnet18_bsl_cpu:latest',
        name='resnet18_baseline',
        description='Predicts damage type, damage extent \
                      and grow stagw for maize, based on ResNet18',
        cost=8
    )
    session.add(model_record)
    session.commit()
    model_created = get_model_by_id(1, session)
    assert model_created.artifact_path == model_record.artifact_path
