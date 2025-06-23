from typing import List, Optional
from models.model import Models, ModelArtifactRead
from models.user import Users
from models.prediction import Predictions, PredictionRequest
from models.ml_task import MLTasks, MLTasksUpdate


def create_model(new_model: Models, session) -> None:
    """Создаёт запись о модели в БД"""
    session.add(new_model)
    session.commit()
    session.refresh(new_model)


def get_model_by_id(model_id: int, session) -> Optional[ModelArtifactRead]:
    """Получает запись о модели из БД по id"""
    model = session.get(Models, model_id)
    if model:
        return model
    # else:
    #     raise ValueError("Model does not exist")


def get_all_models(session) -> List[ModelArtifactRead]:
    """Получает все модели"""
    return session.query(Models).all()


def dict_to_list(dictionary: dict) -> List:
    """Преобразует словаь в список"""
    return '; '.join([f'{key.capitalize()}: {value}'
                      for key, value in dictionary.items()])


def save_prediction(user_id: int, model_id: int,
                    req: PredictionRequest,
                    prediction: float, credit_cost: float,
                    session) -> Optional[Predictions]:
    """Сохраняет и возвращает запись о предсказании в таблице predictions"""
    prediction_record = Predictions(
        user_id=user_id,
        model_id=model_id,
        input_data=req.image_id,
        prediction_result=prediction,
        cost=credit_cost,
    )
    session.add(prediction_record)
    session.commit()
    session.refresh(prediction_record)
    return prediction_record


def get_predictions_by_user(user_id: int, session) -> List[Predictions]:
    """Получает предсказания для пользователя из БД"""
    return session.query(Predictions).filter(Predictions.user_id ==
                                             user_id).all()


def get_all_predictions(user: Users, session) -> List[Predictions]:
    """Получает все предсказания из БД"""
    if user.is_admin:
        return session.query(Predictions).all()
    # else:
    #     return print('Sorry, you are not the admin')


def create_task(new_task: MLTasks, session):
    """Создаёт запись о таске RabbitMQ в БД"""
    session.add(new_task)
    session.commit()
    session.refresh(new_task)
    return new_task


def get_task_by_id(task_id: int, session):
    """Получает запись о таске RabbitMQ в БД"""
    task = session.get(MLTasks, task_id)
    if task:
        return task


def get_all_tasks(user: Users, session):
    """Получает все таски RabbitMQ из БД"""
    if user.is_admin:
        return session.query(MLTasks).all()


def update_task(task_id: int, new_data: MLTasksUpdate, session) -> MLTasks:
    """Обновляет запись о таске RabbitMQ в БД"""
    task = get_task_by_id(task_id, session)
    if task:
        task_data = new_data.dict(exclude_unset=True)
    for key, value in task_data.items():
        setattr(task, key, value)

    session.add(task)
    session.commit()
    session.refresh(task)
    return task
