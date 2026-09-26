"""
Распознавание английской речи. faster-whisper — это тот же CTranslate2 + Whisper,
что вы собирали руками, но с готовыми wheel'ами под Windows: `pip install` и всё
работает, без cmake/MinGW.
"""

from faster_whisper import WhisperModel


class ASR:
    def __init__(self, model_size: str = "small", device: str = "cpu", compute_type: str = "int8"):
        # "small" — хороший баланс качества/скорости на CPU при 32ГБ ОЗУ.
        # Если будет тормозить — возьмите "base"; если мощности хватает — "medium".
        print(f"Загружаю модель Whisper '{model_size}' ({device}/{compute_type})...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("Модель Whisper загружена.")

    def transcribe(self, audio_f32_16k) -> str:
        segments, _info = self.model.transcribe(
            audio_f32_16k,
            language="en",
            task="transcribe",
            beam_size=1,
            vad_filter=False,  # у нас уже свой VAD в vad.py
        )
        return " ".join(seg.text.strip() for seg in segments).strip()
