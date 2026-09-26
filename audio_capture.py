"""
Захват звука, который играет из динамиков/наушников (Discord, YouTube — не важно),
через WASAPI loopback. Никакого VB-Cable и "Стерео микшера" не нужно: PyAudioWPatch
подключается к тому же потоку, что слышите вы сами, поэтому звук в наушниках
НЕ пропадает и не дублируется через виртуальные кабели.
"""

import numpy as np
import pyaudiowpatch as pyaudio
from scipy.signal import resample_poly

TARGET_RATE = 16000  # частота, нужная и VAD, и Whisper
CHUNK_MS = 30        # длина одного блока в мс (webrtcvad требует 10/20/30 мс)


def list_output_devices(pa: pyaudio.PyAudio):
    """Печатает список устройств вывода, для которых доступен loopback-захват."""
    print("\nДоступные устройства вывода (то, что реально играет в колонках/наушниках):")
    devices = []
    for loopback in pa.get_loopback_device_info_generator():
        idx = len(devices)
        print(f"  [{idx}] {loopback['name']} (rate={int(loopback['defaultSampleRate'])})")
        devices.append(loopback)
    return devices


def pick_default_output_loopback(pa: pyaudio.PyAudio):
    """Берёт loopback-версию текущего устройства вывода Windows по умолчанию."""
    wasapi_info = pa.get_host_api_info_by_type(pyaudio.paWASAPI)
    default_speakers = pa.get_device_info_by_index(wasapi_info["defaultOutputDevice"])

    if not default_speakers.get("isLoopbackDevice", False):
        for loopback in pa.get_loopback_device_info_generator():
            if default_speakers["name"] in loopback["name"]:
                return loopback
        raise RuntimeError(
            "Не нашёл loopback-версию устройства вывода по умолчанию. "
            "Запустите скрипт с флагом --list и выберите устройство вручную."
        )
    return default_speakers


class LoopbackStream:
    """
    Отдаёт аудио блоками по CHUNK_MS, уже смикшированное в моно int16 16kHz —
    ровно в том формате, который ждут webrtcvad и faster-whisper.
    """

    def __init__(self, device: dict):
        self.pa = pyaudio.PyAudio()
        self.device = device
        self.native_rate = int(device["defaultSampleRate"])
        self.channels = int(device["maxInputChannels"])
        self.frames_per_native_chunk = int(self.native_rate * CHUNK_MS / 1000)
        self.stream = None

    def __enter__(self):
        self.stream = self.pa.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.native_rate,
            frames_per_buffer=self.frames_per_native_chunk,
            input=True,
            input_device_index=self.device["index"],
        )
        return self

    def __exit__(self, *exc):
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        self.pa.terminate()

    def read_chunk(self) -> bytes:
        """Возвращает PCM16 моно 16kHz блок длиной CHUNK_MS (готово для webrtcvad)."""
        raw = self.stream.read(self.frames_per_native_chunk, exception_on_overflow=False)
        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32)

        if self.channels > 1:
            audio = audio.reshape(-1, self.channels).mean(axis=1)

        if self.native_rate != TARGET_RATE:
            audio = resample_poly(audio, TARGET_RATE, self.native_rate)

        audio_i16 = np.clip(audio, -32768, 32767).astype(np.int16)
        return audio_i16.tobytes()
