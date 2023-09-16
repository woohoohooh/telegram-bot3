import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

# Инициализация бота и диспетчера
bot = Bot(token='YOUR_BOT_TOKEN')
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)
dp.middleware.setup(LoggingMiddleware())

# Создаем базу данных SQLite
conn = sqlite3.connect('answers.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS answers
                  (user_id INTEGER, question_id INTEGER, answer TEXT)''')
conn.commit()

# Словарь вопросов и ответов
questions = {
    1: "Какая у вас фамилия?",
    2: "Какое ваше имя?",
    3: "Сколько вам лет?",
    # Добавьте другие вопросы здесь
}

# Главная функция для начала опроса
@dp.message_handler(commands=['start'])
async def start_survey(message: types.Message):
    await message.reply("Привет! Давайте начнем анкету. Ответьте на первый вопрос:",
                        reply_markup=get_keyboard(1))

# Функция для отправки вопросов и кнопок
async def send_question(message: types.Message, question_id: int):
    if question_id in questions:
        question_text = questions[question_id]
        markup = get_keyboard(question_id)
        await message.reply(question_text, reply_markup=markup)
    else:
        await message.reply("Спасибо за ответы! Анкета завершена.")

# Функция для создания клавиатуры с кнопками
def get_keyboard(question_id: int):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(KeyboardButton("Да"), KeyboardButton("Нет"))
    markup.add(KeyboardButton("Пропустить"))
    return markup

# Обработка ответов пользователя
@dp.message_handler(lambda message: message.text.lower() in ["да", "нет", "пропустить"])
async def process_answer(message: types.Message):
    user_id = message.from_user.id
    text = message.text.lower()

    if text == "пропустить":
        # Если пользователь пропускает вопрос, записываем пустой ответ
        answer = ""
    else:
        answer = text

    question_id = get_question_id(message)

    # Сохраняем ответ пользователя в базу данных
    cursor.execute("INSERT INTO answers (user_id, question_id, answer) VALUES (?, ?, ?)",
                   (user_id, question_id, answer))
    conn.commit()

    # Отправляем следующий вопрос
    next_question_id = question_id + 1
    send_question(message, next_question_id)

# Функция для получения номера текущего вопроса
def get_question_id(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("SELECT MAX(question_id) FROM answers WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    return (result[0] or 0) + 1

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
