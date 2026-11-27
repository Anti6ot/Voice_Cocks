"""
Распознавание речи через faster-whisper.
"""
from faster_whisper import WhisperModel

class ASR:
    def __init__(self, model_size: str = "tiny", device: str = "cpu", compute_type: str = "int8"):
        print(f"Загружаю модель Whisper '{model_size}'...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("Модель Whisper загружена.")
    
    def transcribe(self, audio_f32_16k) -> str:
        segments, _info = self.model.transcribe(
            audio_f32_16k,
            language="en",
            task="transcribe",
            beam_size=1,
            condition_on_previous_text=False,  # <-- ЭТО УБИРАЕТ ПОВТОРЕНИЯ И ГАЛЛЮЦИНАЦИИ
            no_speech_threshold=0.6,           # <-- Игнорирует куски, где больше 60% тишины/шума
            without_timestamps=True,
            vad_filter=False,
        )
        return " ".join(seg.text.strip() for seg in segments).strip()