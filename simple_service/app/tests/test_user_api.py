from fastapi.testclient import TestClient


def test_signup_user(client: TestClient):
    user_data = {
        "username": "test_user2",
        "password": "test_password2",
        "email": "user2@example.com",
    }
    response_signup = client.post("/user/signup", json=user_data)
    assert response_signup.status_code == 200
    assert response_signup.json()["message"] == "User successfully registered!"

    response = client.post("/user/signup", json=user_data)
    assert response.status_code == 409
    assert response.json()["detail"] == "User with this email already exists"


def test_signin_user(client: TestClient, test_user):
    response = client.post(
        "/user/signin",
        data={"username": "user1@example.com", "password": "test_password1"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_signin_user_not_exist(client: TestClient):
    response = client.post(
        "/user/signin",
        data={"username": "users@examples.com", "password": "test_password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User with this email does not exist"
