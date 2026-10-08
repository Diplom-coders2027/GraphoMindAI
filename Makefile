# ==============================================================================
# Makefile — команды быстрого управления проектом
# ==============================================================================

.PHONY: help install run test lint docker-up docker-down clean

help:
	@echo "Доступные команды:"
	@echo "  make install      - Установка зависимостей проекта"
	@echo "  make run          - Локальный запуск приложения"
	@echo "  make test         - Запуск тестов"
	@echo "  make lint         - Проверка кода линтерами"
	@echo "  make docker-up    - Сборка и запуск контейнеров в фоне"
	@echo "  make docker-down  - Остановка контейнеров проекта"
	@echo "  make clean        - Очистка временных файлов и кэша"

# 1. Установка зависимостей (раскомментируйте нужное под ваш стек)
install:
	@echo "Установка зависимостей..."
	# Python: pip install -r requirements.txt
	# Node.js: npm install
	# Go: go mod download

# 2. Локальный запуск приложения
run:
	@echo "Запуск приложения..."
	# Python: python src/main.py
	# Node.js: npm run dev
	# Go: go run ./src/...

# 3. Запуск тестов
test:
	@echo "Запуск тестов..."
	# Python: pytest
	# Node.js: npm test
	# Go: go test ./...

# 4. Проверка кода линтером
lint:
	@echo "Запуск линтеров..."
	# Python: ruff check src/
	# Node.js: npm run lint
	# Go: golangci-lint run ./src/...
	# C++: clang-format -n src/*.cpp

# 5. Управление Docker Compose
docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

# 6. Очистка временных файлов
clean:
	@echo "Очистка временных файлов..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
