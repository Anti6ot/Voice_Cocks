"""
Простой VAD-сегментатор: копит блоки по 30мс, определяет, где говорят,
и когда после речи наступает достаточная тишина — отдаёт готовую реплику
целиком (как numpy float32 -1..1, 16kHz) для распознавания в faster-whisper.
"""

import collections
import numpy as np
import webrtcvad

from audio_capture import TARGET_RATE, CHUNK_MS


class Segmenter:
    def __init__(self, aggressiveness: int = 2, silence_ms: int = 700, max_utterance_ms: int = 12000):
        self.vad = webrtcvad.Vad(aggressiveness)  # 0..3, чем больше — тем строже фильтр не-речи
        self.silence_chunks_needed = silence_ms // CHUNK_MS
        self.max_chunks = max_utterance_ms // CHUNK_MS
        self.buffer = []
        self.silence_run = 0
        self.speaking = False

    def push(self, pcm16_chunk: bytes):
        """
        Скармливаем очередной блок аудио. Возвращает готовую реплику (np.float32)
        когда речь закончилась, иначе None.
        """
        is_speech = self.vad.is_speech(pcm16_chunk, TARGET_RATE)

        if is_speech:
            self.speaking = True
            self.silence_run = 0
            self.buffer.append(pcm16_chunk)
        elif self.speaking:
            self.silence_run += 1
            self.buffer.append(pcm16_chunk)  # немного хвостовой тишины не мешает Whisper
            if self.silence_run >= self.silence_chunks_needed:
                return self._flush()

        if self.speaking and len(self.buffer) >= self.max_chunks:
            # реплика слишком длинная — режем, чтобы не копить задержку
            return self._flush()

        return None

    def _flush(self):
        if not self.buffer:
            self.speaking = False
            return None
        raw = b"".join(self.buffer)
        self.buffer = []
        self.speaking = False
        self.silence_run = 0
        audio_i16 = np.frombuffer(raw, dtype=np.int16)
        return audio_i16.astype(np.float32) / 32768.0
