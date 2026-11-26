
FROM python:3.12-slim

WORKDIR /app

# Системные зависимости OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Установка Python-зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование проекта
COPY src/ ./src/
COPY trained_models/ ./trained_models/

EXPOSE 7860

ENV GRADIO_SERVER_NAME=0.0.0.0

CMD ["python", "src/app.py"]
