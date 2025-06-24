import streamlit as st
import requests
import logging
import time
import pandas as pd
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
            time.sleep(1)
            st.session_state.logged_in = False
            st.session_state.current_page = "Вход"
            st.rerun()
        elif e.response.status_code == 403:
            st.error("Неверный пароль!")
            time.sleep(1)
            st.session_state.logged_in = False
            st.session_state.current_page = "Вход"
            st.rerun()
        elif e.response.status_code == 409:
            st.error("Этот пользователь уже существует!")
            time.sleep(1)
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
    st.title("🌱 Вход в систему")
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
                time.sleep(1)
                st.session_state.logged_in = False
                st.session_state.current_page = "Вход"
                st.rerun()
            elif e.response.status_code == 403:
                st.error("Неверный пароль!")
                time.sleep(1)
                st.session_state.logged_in = False
                st.session_state.current_page = "Вход"
                st.rerun()


# Страница регистрации
def signup_page():
    st.title("🌱 Регистрация")
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
    st.title("🌱 Личный кабинет")
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
            "/user/balance/replenish",
            {"amount": amount}
            )
        if response and response.status_code == 200:
            st.success("Баланс успешно пополнен")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Ошибка пополнения баланса")

    # Модели, доступные для работы
    st.subheader("Доступные модели")
    response = api_request("GET", "/service/models/")
    if response and response.status_code == 200:
        models = response.json()
        if models:
            df_models = pd.DataFrame(models)

            # Переименуем столбцы для удобства отображения
            df_models = df_models.rename(columns={
                "model_id": "ID модели",
                "name": "Название",
                "description": "Описание",
                "cost": "Стоимость"
            })

            df_models_dspl = df_models[["Название", "Описание", "Стоимость"]]
            df_models_dspl["Стоимость"] = df_models_dspl["Стоимость"].astype(int)
            df_models_dspl = df_models_dspl.reset_index(drop=True)

            def render_html_table(df):
                html = "<table style='width:100%; border-collapse:collapse;'>"
                html += "<thead><tr>" + "".join(f"<th style='border:1px solid #ddd; padding:8px; text-align:left'>{col}</th>" for col in df.columns) + "</tr></thead>"
                html += "<tbody>"
                for _, row in df.iterrows():
                    html += "<tr>"
                    for cell in row:
                        cell_html = str(cell).replace('\n', '<br>')
                        html += "<td style='border:1px solid #ddd; padding:8px; vertical-align:top'>{}</td>".format(cell_html)
                    html += "</tr>"
                html += "</tbody></table>"
                st.markdown(html, unsafe_allow_html=True)

            # Выводим таблицу
            render_html_table(df_models_dspl)
        else:
            st.write("База ML моделей пуста")
    else:
        st.error("Ошибка получения списка моделей")

    st.subheader("Получение рекомендаций по уходу")
   
    # Выбор модели
    model_names = df_models["Название"].tolist()
    selected_name = st.selectbox("Выберите модель", model_names)
    model_id = int(df_models[df_models["Название"] == selected_name]["ID модели"].values[0])

    # Ввод координат
    lat_input = st.text_input("Широта (от -90 до 90)", placeholder="необязательно")
    lon_input = st.text_input("Долгота (от -180 до 180)", placeholder="необязательно")

    # Преобразуем строки в float или None
    def parse_coord(val, min_val, max_val):
        try:
            f = float(val)
            if min_val <= f <= max_val:
                return f
            else:
                st.warning(f"Значение должно быть между {min_val} и {max_val}")
                return None
        except ValueError:
            return None

    lat = parse_coord(lat_input, -90, 90) if lat_input else None
    lon = parse_coord(lon_input, -180, 180) if lon_input else None

    # Флаг для обновления file_uploader
    if "uploader_key" not in st.session_state:
        st.session_state["uploader_key"] = "uploader_1"

    uploaded_file = st.file_uploader(
        "Загрузите изображение", 
        type=["jpg", "jpeg", "png"], 
        key=st.session_state["uploader_key"]
    )

    # При загрузке нового файла — очищаем предыдущее состояние
    if uploaded_file:
        st.session_state.pop("last_result", None)
        st.session_state["current_image_file"] = uploaded_file

    # Если изображение уже есть в сессии — отображаем его
    if "current_image_file" in st.session_state:
        st.image(st.session_state["current_image_file"], caption="Загруженное изображение", width=500)

    # Кнопка для отправки на предсказание
    if st.button("🌱 Получить рекомендации"):
        if "current_image_file" not in st.session_state:
            st.warning("Сначала загрузите изображение.")
            st.stop()

        # Сброс предыдущих результатов
        st.session_state.pop("last_result", None)

        # Загрузка изображения на сервер
        with st.spinner("Загрузка изображения..."):
            uploaded_file = st.session_state["current_image_file"]
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            token = st.session_state.get('token')
            headers = {"Authorization": f"Bearer {token}"}

            response = requests.post(f"{API_URL}/service/upload", files=files, headers=headers)

            if response.status_code != 201:
                st.error("Ошибка при загрузке изображения")
                st.stop()

            img_data = response.json()[0]
            image_id = img_data["image_id"]
            image_url = img_data["image_url"]

            # Сохраняем URL для отображения результата
            st.session_state["uploaded_image_url"] = image_url
            # st.image(image_url, caption="Загруженное изображение", width=300)

        # Запрос предсказания
        with st.spinner("Отправка изображения на обработку..."):
            payload = {
                "model_id": model_id,
                "image_id": image_id,
                **({"latitude": lat} if lat is not None else {}),
                **({"longitude": lon} if lon is not None else {}),
            }

            post = api_request("POST", "/service/prediction", payload)

            if not post or post.status_code != 202:
                st.error("Ошибка при отправке на предсказание")
                st.stop()

            task_id = post.json().get("task_id")

        # Ожидание завершения
        with st.spinner("Обработка изображения, подождите..."):
            for _ in range(30):
                time.sleep(1)
                status = api_request("GET", f"/service/tasks/{task_id}")
                if status and status.status_code == 200:
                    items = status.json()
                    if any(item.get("status") == "complete" for item in items):
                        break
            else:
                st.error("Превышено время ожидания обработки")
                st.stop()

        # Получение предсказания
        get_preds = api_request("GET", "/user/predictions")
        if not get_preds or get_preds.status_code != 200:
            st.error("Не удалось получить результаты предсказания")
            st.stop()

        preds = get_preds.json()
        rec = next((p for p in reversed(preds) if p.get("prediction_id") == task_id), None)
        if not rec and preds:
            rec = preds[-1]

        if rec:
            st.session_state["last_result"] = {
                "image_url": rec["input_photo_url"],
                "result": rec.get("prediction_result", "—")
            }
        else:
            st.error("Предсказание не найдено")

    # Кнопка для очистки результата и изображения
    if st.button("Очистить вывод"):
        st.session_state.pop("current_image_file", None)
        st.session_state.pop("uploaded_image_url", None)
        st.session_state.pop("last_result", None)

        # Перегенерируем ключ, чтобы принудительно перерисовать file_uploader
        st.session_state["uploader_key"] = f"uploader_{time.time()}"
        st.experimental_rerun()

    # Отображение результата (если есть)
    if "last_result" in st.session_state:
        st.markdown("---")
        # st.image(st.session_state["last_result"]["image_url"], caption="Изображение из предсказания", width=300)
        st.markdown(f"**Рекомендации по уходу:** {st.session_state['last_result']['result']}")
        st.success("Готово!")

    # История предсказаний
    st.subheader("История запросов")

    if st.button("Показать историю запросов"):
        response = api_request("GET", "/user/predictions")

        if response and response.status_code == 200:
            history = response.json()
            if history:
                for item in history:
                    public_url = item.get('input_photo_url', '')
                    st.write(f"Дата: {item.get('created_at', 'Нет данных')}, ")
                    st.write(f"Модель: {item.get('model_id', 'Нет данных')}")
                    st.markdown(f'<img src="{public_url}" width="200">', unsafe_allow_html=True)
                    st.write(f"Координаты, широта: {item.get('latitude')}, долгота: {item.get('longitude')}")
                    st.write(f"Стоимость: {item.get('cost', 'Нет данных')}")
                    st.write(f"Идентификатор предсказания: {item.get('id', 'Нет данных')}")
                    st.write(f"Рекомендации: {item.get('prediction_result', 'Нет данных')}")
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
    st.title("🌱 Добро пожаловать в AgriSpectra")
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
