import time
from datetime import datetime
from fastapi import HTTPException, status
from jose import jwt, JWTError
from database.config import get_settings


settings = get_settings()
SECRET_KEY = settings.SECRET_KEY


def create_access_token(user_id: int) -> str:
    """
    Создание токена из user_id с использованием jwt.
    """
    payload = {
        "user_id": user_id,
        "expires": time.time() + 3600
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def decode_access_token(token: str) -> dict:
    """
    Получение email из токена с использованием jwt.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY,
                             algorithms=["HS256"])
        expire = payload.get("expires")
        if expire is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token supplied"
            )
        if datetime.utcnow() > datetime.utcfromtimestamp(expire):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token expired!"
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )
