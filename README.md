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
- Скопируйте `.env.example` в `.env` и заполните переменные:
  ```bash
  cp .env.example .env
  # Windows PowerShell:
  Copy-Item .env.example .env
  ```
- Или создайте файл `.env` вручную (см. раздел "Переменные окружения" ниже).

3) Запустите backend:

```bash
uvicorn backend.main:app --reload
```

Или используйте скрипты запуска:
- Windows: `.\start_server.bat` или `.\start_server.ps1`
- Сервер будет доступен на `http://localhost:8000`

4) Установите Playwright окружение (опционально для локального запуска тестов):

```bash
cd tests
npm install
npx playwright install
```

5) Откройте минимальный фронтенд:
- После запуска backend откройте в браузере `http://localhost:8000/` (frontend доступен через сервер).
- Или откройте файл `frontend/index.html` напрямую в браузере (но API запросы могут не работать из-за CORS).

6) Для Playwright на Python:

```bash
pip install -r requirements.txt
playwright install
pytest -q -k example -s
```

## Структура

- `backend/` — FastAPI API
- `backend/services/` — интеграция с LLM, GitHub и генерация кода тестов
- `backend/cli.py` — CLI утилита для генерации тестов из командной строки
- `tests/` — проект Playwright (TypeScript)
- `frontend/` — простой HTML интерфейс (доступен через `/` при запущенном сервере)
- `python_tests/` — директория для автотестов на Python (pytest + playwright)
- `demo_login/` — демо-приложение для тестирования логина
- `start_server.bat` / `start_server.ps1` — скрипты для запуска сервера на Windows

## API (основные эндпоинты)

### GET эндпоинты:
- GET `/` — главная страница (frontend интерфейс)
- GET `/health` — проверка работоспособности сервера
- GET `/templates` — список доступных шаблонов тестов (auth, form, list, crud)
- GET `/docs` — Swagger UI документация API

### POST эндпоинты:
- POST `/generate/test-cases` — генерация тест-кейсов из описания.
- POST `/generate/test-code` — генерация кода автотеста из тест-кейса или шаблона (ts/js/python). Можно использовать либо `test_case`, либо `template` + `template_params`.
- POST `/review/test` — AI ревью кода автотеста.
- POST `/save/local` — сохранение файла локально в репо.
- POST `/save/github` — сохранение/обновление файла через GitHub Contents API.
- POST `/generate/demo-app` — сгенерировать демо-приложение (index.html, script.js, styles.css).
- POST `/git/push` — локальный git add/commit/push (нужен настроенный origin).
- POST `/tests/run` — запуск тестов (body.kind: ts/js/python).

Примеры тел запросов смотрите в `backend/services/schemas.py`.

### Примеры curl запросов

#### Генерация тест-кейсов

```bash
# JSON формат
curl -X POST http://localhost:8000/generate/test-cases \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Логин с email и паролем",
    "lang": "ru",
    "format": "json"
  }'

# Markdown формат
curl -X POST http://localhost:8000/generate/test-cases \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Логин с email и паролем",
    "lang": "ru",
    "format": "markdown",
    "ai_provider": "ollama",
    "ai_model": "llama3"
  }'
```

#### Генерация кода теста из тест-кейса

```bash
curl -X POST http://localhost:8000/generate/test-code \
  -H "Content-Type: application/json" \
  -d '{
    "test_case": {
      "title": "Успешная авторизация",
      "steps": [
        "Открыть страницу /login",
        "Ввести email: user@example.com",
        "Ввести пароль: Passw0rd!",
        "Нажать кнопку Войти"
      ],
      "expected": "Редирект на /dashboard"
    },
    "language": "ts",
    "base_url": "http://localhost:3000"
  }'
```

#### Генерация кода теста из шаблона

```bash
curl -X POST http://localhost:8000/generate/test-code \
  -H "Content-Type: application/json" \
  -d '{
    "template": "auth",
    "template_params": {
      "type": "positive",
      "login_url": "/login",
      "email": "user@example.com",
      "password": "Passw0rd!",
      "success_url": "/dashboard"
    },
    "language": "python",
    "base_url": "http://localhost:3000"
  }'
```

#### AI ревью кода теста

```bash
curl -X POST http://localhost:8000/review/test \
  -H "Content-Type: application/json" \
  -d '{
    "code": "import { test, expect } from '\''@playwright/test'\'';\n\ntest('\''test'\'', async ({ page }) => {\n  await page.goto('\''/login'\'');\n});"
  }'
```

#### Сохранение файла локально

```bash
curl -X POST http://localhost:8000/save/local \
  -H "Content-Type: application/json" \
  -d '{
    "relative_path": "tests/e2e/generated.spec.ts",
    "content": "import { test, expect } from '\''@playwright/test'\'';\n\ntest('\''test'\'', async ({ page }) => {\n  await page.goto('\''/login'\'');\n});"
  }'
```

#### Сохранение файла в GitHub

```bash
curl -X POST http://localhost:8000/save/github \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "your-username",
    "repo": "your-repo",
    "path": "tests/e2e/new_test.spec.ts",
    "content": "import { test, expect } from '\''@playwright/test'\'';\n\ntest('\''test'\'', async ({ page }) => {\n  await page.goto('\''/login'\'');\n});",
    "message": "test: add e2e example",
    "branch": "main"
  }'
```

#### Запуск тестов

```bash
# TypeScript тесты
curl -X POST http://localhost:8000/tests/run \
  -H "Content-Type: application/json" \
  -d '{"kind": "ts"}'

# Python тесты
curl -X POST http://localhost:8000/tests/run \
  -H "Content-Type: application/json" \
  -d '{"kind": "python", "cwd": "python_tests"}'
```

#### Git push

```bash
curl -X POST http://localhost:8000/git/push \
  -H "Content-Type: application/json" \
  -d '{
    "message": "chore: update tests",
    "remote": "origin",
    "branch": "main"
  }'
```

**Примечание для Windows PowerShell:** Используйте обратные кавычки для экранирования или сохраните JSON в файл:
```powershell
$body = Get-Content request.json -Raw
Invoke-RestMethod -Uri http://localhost:8000/generate/test-cases -Method POST -Body $body -ContentType "application/json"
```

## Переменные окружения

- `OPENAI_API_KEY` — API ключ для OpenAI (или совместимых провайдеров).
- `OPENAI_BASE_URL` — базовый URL провайдера (необязательно).
- `OPENAI_MODEL` — модель (по умолчанию gpt-4o-mini).
- `GITHUB_TOKEN` — PAT с доступом к репозиторию.
- `DEFAULT_REPO_ROOT` — локальный путь, куда сохранять файлы.
- `AI_PROVIDER` — провайдер ИИ: `openai` (по умолчанию) или `ollama` (бесплатно, локально).
- Для `ollama`: установите [Ollama](https://ollama.com/download), скачайте модель (`ollama pull llama3`) и задайте `OLLAMA_BASE_URL=http://localhost:11434`, `OLLAMA_MODEL=llama3` (или любую установленную).

### Пример `.env`

```ini
DEFAULT_REPO_ROOT=.

# AI provider: openai | ollama
AI_PROVIDER=ollama

# OpenAI (если используете удалённый API)
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# Ollama (локальная LLM)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# GitHub токен (для /save/github)
GITHUB_TOKEN=ghp_xxx
```

Файл `.env` автоматически подхватывается при запуске backend (см. `backend/services/config.py`).

### Настройка Ollama

1. Установите Ollama: [https://ollama.com/download](https://ollama.com/download)
2. Скачайте нужную модель (например, `ollama pull llama3`)
3. Убедитесь, что сервис запущен (`ollama serve` или просто вызов `ollama run llama3`)
4. Задайте `AI_PROVIDER=ollama` и `OLLAMA_MODEL=<имя_модели>`. Остальные переменные можно оставить по умолчанию.

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
- Для работы с Ollama можно добавить `--ai-provider ollama --ai-model llama3` (модель должна быть заранее установлена через `ollama pull`).

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

Примечание: В проекте ожидается файл `.env` (создайте его вручную по примеру выше) или экспорт переменных окружения в вашей оболочке.

## CI: GitHub Actions для Playwright

В репозитории есть workflow `.github/workflows/playwright.yml`, который:
- запускается на push/PR в ветку `main`,
- ставит зависимости в `tests/`, устанавливает браузеры Playwright,
- поднимает локально демо-приложение (`demo_login`) на порту 3000,
- прогоняет e2e-тесты с `BASE_URL=http://localhost:3000`,
- загружает HTML-репорт Playwright как артефакт job’а.

После запуска workflow откройте вкладку Actions вашего репозитория, выберите последний прогон и скачайте артефакт `playwright-report`.

## Troubleshooting (Решение проблем)

### Сервер не запускается

**Проблема:** Ошибка при запуске `uvicorn backend.main:app`

**Решения:**
- Убедитесь, что виртуальное окружение активировано: `.venv\Scripts\activate` (Windows) или `source .venv/bin/activate` (Linux/Mac)
- Проверьте, что все зависимости установлены: `pip install -r requirements.txt`
- Убедитесь, что Python версии 3.8+ установлен: `python --version`
- Проверьте, что порт 8000 не занят другим процессом

### Frontend не открывается или API запросы не работают

**Проблема:** Страница не загружается или ошибки CORS

**Решения:**
- Убедитесь, что backend сервер запущен на `http://localhost:8000`
- Откройте frontend через сервер: `http://localhost:8000/` (не открывайте `frontend/index.html` напрямую)
- Проверьте консоль браузера (F12) на наличие ошибок
- Убедитесь, что в frontend правильно настроен `API_BASE` (должен быть `http://localhost:8000`)

### AI генерация не работает

**Проблема:** Ошибка "OPENAI_API_KEY is not configured" или "Connection refused" для Ollama

**Решения для OpenAI:**
- Проверьте, что `OPENAI_API_KEY` установлен в `.env` файле
- Убедитесь, что ключ валидный и не истек
- Проверьте баланс на аккаунте OpenAI
- Если используете другой провайдер, убедитесь, что `OPENAI_BASE_URL` указан правильно

**Решения для Ollama:**
- Убедитесь, что Ollama установлен и запущен: `ollama serve` или `ollama run llama3`
- Проверьте, что модель установлена: `ollama list` (должна быть указанная в `OLLAMA_MODEL`)
- Убедитесь, что `OLLAMA_BASE_URL` в `.env` указывает на правильный адрес (по умолчанию `http://localhost:11434`)
- Проверьте, что `AI_PROVIDER=ollama` установлен в `.env`

### Тесты не запускаются

**Проблема:** Ошибки при запуске Playwright тестов

**Решения:**
- Установите браузеры Playwright: `npx playwright install` (в директории `tests/`)
- Убедитесь, что зависимости установлены: `cd tests && npm install`
- Проверьте, что `BASE_URL` или `PLAYWRIGHT_BASE_URL` установлены правильно
- Для Python тестов: `playwright install` (глобально) и `pip install pytest playwright`

### GitHub интеграция не работает

**Проблема:** Ошибка при сохранении в GitHub или git push

**Решения:**
- Убедитесь, что `GITHUB_TOKEN` установлен в `.env` и имеет права `repo`
- Проверьте, что токен не истек (создайте новый в [GitHub Settings](https://github.com/settings/tokens))
- Для `/git/push`: убедитесь, что удаленный репозиторий настроен: `git remote -v`
- Проверьте, что `DEFAULT_REPO_ROOT` указывает на корень git репозитория

### Ошибки форматирования кода

**Проблема:** Код не форматируется или ошибки при форматировании

**Решения:**
- Для TypeScript/JavaScript: убедитесь, что `prettier` доступен (устанавливается автоматически через `npx`)
- Для Python: установите `black` или `ruff`: `pip install black` или `pip install ruff`
- Проверьте, что форматтер доступен в PATH

### Медленная генерация с Ollama

**Проблема:** Генерация занимает очень много времени

**Решения:**
- Это нормально для локальных моделей - Ollama работает медленнее, чем OpenAI
- Используйте более легкие модели (например, `llama3:8b` вместо `llama3:70b`)
- Убедитесь, что у вас достаточно RAM для модели
- Увеличьте таймаут в frontend (по умолчанию 2 минуты)

### Проблемы с путями в Windows

**Проблема:** Ошибки с путями при сохранении файлов

**Решения:**
- Используйте прямые слеши `/` в путях (работают и в Windows)
- Убедитесь, что `DEFAULT_REPO_ROOT` использует правильный формат пути
- Проверьте права доступа к директориям

### Дополнительная помощь

- Проверьте логи сервера в консоли, где запущен `uvicorn`
- Откройте Swagger UI: `http://localhost:8000/docs` для интерактивной документации API
- Проверьте health endpoint: `http://localhost:8000/health`
- Убедитесь, что все переменные окружения загружены: проверьте `.env` файл

## Лицензия

MIT


