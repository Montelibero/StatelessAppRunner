FROM python:3.10-slim

WORKDIR /app

# Отключаем создание .pyc файлов
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app

# Запуск через uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
