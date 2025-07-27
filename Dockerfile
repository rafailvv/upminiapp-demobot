# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash bot

# Создаем директорию для логов и устанавливаем права
RUN mkdir -p /app/logs && \
    chown -R bot:bot /app

USER bot

# Запускаем бота
CMD ["python", "bot.py"] 