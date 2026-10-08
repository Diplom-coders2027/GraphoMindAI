# ==============================================================================
# setup.ps1 — PowerShell скрипт инициализации и публикации шаблона в GitHub
# ==============================================================================
# Использование:
#   .\setup.ps1 -Organization "my-org" [-RepoName "diploma-template"]
# ==============================================================================

[CmdletBinding()]
param (
    [Parameter(Position = 0, Mandatory = $false)]
    [string]$Organization,

    [Parameter(Position = 1, Mandatory = $false)]
    [string]$RepoName = "diploma-template"
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

function Write-Info { param([string]$msg) Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Success { param([string]$msg) Write-Host "[SUCCESS] $msg" -ForegroundColor Green }
function Write-WarningMsg { param([string]$msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-ErrorMsg { param([string]$msg) Write-Host "[ERROR] $msg" -ForegroundColor Red }

# 1. Проверка утилит
Write-Info "Проверка наличия Git и GitHub CLI (gh)..."

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-ErrorMsg "Git не найден в PATH. Установите git: https://git-scm.com/"
    exit 1
}

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-ErrorMsg "GitHub CLI (gh) не найден в PATH. Установите gh: https://cli.github.com/"
    exit 1
}

# 2. Проверка авторизации gh
Write-Info "Проверка статуса авторизации в GitHub CLI..."
try {
    gh auth status | Out-Null
} catch {
    Write-ErrorMsg "Вы не авторизованы в GitHub CLI. Выполните: gh auth login"
    exit 1
}

# 3. Запрос имени организации при отсутствии аргумента
if ([string]::IsNullOrWhiteSpace($Organization)) {
    $Organization = Read-Host "Введите имя организации в GitHub, где будет создан шаблон"
}

if ([string]::IsNullOrWhiteSpace($Organization)) {
    Write-ErrorMsg "Имя организации не может быть пустым."
    exit 1
}

Write-Info "Целевой репозиторий: $Organization/$RepoName"

# 4. Инициализация git
if (-not (Test-Path ".git")) {
    Write-Info "Инициализация локального git-репозитория..."
    git init
    git branch -M main
} else {
    Write-Info "Локальный git-репозиторий уже инициализирован."
    git branch -M main
}

git add .
$hasCommits = $false
try {
    git rev-parse --verify HEAD | Out-Null
    $hasCommits = $true
} catch {
    $hasCommits = $false
}

if (-not $hasCommits) {
    Write-Info "Создание начального коммита..."
    git commit -m "feat: initial commit for diploma repository template"
} else {
    Write-Info "Фиксация изменений..."
    git diff-index --quiet HEAD --
    if ($LASTEXITCODE -ne 0) {
        git commit -m "chore: update template files"
    }
}

# 5. Создание репозитория
Write-Info "Создание публичного репозитория $Organization/$RepoName в GitHub..."
$repoExists = $false
try {
    gh repo view "$Organization/$RepoName" 2>$null | Out-Null
    $repoExists = $true
} catch {
    $repoExists = $false
}

if (-not $repoExists) {
    gh repo create "$Organization/$RepoName" --public --source=. --remote=origin --push
} else {
    Write-WarningMsg "Репозиторий уже существует, привязываем remote и отправляем изменения..."
    git remote remove origin 2>$null
    git remote add origin "https://github.com/$Organization/$RepoName.git"
    git push -u origin main
}

Write-Info "Установка флага Template Repository..."
gh repo edit "$Organization/$RepoName" --template
Write-Success "Репозиторий-шаблон успешно опубликован: https://github.com/$Organization/$RepoName"

# 6. Настройка Branch Protection
Write-Info "Настройка защиты ветки main (обязательный PR + 1 approve)..."

$protectionJson = @"
{
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
}
"@

$tempJsonPath = [System.IO.Path]::GetTempFileName()
try {
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($tempJsonPath, $protectionJson, $utf8NoBom)
    gh api --method PUT `
      -H "Accept: application/vnd.github+json" `
      -H "X-GitHub-Api-Version: 2022-11-28" `
      "/repos/$Organization/$RepoName/branches/main/protection" `
      --input "$tempJsonPath" | Out-Null
    Write-Success "Защита ветки main успешно включена!"
} catch {
    Write-WarningMsg "Не удалось настроить защиту ветки автоматически через API. Проверьте права администратора."
} finally {
    if (Test-Path $tempJsonPath) { Remove-Item $tempJsonPath -Force }
}

# 7. Метки
Write-Info "Настройка меток Issues..."
gh label create "stage" --color "0075ca" --description "Сдача контрольного этапа проекта" --repo "$Organization/$RepoName" --force 2>$null
gh label create "need-feedback" --color "d93f0b" --description "Требуется ответ или ревью преподавателя" --repo "$Organization/$RepoName" --force 2>$null

Write-Host ""
Write-Host "==============================================================================" -ForegroundColor Green
Write-Host "  Шаблон диплома успешно развернут и настроен!" -ForegroundColor Green
Write-Host "  Ссылка: https://github.com/$Organization/$RepoName" -ForegroundColor Green
Write-Host "  Флаг: Template (Студенты могут нажать 'Use this template')" -ForegroundColor Green
Write-Host "  Защита ветки main: включена (PR + 1 Approve)" -ForegroundColor Green
Write-Host "==============================================================================" -ForegroundColor Green
