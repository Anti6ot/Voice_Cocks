"""
Перевод EN -> RU через ctranslate2 + sentencepiece-токенизатор.
Модель (ctranslate2-формат) скачивается автоматически при первом запуске.
"""
import os
import sys

import ctranslate2
import sentencepiece as spm


def _get_model_dir():
    """Каталог модели: в сборке — из _MEIPASS или APPDATA, иначе рядом с кодом."""
    if getattr(sys, "frozen", False):
        bundled = os.path.join(getattr(sys, "_MEIPASS", ""), "models", "opus-mt-en-ru")
        if os.path.isfile(os.path.join(bundled, "model.bin")):
            return bundled
        appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(appdata, "VoiceCocks", "models", "opus-mt-en-ru")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "opus-mt-en-ru")


MODEL_DIR = _get_model_dir()

# Готовый ctranslate2-конвертированный OPUS-MT (en -> ru) с токенизаторами
MODEL_REPO = "ooeoeo/opus-mt-en-ru-ct2-float16"

_translator = None
_source_sp = None
_target_sp = None


def _download_model():
    """Скачивает ctranslate2-модель в MODEL_DIR при первом запуске."""
    from huggingface_hub import snapshot_download

    print(f"[translator] Скачиваю модель перевода {MODEL_REPO}...", flush=True)
    print("[translator] Это займёт несколько минут (около 150 МБ), только первый раз.", flush=True)

    downloaded = snapshot_download(
        repo_id=MODEL_REPO,
        local_dir=MODEL_DIR,
        ignore_patterns=["*.git*", "*.md"],
    )
    print(f"[translator] Модель сохранена в: {downloaded}", flush=True)


def ensure_en_ru_installed():
    global _translator, _source_sp, _target_sp

    if _translator is not None:
        return

    if not os.path.isfile(os.path.join(MODEL_DIR, "model.bin")):
        _download_model()

    print(f"[translator] Загружаю модель из: {MODEL_DIR}", flush=True)
    _translator = ctranslate2.Translator(MODEL_DIR, device="cpu")

    # Для OPUS-MT/Marian токенизация идёт через sentencepiece-модели
    _source_sp = spm.SentencePieceProcessor(model_file=os.path.join(MODEL_DIR, "source.spm"))
    _target_sp = spm.SentencePieceProcessor(model_file=os.path.join(MODEL_DIR, "target.spm"))

    print("[translator] Модель перевода загружена.", flush=True)


def translate_en_to_ru(text: str) -> str:
    if not text or _translator is None:
        return ""

    # Токенизируем исходный текст и явно добавляем EOS (</s>),
    # т.к. в конфиге модели add_source_eos=false.
    source_tokens = _source_sp.encode(text, out_type=str) + ["</s>"]
    results = _translator.translate_batch(
        [source_tokens],
        beam_size=1,
        repetition_penalty=1.2,
        no_repeat_ngram_size=3,
        max_decoding_length=100,
    )
    output_tokens = results[0].hypotheses[0]

    # Превращаем строки токенов обратно в id и декодируем целевой текст
    target_ids = [_target_sp.piece_to_id(tok) for tok in output_tokens]
    return _target_sp.decode(target_ids)