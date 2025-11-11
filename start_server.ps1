# Скрипт запуска backend сервера
Write-Host "Запуск AI Test Assistant Backend..." -ForegroundColor Green

# Активируем виртуальное окружение и запускаем сервер
& .venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

