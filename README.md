# AI Test Assistant (Webant Hackathon 2025)

[![Playwright Tests](https://github.com/kartonka1/hak_ai_tester/actions/workflows/playwright.yml/badge.svg)](https://github.com/kartonka1/hak_ai_tester/actions/workflows/playwright.yml)

AI-помощник тестировщика: генерирует тест-кейсы из текстового описания, преобразует их в автотесты на Playwright, позволяет редактировать и сохранять в GitHub, а также делает AI-ревью тестов.

## Быстрый старт

1) Установите зависимости backend:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2) Настройте окружение:
- Скопируйте `.env.example` в `.env` и заполните переменные.

3) Запустите backend:

```bash
uvicorn backend.main:app --reload
```

4) Установите Playwright окружение (опционально для локального запуска тестов):

```bash
cd tests
npm install
npx playwright install
```

5) Откройте минимальный фронтенд:
- Откройте файл `frontend/index.html` в браузере (или подайте его через любой HTTP сервер).

6) Для Playwright на Python:

```bash
pip install -r requirements.txt
playwright install
pytest -q -k example -s
```

## Структура

- `backend/` — FastAPI API
- `backend/services/` — интеграция с LLM, GitHub и генерация кода тестов
- `tests/` — проект Playwright (TS)
- `frontend/` — простой HTML интерфейс
- `python_tests/` — директория для автотестов на Python (pytest + playwright)

## API (основные эндпоинты)

- POST `/generate/test-cases` — генерация тест-кейсов из описания.
- POST `/generate/test-code` — генерация кода автотеста из тест-кейса (ts/js/python).
- POST `/review/test` — AI ревью кода автотеста.
- POST `/save/local` — сохранение файла локально в репо.
- POST `/save/github` — сохранение/обновление файла через GitHub Contents API.
- POST `/generate/demo-app` — сгенерировать демо-приложение (index.html, script.js, styles.css).
- POST `/git/push` — локальный git add/commit/push (нужен настроенный origin).
- POST `/tests/run` — запуск тестов (body.kind: ts/js/python).

Примеры тел запросов смотрите в `backend/services/schemas.py`.

## Переменные окружения

- `OPENAI_API_KEY` — API ключ для OpenAI (или совместимых провайдеров).
- `OPENAI_BASE_URL` — базовый URL провайдера (необязательно).
- `OPENAI_MODEL` — модель (по умолчанию gpt-4o-mini).
- `GITHUB_TOKEN` — PAT с доступом к репозиторию.
- `DEFAULT_REPO_ROOT` — локальный путь, куда сохранять файлы.
- `AI_PROVIDER` — провайдер ИИ: `openai` (по умолчанию) или `ollama` (бесплатно, локально).
- Для `ollama`: установите Ollama и модель (`OLLAMA_BASE_URL`=http://localhost:11434, `OLLAMA_MODEL`=qwen2.5:7b-instruct или любая установленная).

## Запуск Playwright тестов

```bash
cd tests
npm run test
```

Сгенерированные тесты сохраняйте в `tests/e2e/*.spec.ts`. Playwright конфигурация хранится в `tests/playwright.config.ts`.

Для Python:
```bash
pytest -q
```

Сгенерированные Python тесты сохраняйте в `python_tests/*.py`.

## Демо-логин: запуск и прогон e2e

### Запуск демо-приложения
- Вариант 1 (Node http-server):

```bash
npx http-server demo_login -p 3000 --silent
```

- Вариант 2 (Python http.server):

```bash
python -m http.server 3000 -d demo_login
```

После запуска страница логина доступна по `http://localhost:3000/login.html` (роут `/login` в тестах также будет работать, если сервер отдает `login.html` по этому пути или настроен редирект).

### Настройка BASE_URL для тестов
- Конфиг Playwright (`tests/playwright.config.ts`) читает `PLAYWRIGHT_BASE_URL`.
- Тест `tests/e2e/login.spec.ts` использует `BASE_URL` (переменная окружения).

Рекомендуется выставить обе переменные на `http://localhost:3000`:

- PowerShell (Windows):
```powershell
$env:BASE_URL = 'http://localhost:3000'
$env:PLAYWRIGHT_BASE_URL = 'http://localhost:3000'
cd tests
npm run test
```

- bash:
```bash
export BASE_URL=http://localhost:3000
export PLAYWRIGHT_BASE_URL=http://localhost:3000
cd tests
npm run test
```

### Проверяемые кейсы логина (e2e)
- Позитивный:
  - Валидные креды: `user@example.com` / `Passw0rd!` → редирект на `dashboard.html`, текст «Добро пожаловать».
- Негативные:
  - Пустой email → «Email обязателен».
  - Пустой пароль → «Пароль обязателен».
  - Оба поля пустые → приоритет ошибки по email: «Email обязателен».
  - Невалидный формат email → «Неверный формат email».
  - Неверные учетные данные → «Неверные учетные данные».

## CLI

Пример end-to-end:
```bash
python -m backend.cli --requirements "Логин с email и паролем" --format markdown --target python --out output --push
```

- Сохранит test_cases.md/json, сгенерирует автотест (Python или TS/JS), создаст демо-приложение и опционально сделает git push в настроенный origin.

## Интеграция с GitHub

### Токен доступа (PAT)
1. Создайте персональный токен в GitHub с правами `repo` (достаточно Contents: read/write).
2. Установите его в переменную окружения `GITHUB_TOKEN` перед запуском backend.
   - Пример (PowerShell):
   ```powershell
   $env:GITHUB_TOKEN = 'ghp_xxx...'
   uvicorn backend.main:app --reload
   ```

### Сохранение файла через API `/save/github`
- Эндпоинт использует GitHub Contents API: создаёт или обновляет файл в указанной ветке.
- Пример запроса:
```bash
curl -X POST http://localhost:8000/save/github ^
  -H "Content-Type: application/json" ^
  -d "{\"owner\":\"YOUR_GH_USERNAME\",\"repo\":\"YOUR_REPO\",\"path\":\"tests/e2e/new_test.spec.ts\",\"content\":\"console.log('hi')\\n\",\"message\":\"test: add e2e example\",\"branch\":\"main\"}"
```

Параметры:
- `owner` — владелец репозитория.
- `repo` — имя репозитория.
- `path` — путь к файлу внутри репозитория.
- `content` — содержимое файла (сырой текст; кодируется в base64 на сервере).
- `message` — commit message.
- `branch` — целевая ветка (по умолчанию `main`).

### Локальный git push через `/git/push`
- Эндпоинт делает `git add -A`, коммит и `git push` из директории `DEFAULT_REPO_ROOT` (см. env).
- Требуется заранее настроить удалённый репозиторий (`origin`) и авторизацию (например, с HTTPS и PAT/credential helper).
- Пример:
```bash
curl -X POST http://localhost:8000/git/push -H "Content-Type: application/json" -d "{\"message\":\"chore: update tests\",\"remote\":\"origin\",\"branch\":\"main\"}"
```

Советы:
- Проверьте, что `DEFAULT_REPO_ROOT` указывает на корень этого проекта.
- Убедитесь, что ветка существует; сервис создаст её при необходимости.
- Если push не выполняется (нет удалённого), настройте:
```bash
git remote add origin https://github.com/<owner>/<repo>.git
git push -u origin main
```

### Переменные окружения
- `GITHUB_TOKEN` — обязательна для `/save/github`.
- `DEFAULT_REPO_ROOT` — корень репозитория для `/git/push` (по умолчанию `.`).

Примечание: В проекте ожидается файл `.env` (можно создать по образцу `.env.example`) или экспорт переменных окружения в вашей оболочке.

## CI: GitHub Actions для Playwright

В репозитории есть workflow `.github/workflows/playwright.yml`, который:
- запускается на push/PR в ветку `main`,
- ставит зависимости в `tests/`, устанавливает браузеры Playwright,
- поднимает локально демо-приложение (`demo_login`) на порту 3000,
- прогоняет e2e-тесты с `BASE_URL=http://localhost:3000`,
- загружает HTML-репорт Playwright как артефакт job’а.

После запуска workflow откройте вкладку Actions вашего репозитория, выберите последний прогон и скачайте артефакт `playwright-report`.

## Лицензия

MIT


