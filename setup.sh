#!/usr/bin/env bash
# ==============================================================================
# setup.sh — Скрипт инициализации и публикации репозитория-шаблона в GitHub
# ==============================================================================
# Использование:
#   ./setup.sh <организация_github> [имя_репозитория]
#
# Пример:
#   ./setup.sh my-university-org diploma-template
# ==============================================================================

set -euo pipefail

# Цвета для вывода сообщений
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# 1. Проверка наличия необходимых утилит
info "Проверка наличия Git и GitHub CLI (gh)..."

if ! command -v git &> /dev/null; then
    error "Git не установлен. Пожалуйста, установите git: https://git-scm.com/"
    exit 1
fi

if ! command -v gh &> /dev/null; then
    error "GitHub CLI (gh) не установлен. Пожалуйста, установите gh: https://cli.github.com/"
    exit 1
fi

# 2. Проверка статуса авторизации в GitHub CLI
info "Проверка авторизации в GitHub CLI..."
if ! gh auth status &> /dev/null; then
    error "Вы не авторизованы в GitHub CLI. Выполните: gh auth login"
    exit 1
fi

# 3. Определение организации и имени репозитория
ORG="${1:-}"
REPO_NAME="${2:-diploma-template}"

if [ -z "$ORG" ]; then
    echo -e "${YELLOW}Введите имя организации в GitHub, где будет создан шаблон:${NC}"
    read -r -p "Организация: " ORG
fi

if [ -z "$ORG" ]; then
    error "Имя организации не может быть пустым."
    exit 1
fi

info "Целевой репозиторий: $ORG/$REPO_NAME"

# 4. Инициализация локального Git-репозитория
if [ ! -d ".git" ]; then
    info "Инициализация локального git-репозитория..."
    git init
    git branch -M main
else
    info "Локальный git-репозиторий уже существует."
    git branch -M main
fi

# Добавление файлов в индекс и создание первого коммита при необходимости
if ! git rev-parse --verify HEAD &> /dev/null; then
    info "Создание начального коммита..."
    git add .
    git commit -m "feat: initial commit for diploma repository template"
else
    info "Коммит уже существует. Добавление актуальных файлов..."
    git add .
    if ! git diff-index --quiet HEAD --; then
        git commit -m "chore: update template files"
    fi
fi

# 5. Создание публичного репозитория в организации
info "Создание репозитория в GitHub ($ORG/$REPO_NAME)..."

if ! gh repo view "$ORG/$REPO_NAME" &>/dev/null; then
    gh repo create "$ORG/$REPO_NAME" \
        --public \
        --source=. \
        --remote=origin \
        --push
else
    warn "Репозиторий $ORG/$REPO_NAME уже существует на GitHub. Обновление remote и пуш..."
    git remote remove origin 2>/dev/null || true
    git remote add origin "https://github.com/$ORG/$REPO_NAME.git"
    git push -u origin main
fi

# Делаем репозиторий шаблоном
info "Установка флага Template Repository..."
gh repo edit "$ORG/$REPO_NAME" --template

success "Репозиторий-шаблон успешно опубликован: https://github.com/$ORG/$REPO_NAME"

# 6. Включение защиты ветки main (Branch Protection Rule)
info "Настройка защиты ветки main (обязательный PR + 1 approve)..."

PROTECTION_PAYLOAD='{
  "required_status_checks": null,
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}'

if echo "$PROTECTION_PAYLOAD" | gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "/repos/$ORG/$REPO_NAME/branches/main/protection" \
    --input - > /dev/null; then
    success "Правило защиты ветки main успешно применено!"
else
    warn "Не удалось настроить защиту ветки через API автоматически (возможно, требуются права администратора организации)."
    warn "Вы можете настроить защиту вручную: Settings -> Branches -> Add branch protection rule -> Branch name pattern: main -> Require a pull request before merging (1 approval)."
fi

# 7. Настройка базовых меток (labels)
info "Настройка меток GitHub Issues..."
gh label create "stage" --color "0075ca" --description "Сдача контрольного этапа проекта" --repo "$ORG/$REPO_NAME" --force &>/dev/null || true
gh label create "need-feedback" --color "d93f0b" --description "Требуется ответ или ревью преподавателя" --repo "$ORG/$REPO_NAME" --force &>/dev/null || true

echo ""
echo -e "${GREEN}==============================================================================${NC}"
echo -e "${GREEN}  Шаблон диплома успешно развернут и настроен!${NC}"
echo -e "${GREEN}  Ссылка: https://github.com/$ORG/$REPO_NAME${NC}"
echo -e "${GREEN}  Флаг: Template (Студенты могут нажать 'Use this template')${NC}"
echo -e "${GREEN}  Защита ветки main: включена (PR + 1 Approve)${NC}"
echo -e "${GREEN}==============================================================================${NC}"
