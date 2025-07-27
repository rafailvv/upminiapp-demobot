import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем токен бота из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Получаем домен для мини-приложений
DOMAIN = os.getenv('DOMAIN')

# Проверяем, что необходимые переменные установлены
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен в .env файле")

if not DOMAIN:
    raise ValueError("DOMAIN не установлен в .env файле") 