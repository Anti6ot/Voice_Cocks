import subprocess
import sys


def build_exe():
    print("Устанавливаю PyInstaller...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    print("Создаю .exe файл...")
    subprocess.check_call([
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name", "DiscordTranslator",
        "--add-data", "models;models",
        "main.py"
    ])
    
    print("\n✅ Готово! Файл находится в папке dist/DiscordTranslator.exe")
    print("Этот файл можно запускать без установки Python.")


if __name__ == "__main__":
    build_exe()