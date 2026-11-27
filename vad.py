"""
Агрессивный VAD-сегментатор для быстрого отклика.
Режет аудио максимум каждые 2000 мс, чтобы Whisper не сходил с ума на длинных кусках.
"""
import numpy as np
import webrtcvad
from audio_capture import TARGET_RATE, CHUNK_MS

class Segmenter:
    def __init__(self, aggressiveness: int = 3, silence_ms: int = 200, max_utterance_ms: int = 2000):
        self.vad = webrtcvad.Vad(aggressiveness)
        self.silence_chunks_needed = max(1, silence_ms // CHUNK_MS)
        self.max_chunks = max_utterance_ms // CHUNK_MS
        self.buffer = []
        self.silence_run = 0
        self.speaking = False
    
    def push(self, pcm16_chunk: bytes):
        is_speech = self.vad.is_speech(pcm16_chunk, TARGET_RATE)
        
        if is_speech:
            self.speaking = True
            self.silence_run = 0
            self.buffer.append(pcm16_chunk)
        elif self.speaking:
            self.silence_run += 1
            self.buffer.append(pcm16_chunk)
            
            # Режем, если тишина длилась достаточно ИЛИ если достигли макс. длины
            if self.silence_run >= self.silence_chunks_needed or len(self.buffer) >= self.max_chunks:
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