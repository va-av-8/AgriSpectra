from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from pydantic import EmailStr
from database.database import get_session
from models.user import Users
from models.transaction import Transactions
from models.prediction import Predictions
from models.ml_task import MLTasks
from services.crud import user as UserService
from services.crud import transaction as TransactionService
from services.crud import service as PredictService


admin_route = APIRouter(tags=['Admin'], prefix='/admins')


@admin_route.get('/users', response_model=List[Users])
async def get_all_users(email: EmailStr,
                        session=Depends(get_session)) -> List[Users]:
    """Возвращает всех пользователей"""
    user = UserService.get_user_by_email(email, session)
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Admin access required")

    return UserService.get_all_users(user, session)


@admin_route.post('/balance/replenish')
async def add_balance_to_user(admin_email: EmailStr, user_email: EmailStr,
                              amount: float,
                              session=Depends(get_session)) -> dict:
    """Пополнение баланса пользователю"""
    admin = UserService.get_user_by_email(admin_email, session)
    user = UserService.get_user_by_email(user_email, session)
    if not admin.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Admin acssess required")

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User does not exist")

    if UserService.add_balance_to_user(admin, user.user_id,
                                       amount, session) is None:
        return {"message": f'{amount} added to user {user.email}'}


@admin_route.get('/transactions', response_model=List[Transactions])
async def view_all_transactions(email: EmailStr,
                                session=Depends(get_session)) -> List[Transactions]:
    """Возвращает все успешно завершенные транзакции"""
    user = UserService.get_user_by_email(email, session)
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Admin access required")

    return TransactionService.view_all_transactions(user, session)


@admin_route.get('/predictions', response_model=List[Predictions])
async def get_predictions_all(email: EmailStr,
                              session=Depends(get_session)) -> List[Predictions]:
    """Возвращает все успешно завершенные предсказания"""
    user = UserService.get_user_by_email(email, session)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User with this email does not exist")

    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Admin access required")

    return PredictService.get_all_predictions(user, session)


@admin_route.get('/tasks', response_model=List[MLTasks])
async def get_tasks_all(email: EmailStr,
                        session=Depends(get_session)) -> List[MLTasks]:
    """Возвращает все отправленные таски RabbitMQ"""
    user = UserService.get_user_by_email(email, session)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User with this email does not exist")

    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Admin access required")

    return PredictService.get_all_tasks(user, session)
