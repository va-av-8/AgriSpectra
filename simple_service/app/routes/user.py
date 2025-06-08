import logging
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import List, Dict, Any, Annotated

from database.database import get_session
from models.user import Users
from models.transaction import BalanceUpdate
from services.crud import user as UserService
from services.crud import transaction as TransactionService
from services.crud import service as PredictService
from webui.auth.hash_password import HashPassword
from webui.auth.jwt_handler import create_access_token
from webui.auth.authenticate import authenticate_user


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

user_route = APIRouter(tags=['User'], prefix='/user')
hash_password = HashPassword()


@user_route.post('/signup')
async def signup(user: Users, session=Depends(get_session)) -> dict:
    user_exist = UserService.get_user_by_email(user.email, session)
    if user_exist:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="User with this email already exists")
    hashed_password = hash_password.create_hash(user.password)
    user.password = hashed_password
    UserService.create_user(user, session)
    return {"message": "User successfully registered!"}


@user_route.post('/signin')
async def signin(data: Annotated[OAuth2PasswordRequestForm, Depends()],
                 session=Depends(get_session)) -> dict:
    logging.info(f"Received data: {data}")
    user_exist = UserService.authenticate(data.username, data.password, session)
    if user_exist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User with this email does not exist")

    if hash_password.verify_hash(data.password, user_exist.password):
        access_token = create_access_token(user_exist.user_id)
        return {"access_token": access_token, "token_type": "Bearer", "username": user_exist.username}

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                        detail="Wrong credentials passed")


@user_route.post('/balance/replenish')
async def add_balance(user_id: Annotated[int, Depends(authenticate_user)],
                      balance_update: BalanceUpdate,
                      session=Depends(get_session)) -> dict:
    user = UserService.get_user_by_id(user_id, session)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User does not exist")

    if balance_update.amount <= 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Amount should be greater then 0")
    if UserService.add_balance(user_id, balance_update.amount, session) is not None:
        raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User does not exist or amount less or equal to 0")

    return {"message": f"{balance_update.amount} added to your balance"}


@user_route.get('/balance')
async def check_balance(user_id: Annotated[int, Depends(authenticate_user)],
                        session=Depends(get_session)) -> dict:
    user = UserService.get_user_by_id(user_id, session)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User does not exist")
    balance = UserService.check_balance(user_id, session)
    return {"message": f"Your balance is {balance}", "balance": f"{balance}"}


@user_route.get('/transactions')
async def get_transactions_by_user(
        user_id: Annotated[int, Depends(authenticate_user)],
        session=Depends(get_session)) -> List[Dict[str, Any]]:
    user = UserService.get_user_by_id(user_id, session)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User does not exist")
    transactions = TransactionService.get_transactions_by_user(user_id, session)
    return [
            {
                "id": transaction.transaction_id,
                "type": transaction.transaction_type,
                "amount": transaction.amount,
                "created_at": transaction.timestamp.isoformat()
            } for transaction in transactions
        ]


@user_route.get('/predictions')
async def get_predictions_user(
        user_id: Annotated[int, Depends(authenticate_user)],
        session=Depends(get_session)) -> List[Dict[str, Any]]:
    user = UserService.get_user_by_id(user_id, session)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User with this email does not exist")
    predictions = PredictService.get_predictions_by_user(user_id, session)
    return [
            {
                "id": prediction.prediction_id,
                "model_id": prediction.model_id,
                "input_photo_url": prediction.input_photo_url,
                "prediction_result": prediction.prediction_result,
                "created_at": prediction.timestamp.isoformat(),
                "cost": prediction.cost
            } for prediction in predictions
        ]
