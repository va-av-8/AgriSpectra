from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
from .jwt_handler import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/signin")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Модель данных для хранения информации о токене.
    """
    user_id: Optional[int] = None


def authenticate_user(token: str = Depends(oauth2_scheme)):
    """
    Функция для проверки подлинности пользователя по токену.
    Расшифровывает токен и проверяет его валидность.
    Возвращает user_id пользователя.
    """
    try:
        payload = decode_access_token(token)
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user_id
