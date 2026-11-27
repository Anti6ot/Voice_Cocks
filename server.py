"""
WebSocket-сервер: захват звука -> распознавание -> перевод -> отправка в Electron.
Поддерживает перезагрузку настроек из settings.json на лету.
"""
import asyncio
import json
import os
import sys
import threading
import time
import argparse

import pyaudiowpatch as pyaudio
import websockets

from audio_capture import LoopbackStream, list_output_devices, pick_default_output_loopback
from vad import Segmenter
from asr import ASR
from translator import ensure_en_ru_installed, translate_en_to_ru
from config_server import run_config_server, load_config, save_config, CONFIG_FILE


def config_signature():
    """Возвращает содержимое settings.json (для отслеживания изменений)."""
    try:
        with open(CONFIG_FILE, 'rb') as f:
            return f.read()
    except OSError:
        return None


clients = set()


async def broadcast(message: str):
    """Отправка сообщения всем подключённым клиентам."""
    if not clients:
        return
    disconnected = set()
    for client in clients.copy():
        try:
            await client.send(message)
        except websockets.exceptions.ConnectionClosed:
            disconnected.add(client)
    clients.difference_update(disconnected)


def audio_loop(device, model_size: str, loop: asyncio.AbstractEventLoop, stop_event: threading.Event):
    """Фоновый поток: захват звука -> VAD -> ASR -> перевод -> broadcast."""
    try:
        print("[server] Загружаю модель перевода...", flush=True)
        ensure_en_ru_installed()
        print("[server] Модель перевода загружена.", flush=True)

        print("[server] Загружаю Whisper...", flush=True)
        asr = ASR(model_size=model_size)
        print("[server] Whisper загружен.", flush=True)

        segmenter = Segmenter(aggressiveness=2, silence_ms=1000, max_utterance_ms=10000)

        print("[server] 🎧 Слушаю...", flush=True)
        asyncio.run_coroutine_threadsafe(
            broadcast(json.dumps({"type": "status", "text": "🎧 Слушаю..."})),
            loop,
        )

        with LoopbackStream(device) as stream:
            while not stop_event.is_set():
                chunk = stream.read_chunk()
                utterance = segmenter.push(chunk)
                if utterance is None:
                    continue

                text_en = asr.transcribe(utterance)
                if not text_en:
                    continue

                text_ru = translate_en_to_ru(text_en)
                print(f"EN: {text_en}", flush=True)
                print(f"RU: {text_ru}", flush=True)

                message = json.dumps({
                    "type": "subtitle",
                    "original": text_en,
                    "translated": text_ru,
                })
                asyncio.run_coroutine_threadsafe(broadcast(message), loop)

    except Exception as e:
        print(f"[server] Ошибка аудио-потока: {e}", file=sys.stderr, flush=True)
        asyncio.run_coroutine_threadsafe(
            broadcast(json.dumps({"type": "status", "text": f"❌ Ошибка: {e}"})),
            loop,
        )


class AudioController:
    """Управляет фоновым аудио-потоком и перезапускает его при смене настроек."""

    def __init__(self, loop):
        self.loop = loop
        self.stop_event = threading.Event()
        self.worker = None
        self.signature = None

    def start(self):
        config = load_config()
        model_size = config.get("model", "tiny")
        device_index = config.get("device", 0)

        pa = pyaudio.PyAudio()
        devices = list_output_devices(pa)

        if not devices:
            print("[server] Устройства не найдены!", file=sys.stderr, flush=True)
            pa.terminate()
            return

        if device_index is not None and device_index < len(devices):
            device = devices[device_index]
        else:
            device = pick_default_output_loopback(pa)

        pa.terminate()

        print(f"[server] Устройство: {device['name']}", flush=True)
        print(f"[server] Модель: {model_size}", flush=True)

        self.stop_event = threading.Event()
        self.worker = threading.Thread(
            target=audio_loop,
            args=(device, model_size, self.loop, self.stop_event),
            daemon=True,
        )
        self.worker.start()
        self.signature = config_signature()

    def restart(self):
        print("[server] Перезапуск аудио-потока с новыми настройками...", flush=True)
        self.stop_event.set()
        if self.worker is not None:
            self.worker.join(timeout=5)
        self.start()

    def check(self):
        if self.signature is not None and config_signature() != self.signature:
            self.restart()


async def ws_handler(websocket):
    """Обработчик подключения клиента."""
    clients.add(websocket)
    print(f"[server] Клиент подключён. Всего: {len(clients)}", flush=True)
    try:
        async for _ in websocket:
            pass  # Не ожидаем сообщений от клиента
    except websockets.exceptions.ConnectionClosed:
        pass  # обычное закрытие/обрыв соединения — не ошибка
    finally:
        clients.discard(websocket)
        print(f"[server] Клиент отключён. Всего: {len(clients)}", flush=True)


async def main(device_index: int | None, model_size: str | None):
    # CLI-аргументы (для ручного запуска) перезаписывают settings.json,
    # чтобы дальше они подхватывались как источник настроек.
    if device_index is not None or model_size is not None:
        config = load_config()
        if device_index is not None:
            config["device"] = device_index
        if model_size is not None:
            config["model"] = model_size
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

    loop = asyncio.get_event_loop()
    controller = AudioController(loop)
    controller.start()

    def watcher():
        while True:
            time.sleep(1)
            try:
                controller.check()
            except Exception as e:
                print(f"[server] Ошибка watcher: {e}", file=sys.stderr, flush=True)

    threading.Thread(target=watcher, daemon=True).start()

    # HTTP-сервер настроек (:8766) в отдельном потоке
    threading.Thread(target=run_config_server, daemon=True).start()

    async with websockets.serve(ws_handler, "localhost", 8765):
        print("[server] WebSocket запущен: ws://localhost:8765", flush=True)
        await asyncio.Future()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", type=int, default=None)
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    try:
        asyncio.run(main(args.device, args.model))
    except KeyboardInterrupt:
        print("\n[server] Останавливаюсь...", flush=True)
