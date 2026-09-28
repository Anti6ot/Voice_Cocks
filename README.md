   ![Version](https://img.shields.io/github/v/release/Anti6ot/discord-translator)
   ![Downloads](https://img.shields.io/github/downloads/Anti6ot/discord-translator/total)
   ![License](https://img.shields.io/github/license/Anti6ot/discord-translator)

# 🎧VOICE_COCKS  Переводчик Discord / YouTube (EN -> RU) в реальном времени

Приложение для захвата системного звука, распознавания английской речи и отображения перевода в виде прозрачного оверлея поверх всех окон.

## ⚠️ КРИТИЧЕСКИ ВАЖНЫЕ ТРЕБОВАНИЯ (Прочтите перед установкой!)

1. **Версия Python**: Строго **Python 3.12** (или 3.10 / 3.11). 
   - *Python 3.14 и новее НЕ ПОДДЕРЖИВАЕТСЯ* из-за отсутствия совместимых wheel-пакетов для C-расширений.
   - Скачайте с [python.org](https://www.python.org/downloads/release/python-3120/) и **обязательно** поставьте галочку *"Add python.exe to PATH"* при установке.
2. **Microsoft Visual C++ Redistributable (x64)**: 
   - Библиотека `torch` (используемая для перевода) требует эти системные файлы. Без них приложение будет "тихо" падать с ошибкой `OSError: [WinError 1114] ... c10.dll`.
   - 📥 [Скачать установщик (vc_redist.x64.exe)](https://aka.ms/vs/17/release/vc_redist.x64.exe)
   - ⚠️ **После установки ОБЯЗАТЕЛЬНО перезагрузите компьютер.**
3. **Расположение папки**: 
   - **НЕ размещайте проект в папках OneDrive** (например, `OneDrive\Рабочий стол`). Функция "Файлы по запросу" блокирует загрузку `.dll` библиотек, вызывая странные ошибки.
   - ✅ Переместите папку проекта в надежное место, например: `C:\projects\discord-translator`

---

## 🛠️ Установка

Откройте **PowerShell** (или командную строку) и выполните команды по порядку:

1. Перейдите в папку с проектом:
   ```powershell
   cd C:\путь\к\вашей\папке\discord-translator
   ```
2. Создайте виртуальное окружение:
   ```powershell
   python -m venv venv
   ```
3. Активируйте его:
   ```powershell
   venv\Scripts\Activate.ps1
   ```
   *(Если появится красная ошибка о "выполнении сценариев", выполните эту команду и повторите активацию: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*
4. Установите зависимости:
   ```powershell
   pip install -r requirements.txt
   ```
   *При первом запуске также будут автоматически скачаны модели Whisper и языковой пакет для перевода (~150 МБ).*

---

## 🚀 Использование

1. Посмотрите список доступных устройств захвата звука:
   ```powershell
   python main.py --list
   ```
   *(Ищите устройство с пометкой `[Loopback]`, например: `[0] Наушники (Realtek(R) Audio) [Loopback]`)*

2. Запустите приложение, указав номер устройства и размер модели:
   ```powershell
   python main.py --device 0 --model tiny
   ```
   - `--device`: номер устройства из списка выше (по умолчанию 0).
   - `--model`: размер модели распознавания. Доступны: `tiny` (самая быстрая, рекомендуется), `base`, `small`, `medium`.

### 🖱️ Управление оверлеем:
- **Перемещение**: Зажмите левую кнопку мыши на окне субтитров и перетащите его.
- **Закрытие**: Нажмите клавишу `Esc`, когда окно активно, или `Ctrl+C` в окне консоли.

---

## 📂 Структура проекта

- `main.py` — Точка входа. Инициализирует PyQt6, запускает фоновый поток обработки.
- `overlay.py` — Логика прозрачного окна (PyQt6), всегда поверх остальных окон.
- `translator.py` — Модуль перевода (использует `argos-translate`).
- `asr.py` — Обертка для распознавания речи (`faster-whisper`).
- `vad.py` — Детектор активности голоса (`webrtcvad`), отсекает тишину.
- `audio_capture.py` — Захват звука через WASAPI loopback (`PyAudioWPatch`).
- `requirements.txt` — Список зависимостей.

---

## 🆘 Решение частых проблем (Troubleshooting)

| Симптом | Причина и решение |
| :--- |--- |
| **Ошибка `[WinError 1114] ... c10.dll`** или **мгновенное закрытие** без ошибок | Не установлен или не применен **Visual C++ Redistributable**. Установите его и **перезагрузите ПК**. |
| **Окно не появляется, консоль просто возвращает приглашение** | 1. Проект лежит в OneDrive (переместите в `C:\projects`).<br>2. Используется Python 3.14 (переустановите на 3.12). |
| **Ошибка `Execution of scripts is disabled...`** | PowerShell блокирует активацию venv. Выполните: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| **Ошибка `No matching distribution found for webrtcvad...`** | Вы используете неподдерживаемую версию Python. Убедитесь, что `python --version` выдает `3.12.x`. |
| **Звук не захватывается / тишина** | Убедитесь, что вы выбрали устройство с пометкой `[Loopback]` в выводе `--list`, и что в этом устройстве действительно есть звук. |

---

## 📝 Содержимое `requirements.txt` (для справки)
```text
faster-whisper==1.0.3
PyAudioWPatch==0.2.12.8
webrtcvad-wheels==2.0.14
argostranslate==1.9.6
scipy==1.13.1
numpy==1.26.4
colorama==0.4.6
PyQt6==6.7.1
```

### 💡 Рекомендация:
Сразу после создания этого файла **переместите всю папку `discord-translator`** из `OneDrive\Рабочий стол` в корень диска, например в `C:\discord-translator`. Это на 99% гарантирует, что вы больше не столкнетесь с проблемами блокировки `.dll` файлов и "тихими" падениями PyQt6/torch. 

После перемещения просто откройте PowerShell, перейдите в новую папку (`cd C:\discord-translator`) и запустите `venv\Scripts\Activate.ps1`, а затем `python main.py --device 0 --model tiny`.


## создание exeшника

pyinstaller --onefile --windowed --name Voice_Cocks `
    --hidden-import=ctranslate2 `
    --hidden-import=sentencepiece `
    --hidden-import=huggingface_hub `
    --collect-all ctranslate2 `
    --collect-all sentencepiece `
    main.py