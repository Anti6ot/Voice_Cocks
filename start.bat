@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo    Voice Cocks — Переводчик Discord / YouTube (EN -^> RU)
echo ============================================================
echo.

:: ------------------------------------------------------------------
:: 1. Ищем подходящий Python (нужен 3.12, т.к. под него собраны пакеты)
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
    echo   1. Скачайте: https://www.python.org/downloads/release/python-3120/
    echo   2. При установке поставьте галочку "Add Python to PATH".
    echo.
    pause
    exit /b 1
)
echo [OK] Python 3.12 найден.
echo.

:: ------------------------------------------------------------------
:: 2. Виртуальное окружение Python
:: ------------------------------------------------------------------
if not exist "venv\Scripts\python.exe" (
    echo [1/2] Создаю виртуальное окружение venv...
    !PY! -m venv venv
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось создать venv.
        pause
        exit /b 1
    )
) else (
    echo [1/2] Виртуальное окружение уже есть.
)

:: ------------------------------------------------------------------
:: 3. Зависимости Python
:: ------------------------------------------------------------------
venv\Scripts\python.exe -c "import faster_whisper, pyaudiowpatch, webrtcvad, ctranslate2, sentencepiece, huggingface_hub, numpy" >nul 2>nul
if errorlevel 1 (
    echo [2/2] Устанавливаю зависимости Python (первый раз может занять пару минут)...
    venv\Scripts\python.exe -m pip install --upgrade pip >nul
    venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось установить зависимости. Проверьте интернет.
        pause
        exit /b 1
    )
) else (
    echo [2/2] Зависимости Python уже установлены.
)

echo.
echo Запускаю переводчик...
echo Сначала откроется окно выбора устройства и модели,
echo затем — прозрачное окно субтитров поверх всех окон.
echo.

venv\Scripts\python.exe main.py

if errorlevel 1 (
    echo.
    echo [ОШИБКА] Приложение завершилось с ошибкой. Подробности выше.
    pause
)

endlocal
