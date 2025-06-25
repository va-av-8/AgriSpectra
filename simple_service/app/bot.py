import telebot
import json
from telebot import types

from models.user import Users
from models.request import PredictItem
from services.crud import user as UserService
from services.crud import service as PredService
from database.database import get_session, init_db


with open('config.json') as f:
    config = json.load(f)

token = config["telegram_token"]
bot = telebot.TeleBot(token)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    '''
    Display the commands and what are they intended for.
    '''
    bot.reply_to(message, build_help_message())
    markup = types.ReplyKeyboardMarkup()
    item_signup = types.KeyboardButton('/signup')
    item_signin = types.KeyboardButton('/signin')
    item_balance = types.KeyboardButton('/balance')
    item_replenish = types.KeyboardButton('/top-up')
    item_transactions = types.KeyboardButton('/transactions')
    item_prediction = types.KeyboardButton('/predict')
    item_pred_hist = types.KeyboardButton('/predictions')
    markup.row(item_signup, item_signin)
    markup.row(item_balance, item_replenish, item_transactions)
    markup.row(item_prediction, item_pred_hist)
    bot.send_message(message.chat.id, "\n\nЧтобы продолжить, введите команду \
                     или выберите ее непосредственно в нижнем меню.",
                     reply_markup=markup)


# Регистрация
@bot.message_handler(commands=['signup'])
def signup(message):
    bot.send_message(message.chat.id, "Введите ваш email:")
    bot.register_next_step_handler(message, get_email)


def get_email(message):
    email = message.text
    bot.send_message(message.chat.id, "Введите ваш логин:")
    bot.register_next_step_handler(message, lambda msg: get_username(msg, email))


def get_username(message, email):
    username = message.text
    bot.send_message(message.chat.id, "Введите пароль:")
    bot.register_next_step_handler(message, lambda msg: save_user(msg, email, username))


def save_user(message, email, username):
    password = message.text
    session = next(get_session())

    # Проверяем, нет ли уже такого email в базе
    existing_user = session.query(Users).filter(Users.email == email).first()
    if existing_user:
        bot.send_message(message.chat.id, "Этот email уже зарегистрирован!")
        return

    new_user = Users(email=email, username=username, password=password)
    UserService.create_user(new_user, session)
    bot.send_message(message.chat.id, "Регистрация успешна! ✅")


# Авторизация
@bot.message_handler(commands=["signin"])
def signin(message):
    bot.send_message(message.chat.id, "Введите ваш email:")
    bot.register_next_step_handler(message, check_email)


def check_email(message):
    email = message.text
    bot.send_message(message.chat.id, "Введите пароль:")
    bot.register_next_step_handler(message, lambda msg: verify_user(msg, email))


def verify_user(message, email):
    password = message.text
    session = next(get_session())

    try:
        user = UserService.authenticate(email, password, session)
        bot.send_message(message.chat.id, f"Добро пожаловать, {user.username}! ✅")
    except ValueError:
        bot.send_message(message.chat.id, "Ошибка входа! ❌ Проверьте email и пароль.")


# Пополнение баланса
@bot.message_handler(commands=["top-up"])
def add_balance_handler(message):
    bot.send_message(message.chat.id, "Введите ваш email:")
    bot.register_next_step_handler(message, process_balance_email)


def process_balance_email(message):
    email = message.text
    session = next(get_session())
    user = session.query(Users).filter(Users.email == email).first()
    if not user:
        bot.send_message(message.chat.id, "Ошибка: Пользователь не найден ❌")
        return
    bot.send_message(message.chat.id, "Введите сумму пополнения:")
    bot.register_next_step_handler(message, lambda msg: process_balance(msg, user.user_id))


def process_balance(message, user_id):
    try:
        amount = float(message.text)
        session = next(get_session())
        UserService.add_balance(user_id, amount, session)
        bot.send_message(message.chat.id, f"Баланс успешно пополнен на {amount} ✅")
    except ValueError as e:
        bot.send_message(message.chat.id, f"Ошибка: {str(e)}")


# Проверка баланса
@bot.message_handler(commands=["balance"])
def check_balance_handler(message):
    bot.send_message(message.chat.id, "Введите ваш email:")
    bot.register_next_step_handler(message, process_check_balance_email)


def process_check_balance_email(message):
    email = message.text
    session = next(get_session())
    user = session.query(Users).filter(Users.email == email).first()
    if not user:
        bot.send_message(message.chat.id, "Ошибка: Пользователь не найден ❌")
        return
    balance = UserService.check_balance(user.user_id, session)
    bot.send_message(message.chat.id, f"Ваш баланс: {balance} 💰")


# Получение предсказания
@bot.message_handler(commands=["predict"])
def predict_handler(message):
    bot.send_message(message.chat.id, "Введите ваш email:")
    bot.register_next_step_handler(message, get_user_for_prediction)


def get_user_for_prediction(message):
    email = message.text
    session = next(get_session())
    user = session.query(Users).filter(Users.email == email).first()
    if not user:
        bot.send_message(message.chat.id, "Ошибка: Пользователь не найден ❌")
        return
    bot.send_message(message.chat.id, "Введите ID модели:")
    bot.register_next_step_handler(message, lambda msg: get_model_id(msg, user.user_id))


def get_model_id(message, user_id):
    try:
        model_id = int(message.text)
        session = next(get_session())
        model = PredService.get_model_by_id(model_id, session)
        if not model:
            bot.send_message(message.chat.id, "Модель не найдена ❌")
            return
        fields = list(PredictItem.__annotations__.keys())
        ask_for_input(message.chat.id, user_id, model, fields, {})
    except ValueError:
        bot.send_message(message.chat.id, "Ошибка: Некорректный ID модели ❌")


def ask_for_input(chat_id, user_id, model, fields, data):
    if not fields:
        session = next(get_session())
        predict_item = PredictItem(**data)
        result = PredictItem.process_request(model, user_id, predict_item, session)
        if "error" in result:
            bot.send_message(chat_id, f"Ошибка: {result['error']} ❌")
        else:
            bot.send_message(chat_id, f"Предсказанное значение: {result['predicted_quality']} ✅")
        return
    field = fields[0]
    bot.send_message(chat_id, f"Введите значение для {field}:")
    bot.register_next_step_handler_by_chat_id(chat_id, lambda msg: collect_input(msg, chat_id, user_id, model, fields[1:], data, field))


def collect_input(message, chat_id, user_id, model, fields, data, field):
    try:
        data[field] = float(message.text)
        ask_for_input(chat_id, user_id, model, fields, data)
    except ValueError:
        bot.send_message(chat_id, "Ошибка: Введите корректное числовое значение ❌")
        ask_for_input(chat_id, user_id, model, [field] + fields, data)


def build_help_message():
    '''
    Helper method to build the bot help message
    '''
    return "\n \
SimpleMLServiceBot предсказывает качество вина по его составу.\n \
\n \
Команды для взаимодействия с ботом: \n \
\n \
/signup - регистрация \n \
/signin - авторизация \n \
/balance - проверка баланса \n \
/top-up - пополнение баланса \n \
/transactions - история транзакций \n \
/predict - выполнение предсказания \n \
/predictions - история предсказаний \n \
\n"


# init_db()
# bot.polling()

while True:
    try:
        init_db()
        bot.polling(none_stop=True)
    except:
        print("Telegram API timeout happened")
