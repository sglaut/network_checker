FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY ./app/requirements.txt /app

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY ./app/main.py /app

# Создаем пользователя и группу
RUN groupadd -r appgroup && useradd -r -g appgroup -s /bin/bash appuser

# Создаем директорию для логов и даем права
RUN mkdir -p /app/logs && chown -R appuser:appgroup /app

USER appuser

# Запускаем приложение
CMD ["python", "main.py"]