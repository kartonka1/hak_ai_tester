@echo off
echo Запуск AI Test Assistant Backend...
.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

