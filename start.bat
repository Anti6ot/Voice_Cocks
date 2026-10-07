@echo off
chcp 65001 >nul
echo ========================================
echo   Discord Translator - Hybrid Mode
echo ========================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Python venv не найден!
    pause
    exit /b 1
)

where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js не найден!
    echo Скачайте: https://nodejs.org/
    pause
    exit /b 1
)

echo [1/3] Запуск сервера настроек...
start "Config Server" cmd /c "venv\Scripts\python.exe config_server.py"

timeout /t 2 /nobreak > nul

echo [2/3] Запуск основного сервера...
start "Backend" cmd /c "venv\Scripts\python.exe server.py"

timeout /t 5 /nobreak > nul

echo [3/3] Запуск оверлея...
cd overlay
start "Overlay" cmd /c "npx electron ."
cd ..

echo.
echo Запущено! Используйте кнопку "⚙ Настройки" в оверлее для изменения параметров.
echo Закройте окна терминалов для остановки.