import pytest

from fastapi.testclient import TestClient
from api import app
from sqlmodel import SQLModel, Session, create_engine
from database.database import get_session
from sqlalchemy.pool import StaticPool
from services.crud.user import get_user_by_email


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///testing.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def reset_db(session):
    session.rollback()

    # Полностью удаляем и пересоздаём схему БД
    SQLModel.metadata.drop_all(session.bind)
    SQLModel.metadata.create_all(session.bind)

    session.commit()


@pytest.fixture(name="test_user")
def test_user_fixture(client: TestClient, session: Session):
    signup_response = client.post(
        "/user/signup",
        json={
            "username": "test_user1",
            "password": "test_password1",
            "email": "user1@example.com",
            "balance": 50,
        },
    )
    assert signup_response.status_code == 200

    # Логинимся для получения токена
    signin_response = client.post(
        "/user/signin",
        data={
            "username": "user1@example.com",
            "password": "test_password1",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert signin_response.status_code == 200
    token = signin_response.json()["access_token"]

    user = get_user_by_email("user1@example.com", session)
    assert user is not None, "Пользователь не был создан"

    return {"user": user, "token": token}
