"""
Перевод EN -> RU напрямую через ctranslate2 + sentencepiece.
Модель скачивается один раз с Hugging Face и распаковывается.
"""
import os
import sys
import zipfile
import ctranslate2
import sentencepiece as spm
from huggingface_hub import hf_hub_download

MODEL_REPO = "ordois/opus-mt-en-ru-ctranslate2-int8"
ZIP_FILENAME = "opus-mt-en-ru-ctranslate2-int8.zip"

# Универсальное определение базовой папки:
# - при запуске из .exe: папка, где лежит сам .exe
# - при запуске из python: папка, где лежит translator.py
if getattr(sys, 'frozen', False):
    # Запущено как PyInstaller .exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Запущено как обычный Python-скрипт
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_DIR = os.path.join(BASE_DIR, "models", "opus-mt-en-ru")
DONE_MARKER = os.path.join(MODEL_DIR, ".extracted_ok")

_translator = None
_sp_source = None
_sp_target = None


def _find_file(root: str, filename: str) -> str:
    for dirpath, _dirs, files in os.walk(root):
        if filename in files:
            return os.path.join(dirpath, filename)
    raise FileNotFoundError(f"Не нашёл '{filename}' внутри {root}")


def ensure_en_ru_installed():
    global _translator, _sp_source, _sp_target

    os.makedirs(MODEL_DIR, exist_ok=True)

    if not os.path.exists(DONE_MARKER):
        print(f"Скачиваю модель перевода EN -> RU (архив, один раз)...")
        print(f"Папка модели: {MODEL_DIR}")
        zip_path = hf_hub_download(repo_id=MODEL_REPO, filename=ZIP_FILENAME)
        print("Распаковываю модель...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(MODEL_DIR)
        with open(DONE_MARKER, "w") as f:
            f.write("ok")

    if _translator is None:
        model_bin_path = _find_file(MODEL_DIR, "model.bin")
        model_dir_actual = os.path.dirname(model_bin_path)
        source_spm = _find_file(MODEL_DIR, "source.spm")
        target_spm = _find_file(MODEL_DIR, "target.spm")

        print(f"Загружаю ctranslate2 Translator из: {model_dir_actual}")
        _translator = ctranslate2.Translator(model_dir_actual, device="cpu")
        _sp_source = spm.SentencePieceProcessor(model_file=source_spm)
        _sp_target = spm.SentencePieceProcessor(model_file=target_spm)
        print("Модель перевода EN -> RU загружена.")


def translate_en_to_ru(text: str) -> str:
    if not text or _translator is None:
        return ""
    tokens = _sp_source.encode(text, out_type=str)
    results = _translator.translate_batch([tokens])
    out_tokens = results[0].hypotheses[0]
    return _sp_target.decode(out_tokens)