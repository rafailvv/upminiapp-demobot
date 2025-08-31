import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN, DOMAIN, DOMAIN_TEST

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Создание клавиатуры с кнопкой для мини-приложения
def get_main_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Меню ресторана",
                    web_app=types.WebAppInfo(url=f"{DOMAIN}/miniapp/menu")
                ),
                InlineKeyboardButton(
                    text="Магазин одежды",
                    web_app=types.WebAppInfo(url=f"{DOMAIN}/miniapp/clothing_store")
                )
            ],
            [
                InlineKeyboardButton(
                    text="Книжный магазин",
                    web_app=types.WebAppInfo(url=f"{DOMAIN}/miniapp/books_store")
                ),
                InlineKeyboardButton(
                    text="Запись на консультацию",
                    web_app=types.WebAppInfo(url=f"{DOMAIN}/consultations")
                )
            ],
            [
                InlineKeyboardButton(
                    text="Спорт и питание",
                    web_app=types.WebAppInfo(url=f"{DOMAIN}/miniapp/sport-nutrition")
                )
            ]
        ]
    )
    return keyboard

# Создание клавиатуры с кнопкой для мини-приложения
def get_test_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Меню тестовое",
                    web_app=types.WebAppInfo(url=f"{DOMAIN_TEST}/miniapp/menu")
                )
            ]
        ]
    )
    return keyboard

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = "Демо-бот конструктора телеграм-мини апп"
    
    await message.answer(
        text=welcome_text,
        reply_markup=get_main_keyboard()
    )

# Обработчик команды /test
@dp.message(Command("test"))
async def cmd_start(message: types.Message):
    welcome_text = "Тестовый демо-приложения"

    await message.answer(
        text=welcome_text,
        reply_markup=get_test_keyboard()
    )

# Обработчик для всех остальных сообщений
@dp.message()
async def echo_message(message: types.Message):
    await message.answer(
        text="Используйте /start для начала работы с ботом",
        reply_markup=get_main_keyboard()
    )

# Главная функция
async def main():
    logging.info("Запуск бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 