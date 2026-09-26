"""
Консольный переводчик Discord / YouTube EN -> RU в реальном времени.

Запуск:
    python main.py            # устройство вывода по умолчанию
    python main.py --list     # показать список устройств
    python main.py --device 0 # конкретное устройство
    python main.py --model tiny  # самая быстрая модель Whisper
"""
import argparse
import sys

import pyaudiowpatch as pyaudio
from colorama import Fore, Style, init as colorama_init

from audio_capture import LoopbackStream, list_output_devices, pick_default_output_loopback
from vad import Segmenter
from asr import ASR
from translator import ensure_en_ru_installed, translate_en_to_ru

colorama_init()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true", help="показать список устройств вывода")
    parser.add_argument("--device", type=int, default=None, help="индекс устройства из --list")
    parser.add_argument("--model", default="tiny", help="размер модели whisper: tiny/base/small/medium")
    args = parser.parse_args()

    pa = pyaudio.PyAudio()
    devices = list_output_devices(pa)
    if args.list:
        pa.terminate()
        return

    if args.device is not None:
        device = devices[args.device]
    else:
        device = pick_default_output_loopback(pa)
        print(f"\nИспользую устройство по умолчанию: {device['name']}")
    pa.terminate()

    ensure_en_ru_installed()
    asr = ASR(model_size=args.model)
    segmenter = Segmenter(aggressiveness=2, silence_ms=700)

    print(f"\n{Fore.CYAN}🎧 Слушаю... Говорите/включайте английскую речь. Ctrl+C для выхода.{Style.RESET_ALL}\n")

    with LoopbackStream(device) as stream:
        try:
            while True:
                chunk = stream.read_chunk()
                utterance = segmenter.push(chunk)
                if utterance is None:
                    continue

                text_en = asr.transcribe(utterance)
                if not text_en:
                    continue

                text_ru = translate_en_to_ru(text_en)
                print(f"{Fore.YELLOW}EN:{Style.RESET_ALL} {text_en}")
                print(f"{Fore.GREEN}RU:{Style.RESET_ALL} {text_ru}\n")
        except KeyboardInterrupt:
            print("\nОстанавливаюсь...")


if __name__ == "__main__":
    sys.exit(main())