import os
from dotenv import load_dotenv
from access_control import parse_operator_ids

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем токен бота из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Получаем домен для мини-приложений
DOMAIN = os.getenv('DOMAIN')

# Получаем тестовый домен для мини-приложений
DOMAIN_TEST = os.getenv('DOMAIN_TEST')

# Optional allowlist for exporting form responses. An empty or invalid value denies access.
FORM_RES_OPERATOR_IDS = parse_operator_ids(os.getenv('FORM_RES_OPERATOR_IDS'))

# Проверяем, что необходимые переменные установлены
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен в .env файле")

if not DOMAIN:
    raise ValueError("DOMAIN не установлен в .env файле")

if not DOMAIN_TEST:
    raise ValueError("DOMAIN_TEST не установлен в .env файле")
