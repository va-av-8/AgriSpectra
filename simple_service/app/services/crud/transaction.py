from models.transaction import Transactions
from typing import List
from models.user import Users


def create_transaction(session, user_id: int, amount: float,
                       transaction_type: str) -> None:
    transaction = Transactions(user_id=user_id,
                               amount=amount,
                               transaction_type=transaction_type
                               )
    session.add(transaction)
    session.commit()
    session.refresh(transaction)


def get_transactions_by_user(user_id: int, session) -> List[Transactions]:
    return session.query(Transactions).filter(Transactions.user_id ==
                                              user_id).all()


def view_all_transactions(user: Users, session) -> List[Transactions]:
    user = session.get(Users, user.user_id)
    if user.is_admin:
        return session.query(Transactions).all()
    else:
        return print('Sorry, you are not the admin')
