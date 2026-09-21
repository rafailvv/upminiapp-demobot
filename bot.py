import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import BOT_TOKEN, DOMAIN, DOMAIN_TEST, FORM_RES_OPERATOR_IDS
from form_handler import POLICY_URL, handle_form_res_command

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Создание главной клавиатуры
def get_main_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Меню",
                    callback_data="menu"
                ),
                InlineKeyboardButton(
                    text="Запись на консультацию",
                    web_app=types.WebAppInfo(url=f"{DOMAIN}/consultations/?id=4e08b859-f884-40ea-b3fe-636f0b7e6bb2")
                )
            ],
            [
                InlineKeyboardButton(
                    text="Спорт и питание",
                    web_app=types.WebAppInfo(url=f"{DOMAIN}/miniapp/sport-nutrition")
                ),
                InlineKeyboardButton(
                    text="Квиз",
                    web_app=types.WebAppInfo(url=f"{DOMAIN}/miniapp/quiz")
                )
            ],
            [InlineKeyboardButton(text="Политика обработки персональных данных", url=POLICY_URL)]
        ]
    )
    return keyboard

# Создание клавиатуры для меню магазинов
def get_menu_keyboard() -> InlineKeyboardMarkup:
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
                )
            ],
            [
                InlineKeyboardButton(
                    text="← Назад",
                    callback_data="back_to_main"
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


def get_privacy_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Политика обработки персональных данных", url=POLICY_URL)]
        ]
    )

# Создание клавиатуры для cust_dev
def get_cust_dev_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Заполнить анкету",
                    web_app=types.WebAppInfo(url=f"{DOMAIN}/miniapp/cust_dev")
                )
            ],
            [InlineKeyboardButton(text="Политика обработки персональных данных", url=POLICY_URL)]
        ]
    )
    return keyboard

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Проверяем, есть ли параметры в команде
    command_args = message.text.split()
    
    if len(command_args) > 1 and command_args[1] == "cust_dev":
        # Специальное сообщение для cust_dev
        welcome_text = """👋 Мы команда Upmini.app — создаём автоматизированное решение в Telegram с мини-приложениями для экспертов и малого бизнеса.
Нам важно понять, как вы работаете с клиентами, чтобы сделать инструмент, который действительно экономит время и помогает зарабатывать.

Заполнение займёт не больше 5–7 минут.

По итогам — участники получат ранний доступ и готовое решение под свои задачи."""
        
        await message.answer(
            text=welcome_text,
            reply_markup=get_cust_dev_keyboard()
        )
    else:
        # Обычное приветственное сообщение
        welcome_text = (
            "Демо-бот конструктора Telegram мини-приложений от команды Upmini.app\n\n"
            "Политика обработки персональных данных доступна по кнопке ниже."
        )
        
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

# Обработчик команды /form_res
@dp.message(Command("form_res"))
async def cmd_form_res(message: types.Message):
    """Обработчик команды /form_res для получения ответов формы"""
    await handle_form_res_command(message, FORM_RES_OPERATOR_IDS)


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "Команды бота:\n"
        "/start — открыть демо-меню\n"
        "/help — справка и политика обработки персональных данных\n\n"
        "Выгрузка ответов форм через /form_res доступна только настроенным операторам.",
        reply_markup=get_privacy_keyboard(),
    )

# Обработчик для callback-кнопки "Меню"
@dp.callback_query(lambda c: c.data == "menu")
async def process_menu_callback(callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.edit_text(
        text="Выберите магазин:",
        reply_markup=get_menu_keyboard()
    )

# Обработчик для callback-кнопки "Назад"
@dp.callback_query(lambda c: c.data == "back_to_main")
async def process_back_callback(callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.edit_text(
        text="Демо-бот конструктора телеграм-мини апп",
        reply_markup=get_main_keyboard()
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
