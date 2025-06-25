from typing import List, Optional
from models.user import Users
from services.crud.transaction import create_transaction


def create_user(new_user: Users, session) -> None:
    session.add(new_user)
    session.commit()
    session.refresh(new_user)


def authenticate(email: str, password: str, session) -> Optional[Users]:
    user = session.query(Users).filter(Users.email == email
                                       and Users.password == password).first()
    if user:
        return user
    # else:
    #     raise ValueError("User does not exist")


def get_all_users(user: Users, session) -> List[Users]:
    if user.is_admin:
        return session.query(Users).all()
    else:
        return print('Sorry, you are not the admin')


def get_user_by_id(id: int, session) -> Optional[Users]:
    user = session.get(Users, id)
    if user:
        return user
    else:
        raise ValueError("User does not exist")


def get_user_by_email(email: str, session) -> Optional[Users]:
    user = session.query(Users).filter(Users.email == email).first()
    if user:
        return user
    # else:
    #     raise ValueError("User does not exist")


def add_balance(user_id: int, amount: float, session) -> None:
    user = session.get(Users, user_id)
    if user:
        if amount > 0:
            user.balance += amount
            create_transaction(session, user_id, amount, "deposit")
            print(f"{amount} added to user id: {user_id} balance")
            session.add(user)
            session.commit()
            session.refresh(user)
        else:
            raise ValueError("Not enough credits")
    else:
        raise ValueError("User does not exist")


def deduct_balance(user_id: int, amount: float, session) -> None:
    user = session.get(Users, user_id)
    if user and amount > 0 and user.balance >= amount:
        user.balance -= amount
        create_transaction(session, user_id, amount, "deduct")
        print(f"{amount} deducted from your balance")
        session.add(user)
        session.commit()
        session.refresh(user)
        return True
    return False


def check_balance(user_id: int, session) -> float:
    user = session.get(Users, user_id)
    if user:
        return user.balance
    else:
        raise ValueError("User does not exist")


def add_balance_to_user(user: Users, user_to_add_id: int,
                        amount, session) -> None:
    if not user.is_admin:
        raise ValueError("Admin acсess required")

    add_balance(user_to_add_id, amount, session)


def get_admin(session) -> Optional[Users]:
    admin = session.query(Users).filter(Users.is_admin == True).first()
    if admin:
        return admin
    else:
        raise ValueError("Admin does not exist")
