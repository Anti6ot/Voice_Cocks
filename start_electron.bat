@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo    Voice Cocks — запуск (overlay + консоль с переводом)
echo ============================================================
echo.

:: ------------------------------------------------------------------
:: 1. Python 3.12
:: ------------------------------------------------------------------
set "PY="
where py >nul 2>nul
if !errorlevel! equ 0 (
    py -3.12 -c "import sys" >nul 2>nul
    if !errorlevel! equ 0 set "PY=py -3.12"
)
if not defined PY (
    python -c "import sys; exit(0 if sys.version_info[:2] == (3,12) else 1)" >nul 2>nul
    if !errorlevel! equ 0 set "PY=python"
)
if not defined PY (
    echo [ОШИБКА] Не найден Python 3.12.
    echo   Скачайте: https://www.python.org/downloads/release/python-3120/
    pause
    exit /b 1
)

:: ------------------------------------------------------------------
:: 2. venv
:: ------------------------------------------------------------------
if not exist "venv\Scripts\python.exe" (
    echo [1/3] Создаю venv...
    !PY! -m venv venv
    if errorlevel 1 ( echo Ошибка venv. & pause & exit /b 1 )
) else (
    echo [1/3] venv уже есть.
)

:: ------------------------------------------------------------------
:: 3. Python-зависимости
:: ------------------------------------------------------------------
venv\Scripts\python.exe -c "import faster_whisper, pyaudiowpatch, webrtcvad, ctranslate2, sentencepiece, huggingface_hub, numpy, websockets" >nul 2>nul
if errorlevel 1 (
    echo [2/3] Устанавливаю зависимости Python...
    venv\Scripts\python.exe -m pip install --upgrade pip >nul
    venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 ( echo Ошибка установки. & pause & exit /b 1 )
) else (
    echo [2/3] Зависимости Python уже установлены.
)

:: ------------------------------------------------------------------
:: 4. Node.js + Electron
:: ------------------------------------------------------------------
where node >nul 2>nul
if errorlevel 1 (
    echo [ОШИБКА] Node.js не найден. Скачайте: https://nodejs.org/
    pause
    exit /b 1
)
if not exist "overlay\node_modules\electron\dist\electron.exe" (
    echo [3/3] Устанавливаю Electron...
    pushd overlay
    if exist "package-lock.json" ( call npm ci ) else ( call npm install )
    popd
    if errorlevel 1 ( echo Ошибка установки Electron. & pause & exit /b 1 )
) else (
    echo [3/3] Electron уже установлен.
)

echo.
echo Запускаю:
echo   - консольное окно "Субтитры и перевод" (EN/RU)
echo   - окно настроек, затем overlay субтитров
echo.

:: ------------------------------------------------------------------
:: 5. Бэкенд — видимое окно с логом субтитров и перевода.
::    Он же поднимает HTTP-сервер настроек (:8766) и WebSocket (:8765).
:: ------------------------------------------------------------------
start "Субтитры и перевод" cmd /k "venv\Scripts\python.exe server.py"

timeout /t 4 /nobreak >nul

:: ------------------------------------------------------------------
:: 6. Overlay Electron — напрямую, без консольного окна npx
:: ------------------------------------------------------------------
start "Voice Cocks Overlay" "overlay\node_modules\electron\dist\electron.exe" "overlay"

echo.
echo Готово.
echo Закройте окно "Субтитры и перевод" и overlay, чтобы остановить приложение.
echo Логи ошибок: config_server.log и backend_error.log.

endlocal
