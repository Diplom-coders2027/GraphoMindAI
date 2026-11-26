
.PHONY: help install run test lint docker-up docker-down clean

help:
	@echo "Доступные команды:"
	@echo "  make install      - Установка зависимостей"
	@echo "  make run          - Запуск приложения"
	@echo "  make test         - Запуск тестов"
	@echo "  make lint         - Проверка кода"
	@echo "  make docker-up    - Запуск Docker"
	@echo "  make docker-down  - Остановка Docker"
	@echo "  make clean        - Очистка временных файлов"

install:
	pip install -r requirements.txt

run:
	python src/app.py

test:
	pytest tests/

lint:
	ruff check src/ tests/

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
