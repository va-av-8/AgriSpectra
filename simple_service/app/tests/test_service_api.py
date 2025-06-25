import io
from fastapi.testclient import TestClient
from PIL import Image
from models.user_images import UserImages
from services.crud.service import create_model, get_model_by_id
from models.model import Models


def create_test_image_bytes():
    """Создаёт временное изображение в памяти."""
    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)
    return img_bytes


def test_upload_image(client: TestClient, session, test_user):
    img_bytes = create_test_image_bytes()

    files = {
        "file": ("test_image.jpg", img_bytes, "image/jpeg")
    }

    response = client.post(
        "/service/upload",
        files=files,
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert isinstance(data, list)
    assert "image_id" in data[0]
    assert "image_url" in data[0]

    # Проверим, что изображение действительно сохранилось в БД
    image_id = data[0]["image_id"]
    img_record = session.get(UserImages, image_id)
    assert img_record is not None
    assert img_record.image_url.startswith("http://")
    assert img_record.input_data.endswith(".jpg")


def test_get_predictions(client: TestClient, test_user):
    token = test_user["token"]

    response = client.get(
        "/user/predictions",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json() == []
