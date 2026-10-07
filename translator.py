"""
Перевод EN -> RU через ctranslate2 + MarianTokenizer.
Работает с моделью, содержащей shared_vocabulary.json (без .spm файлов).
"""
import os
import ctranslate2

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models", "opus-mt-en-ru")

_translator = None
_tokenizer = None


def ensure_en_ru_installed():
    global _translator, _tokenizer

    if _translator is not None:
        return

    print(f"[translator] Загружаю модель из: {MODEL_DIR}", flush=True)
    _translator = ctranslate2.Translator(MODEL_DIR, device="cpu")

    from transformers import MarianTokenizer
    _tokenizer = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-ru")

    print("[translator] Модель перевода загружена.", flush=True)


def translate_en_to_ru(text: str) -> str:
    if not text or _translator is None:
        return ""

    tokens = _tokenizer.tokenize(text)
    results = _translator.translate_batch([tokens])
    output_tokens = results[0].hypotheses[0]

    output_ids = _tokenizer.convert_tokens_to_ids(output_tokens)
    return _tokenizer.decode(output_ids, skip_special_tokens=True)