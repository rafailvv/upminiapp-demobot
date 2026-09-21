# Telegram Mini App Demo Bot

Демо-бот для конструктора телеграм-мини апп с использованием aiogram.

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd upminiapp-demobot
```

2. Создайте виртуальное окружение:
```bash
python -m venv .venv
source .venv/bin/activate  # для Linux/Mac
# или
.venv\Scripts\activate  # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` на основе `env.example`:
```bash
cp env.example .env
```

5. Отредактируйте файл `.env` и добавьте:
   - `BOT_TOKEN` - токен вашего телеграм бота (получите у @BotFather)
   - `DOMAIN` - домен для ваших мини-приложений
   - `FORM_RES_OPERATOR_IDS` - Telegram ID операторов, которым разрешена выгрузка ответов форм; перечисляйте ID через запятую. Пустое или некорректное значение закрывает доступ.

## Запуск

### Локальный запуск

```bash
python bot.py
```

### Запуск через Docker

1. Убедитесь, что у вас установлены Docker и Docker Compose

2. Создайте файл `.env` на основе `env.example`:
```bash
cp env.example .env
```

3. Отредактируйте файл `.env` и добавьте:
   - `BOT_TOKEN` - токен вашего телеграм бота (получите у @BotFather)
   - `DOMAIN` - домен для ваших мини-приложений
   - `FORM_RES_OPERATOR_IDS` - Telegram ID операторов, которым разрешена выгрузка ответов форм; перечисляйте ID через запятую. Пустое или некорректное значение закрывает доступ.

4. Запустите бота через Docker Compose:
```bash
docker-compose up --build
```

5. Для запуска в фоновом режиме:
```bash
docker-compose up -d --build
```

6. Для остановки:
```bash
docker-compose down
```

## Функциональность

- При команде `/start` бот отправляет приветственное сообщение
- Содержит ссылку на политику обработки персональных данных Upmini.app
- Выгрузка ответов форм через `/form_res <form_id>` разрешена только Telegram ID из `FORM_RES_OPERATOR_IDS` и только в личном чате с ботом
- Под сообщением отображается кнопка "Меню" для открытия мини-приложения
- Кнопка открывает ссылку `/miniapp/menu` на указанном домене

## Структура проекта

```
upminiapp-demobot/
├── bot.py              # Основной файл бота
├── config.py           # Конфигурация и загрузка переменных окружения
├── requirements.txt    # Зависимости Python
├── .env               # Переменные окружения (создается пользователем)
├── env.example        # Пример файла переменных окружения
├── .gitignore         # Исключения для Git
├── Dockerfile         # Docker образ
├── docker-compose.yml # Docker Compose конфигурация
├── .dockerignore      # Исключения для Docker
└── README.md          # Документация
```

## Требования

- Python 3.8+
- aiogram 3.4.1
- python-dotenv 1.0.0
