# Шаблон выпускного проекта (Диплом)

[![GitHub template](https://img.shields.io/badge/GitHub-Template-blue?logo=github)](https://github.com/)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg)](https://conventionalcommits.org)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

Данный репозиторий является официальным шаблоном для выполнения выпускного дипломного проекта студентов **3 и 5 курса** курсов программирования.

---

## 📋 Паспорт проекта

| Параметр | Значение |
| :--- | :--- |
| **Тема проекта** | *Разработка программного комплекса для...* |
| **Студент** | Фамилия Имя Отчество |
| **Курс / Группа** | 3 курс / 5 курс, Группа XXX |
| **Преподаватель** | Фамилия Имя Отчество |
| **Учебный год** | 2026 / 2027 |

---

## 🛠 Технологический стек

- **Backend:** `Language / Framework` (например, Python / FastAPI, Go, Java / Spring Boot, C++ / Qt)
- **Frontend:** `Framework / Library` (например, TypeScript / React, Vue, Desktop UI)
- **База данных:** `Database` (например, PostgreSQL, Redis, ClickHouse)
- **Инфраструктура / CI/CD:** Docker, Docker Compose, GitHub Actions
- **Документация:** Markdown / LaTeX / Typst, PlantUML / Mermaid / draw.io

---

## 🚀 Быстрый старт (локальный запуск)

Проект спроектирован для запуска в 2–3 команды с использованием Docker Compose:

```bash
# 1. Склонировать репозиторий
git clone https://github.com/Diplom-coders2027/<ВАШ_РЕПОЗИТОРИЙ>.git
cd <ВАШ_РЕПОЗИТОРИЙ>

# 2. Скопировать конфигурацию переменных окружения
cp .env.example .env

# 3. Запустить проект и сервисы
docker compose up --build
```

> **Примечание:** После запуска приложение будет доступно по адресу `http://localhost:8080`, документация API — по адресу `http://localhost:8080/docs`.

### Альтернативный запуск без Docker

<details>
<summary>Инструкция для локального окружения</summary>

```bash
# Установка зависимостей
make install   # или npm install / poetry install / pip install -r requirements.txt

# Запуск тестов
make test

# Запуск в режиме разработки
make run
```

</details>

---

## 📁 Структура репозитория

```text
├── .github/
│   ├── workflows/
│   │   └── check-pr.yml         # Автоматическая проверка гигиены PR (секреты, .env)
│   ├── ISSUE_TEMPLATE/
│   │   ├── 01_stage.md          # Шаблон сдачи контрольного этапа
│   │   └── 02_question.md       # Шаблон вопроса преподавателю / проблемы
│   └── PULL_REQUEST_TEMPLATE.md # Шаблон сдачи этапа через PR на проверку
├── docs/                        # Пояснительная записка и сопроводительные материалы
│   ├── diagrams/                # Исходники архитектурных диаграмм и схем БД
│   └── README.md                # Требования к оформлению проектной документации
├── src/                         # Исходный код разрабатываемой системы
├── .editorconfig                # Единые правила форматирования кода (UTF-8, LF)
├── .env.example                 # Пример конфигурационных переменных
├── .gitignore                   # Защита от мусора и утечек секретов
├── CONTRIBUTING.md              # Регламент разработки, Git Flow и защита main
├── docker-compose.yml           # Стартовая конфигурация сервисов и базы данных
├── Dockerfile                   # Базовый Dockerfile проекта
├── GUIDELINE.md                 # Пошаговое руководство от клонирования до защиты
├── LICENSE                      # Лицензия MIT
├── Makefile                     # Команды быстрого старта (make run, test, lint)
├── README.md                    # Паспорт проекта и инструкции
└── setup.sh                     # Скрипт создания шаблона в организации GitHub
```

---

## 📖 Руководство и регламент работы

- **Пошаговое руководство для студента:** [GUIDELINE.md](GUIDELINE.md) — подробный разбор всего цикла работы: создание репозитория, сдача этапов, прохождение ревью, решение типовых проблем с Git.
- **Правила веток и коммитов:** [CONTRIBUTING.md](CONTRIBUTING.md) — краткий регламент именования веток (`stage/`, `fix/`, `docs/`) и сообщений коммитов (`feat:`, `fix:`, `docs:`).
