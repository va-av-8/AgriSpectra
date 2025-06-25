from fastapi.testclient import TestClient
from services.crud.transaction import create_transaction
from sqlmodel import Session


def test_check_balance(client: TestClient, test_user):
    token = test_user["token"]
    response = client.get(
        "/user/balance",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "balance" in data
    assert float(data["balance"]) == 50.0


def test_topup_balance(client: TestClient, test_user):
    token = test_user["token"]
    response = client.post(
        "/user/balance/replenish",
        headers={"Authorization": f"Bearer {token}"},
        json={"amount": 20},
    )
    assert response.status_code == 200
    assert "message" in response.json()

    # Проверка обновлённого баланса
    balance_resp = client.get("/user/balance", headers={"Authorization": f"Bearer {token}"})
    assert balance_resp.status_code == 200
    assert float(balance_resp.json()["balance"]) == 70.0


def test_get_transactions(client: TestClient, test_user, session: Session):
    user_id = test_user["user"].user_id
    create_transaction(session, user_id, 10, "deposit")
    session.commit()

    token = test_user["token"]
    response = client.get(
        "/user/transactions",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    transactions = response.json()
    assert isinstance(transactions, list)
    assert len(transactions) > 0

    first_transaction = transactions[0]
    assert first_transaction["type"] == "deposit"
    assert first_transaction["amount"] == 10
