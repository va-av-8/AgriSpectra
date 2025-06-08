import streamlit as st
import requests
import logging
import time
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from auth.jwt_handler import decode_access_token


# Настройка логирования (перед сдачей финального проекта настрою в отдельном модуле)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Основной адрес API
API_URL = "http://app:8080"

load_dotenv()


class Settings(BaseSettings):
    SECRET_KEY: str


settings = Settings()
SECRET_KEY = settings.SECRET_KEY


def set_token(token):
    st.session_state.token = token
    st.session_state.logged_in = True


def get_token():
    token = st.session_state.get("token", None)
    if token is None:
        return None
    return str(token)


def remove_token():
    st.session_state["token"]


# Инициализация session_state
def initialize_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Главная"
    if "available_pages" not in st.session_state:
        st.session_state.available_pages = {
            "Главная": main_page,
            "Вход": signin_page,
            "Регистрация": signup_page
        }
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'token' not in st.session_state:
        st.session_state.token = None


# Функция для выполнения запросов к API с токеном
def api_request(method, endpoint, data=None):
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"{API_URL}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            logging.info(f"Sent data: {data}")
            response = requests.post(url, json=data, headers=headers)
        else:
            raise ValueError("Unsupported HTTP method")

        response.raise_for_status()  # Вызовет исключение для статус-кодов 4xx/5xx
        return response

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            st.error("Сессия истекла. Пожалуйста, войдите снова.")
            remove_token()
            st.session_state.logged_in = False
            st.session_state.current_page = "Вход"
            st.rerun()
        elif e.response.status_code == 404:
            st.error("Введены некорректные данные")
            time.sleep(5)
            st.session_state.logged_in = False
            st.session_state.current_page = "Вход"
            st.rerun()
        elif e.response.status_code == 403:
            st.error("Неверный пароль!")
            time.sleep(5)
            st.session_state.logged_in = False
            st.session_state.current_page = "Вход"
            st.rerun()
        elif e.response.status_code == 409:
            st.error("Этот пользователь уже существует!")
            time.sleep(5)
            st.session_state.logged_in = False
            st.session_state.current_page = "Вход"
            st.rerun()
        else:
            st.error(f"Ошибка API: {e}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка запроса: {e}")
        return None


# Страница входа в систему
def signin_page():
    st.title("Вход в систему")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Пароль", type="password", key="login_password")
    login_button = st.button("Войти")

    if login_button:
        try:
            response = requests.post(f"{API_URL}/user/signin", data={"username": email, "password": password})
            response.raise_for_status()
            if response and response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                set_token(token)
                logging.info(f"Токен сохранён: {get_token()}")
                st.session_state.username = data.get("username")
                st.session_state.current_page = "Личный кабинет"
                st.success("Вход выполнен успешно")
                logging.info(f"Перед перезагрузкой: {st.session_state}")
                time.sleep(3)
                st.rerun()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                st.error("Введены некорректные данные")
                time.sleep(5)
                st.session_state.logged_in = False
                st.session_state.current_page = "Вход"
                st.rerun()
            elif e.response.status_code == 403:
                st.error("Неверный пароль!")
                time.sleep(5)
                st.session_state.logged_in = False
                st.session_state.current_page = "Вход"
                st.rerun()


# Страница регистрации
def signup_page():
    st.title("Регистрация")
    email = st.text_input("Email", key="register_email")
    password = st.text_input("Пароль", type="password", key="register_password")
    username = st.text_input("Имя пользователя", key="register_username")
    register_button = st.button("Зарегистрироваться")

    if register_button:
        response = api_request("POST", "/user/signup", {"email": email,
                                                        "password": password,
                                                        "username": username})
        if response and response.status_code == 200:
            st.session_state.current_page = "Вход"
            st.success("Регистрация выполнена успешно")
            time.sleep(3)
            st.rerun()
        else:
            st.error("Ошибка регистрации")


# Страница личного кабинета
def dashboard_page():
    st.title("Личный кабинет")
    if not st.session_state.logged_in or not st.session_state.user_id:
        st.error("Сначала войдите в систему")
        st.session_state.current_page = "Вход"
        st.rerun()
        return

    st.write(f"Добро пожаловать, {st.session_state.username}!")

    # Отображение текущего баланса
    response = api_request("GET", "/user/balance")
    if response and response.status_code == 200:
        balance = response.json().get("balance")
        st.write(f"Текущий баланс: {balance} кредитов")
    else:
        st.error("Ошибка получения текущего баланса")

    # Пополнение баланса
    st.subheader("Пополнение баланса")
    amount = st.number_input("Сумма пополнения (в кредитах)", min_value=0)
    if st.button("Пополнить баланс"):
        response = api_request(
            "POST",
            f"/user/balance/replenish",
            {"amount": amount}
            )
        if response and response.status_code == 200:
            st.success("Баланс успешно пополнен")
            time.sleep(3)
            st.rerun()
        else:
            st.error("Ошибка пополнения баланса")

    # Модели, доступные для работы
    st.subheader("Доступные модели")
    response = api_request("GET", "/service/models/")
    if response and response.status_code == 200:
        models = response.json()
        if models:
            for item in models:
                st.write(
                    f"ID модели: {item.get('model_id', 'Нет данных')}, "
                    f"Название: {item.get('name', 'Нет данных')}, "
                    f"Описание: {item.get('description', 'Нет данных')}, "
                    f"Стоимость: {item.get('cost', 'Нет данных')}"
                            )
        else:
            st.write("База ML моделей пуста")
    else:
        st.error("Ошибка получения списка моделей")

    # Запрос предсказания
    st.subheader("Запрос предсказания")

    model_id = st.number_input("ID модели", min_value=1, value=1)

    if 'uploaded_image_id' not in st.session_state:
        uploaded_file = st.file_uploader("Загрузите изображение", type=["jpg", "png", "jpeg"])

        if uploaded_file:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            token = st.session_state.get('token')
            headers = {"Authorization": f"Bearer {token}"}

            response = requests.post(
                f"{API_URL}/service/upload",
                files=files,
                headers=headers
            )

            if response.status_code == 201:
                img_data = response.json()[0]
                st.session_state.uploaded_image_id = img_data['image_id']
                public_url = img_data['image_url']
                st.session_state.uploaded_image_url = public_url
                st.success(f"Изображение успешно загружено. ID изображения: {img_data['image_id']}")
                st.markdown(f'<img src="{public_url}" width="200">', unsafe_allow_html=True)
            else:
                st.error("Ошибка загрузки изображения")
    else:
        st.image(st.session_state.uploaded_image_url)

    if 'uploaded_image_id' in st.session_state:
        if st.button("Выполнить предсказание"):
            response = api_request(
                "POST",
                "/service/prediction",
                {"model_id": model_id,
                 "image_id": st.session_state.uploaded_image_id}
            )
            if response and response.status_code == 202:
                result = response.json()
                task_id = result.get('task_id', 'Нет данных')
                cost = result.get('cost', 'Нет данных')
                st.success("Данные успешно отправлены для получения предсказания")
                st.write(f"Создана задача для ML сервиса, task_id: {task_id}")
                st.write(f"Списано кредитов: {cost}")
                del st.session_state.uploaded_image_id
                del st.session_state.uploaded_image_url
            else:
                st.error("Ошибка получения предсказания")


    # История тасок ML сервису
    st.subheader("Статусы заданий для ML сервиса")
    task_id = st.number_input("Идентификатор задачи, task_id", min_value=0)
    if st.button("Показать статусы заданий"):
        response = api_request(
            "GET",
            f"/service/tasks/{task_id}"
            )
        if response and response.status_code == 200:
            history = response.json()
            if history:
                for item in history:
                    st.write(
                        f"Дата: {item.get('created_at', 'Нет данных')}, "
                        f"Модель: {item.get('model_id', 'Нет данных')}, "
                        f"Ввод: {item.get('input_data', 'Нет данных')}, "
                        f"Статус: {item.get('status', 'Нет данных')}, "
                        f"Идентификатор предсказания: {item.get('prediction_id', 'Нет данных')}, "
                        f"Предсказанное качество: {item.get('prediction_result', 'Нет данных')}"
                             )
            else:
                st.write("История заданий пуста")
        else:
            st.error("Ошибка получения истории")

    # История предсказаний
    st.subheader("История предсказаний")

    if st.button("Показать историю предсказаний"):
        response = api_request("GET", "/user/predictions")

        if response and response.status_code == 200:
            history = response.json()
            if history:
                for item in history:
                    public_url = item.get('input_photo_url', '')
                    st.write(f"Дата: {item.get('created_at', 'Нет данных')}, ")
                    st.write(f"Модель: {item.get('model_id', 'Нет данных')}")
                    st.markdown(f'<img src="{public_url}" width="200">', unsafe_allow_html=True)
                    st.write(f"Стоимость: {item.get('cost', 'Нет данных')}")
                    st.write(f"Идентификатор предсказания: {item.get('id', 'Нет данных')}")
                    st.write(f"Предсказание: {item.get('prediction_result', 'Нет данных')}")
                    st.markdown("---")
            else:
                st.write("История предсказаний пуста")
        else:
            st.error("Ошибка получения истории")

    # История транзакций
    st.subheader("История транзакций")
    if st.button("Показать историю транзакций"):
        response = api_request("GET", "/user/transactions")
        if response and response.status_code == 200:
            history = response.json()
            if history:
                for item in history:
                    st.write(
                        f"Дата: {item.get('created_at', 'Нет данных')}, "
                        f"Тип: {item.get('type', 'Нет данных')}, "
                        f"Сумма: {item.get('amount', 'Нет данных')}"
                             )
            else:
                st.write("История предсказаний пуста")
        else:
            st.error("Ошибка получения истории")


# Главная страница
def main_page():
    st.title("Добро пожаловать в AgriSpectra")
    st.write("""
    AgriSpectra - это сервис для прогнозирования стадии роста кукурузы, типа и степени её повреждения.
    Наш сервис предоставляет следующие возможности:
    - Регистрация и авторизация пользователей
    - Просмотр и пополнение баланса (в условных кредитах)
    - Отправка запросов к нейросетям для получения предсказаний
    - Просмотр истории загруженных данных и полученных предсказаний

    Начните с регистрации или входа в систему, чтобы получить доступ ко всем функциям сервиса.
    """)


# Основной поток работы приложения
def main():
    initialize_session_state()

    st.sidebar.title("Навигация")

    token = get_token()

    if token:
        try:
            decoded_token = decode_access_token(token)
            if decoded_token:
                st.session_state.logged_in = True
                st.session_state.user_id = decoded_token.get("user_id")
                st.sidebar.write(f"Привет, {st.session_state.username}!")
            else:
                raise ValueError("Invalid token")
        except Exception as e:
            st.error(f"Ошибка проверки токена: {e}")
            st.session_state.logged_in = False
            remove_token()
    else:
        st.session_state.logged_in = False

    logging.info(f"Состояние после проверки: {st.session_state}")

    # Настраиваем навигацию в зависимости от статуса входа
    if st.session_state.logged_in:
        st.session_state.available_pages = {
            "Главная": main_page,
            "Личный кабинет": dashboard_page,
        }
    else:
        st.session_state.available_pages = {
            "Главная": main_page,
            "Вход": signin_page,
            "Регистрация": signup_page
        }

    if st.session_state.logged_in and st.sidebar.button("Выйти", key="logout_button"):
        remove_token()
        st.session_state.clear()  # Полностью очищаем session_state
        st.session_state.logged_in = False  # Перезаписываем флаг, чтобы он явно остался
        st.session_state.available_pages = {  
            "Главная": main_page,
            "Вход": signin_page,
            "Регистрация": signup_page
        }
        st.session_state.current_page = "Главная"
        st.rerun()

    # Обновляем навигацию в боковой панели
    page_names = list(st.session_state.available_pages.keys())
    selected_page = st.sidebar.radio("Перейти к", page_names, key="navigation")

    # Проверяем, изменилась ли страница
    if selected_page != st.session_state.current_page:
        st.session_state.current_page = selected_page
        st.rerun()

    # Отображаем текущую страницу
    if st.session_state.current_page in st.session_state.available_pages:
        st.session_state.available_pages[st.session_state.current_page]()
    else:
        st.error(f"Ошибка: страница '{st.session_state.current_page}' не найдена")
        main_page()


if __name__ == "__main__":
    main()
