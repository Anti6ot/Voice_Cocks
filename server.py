"""
WebSocket-сервер: захват звука -> распознавание -> перевод -> отправка в Electron.
"""
import asyncio
import json
import sys
import threading
import argparse

import pyaudiowpatch as pyaudio
import websockets

from audio_capture import LoopbackStream, list_output_devices, pick_default_output_loopback
from vad import Segmenter
from asr import ASR
from translator import ensure_en_ru_installed, translate_en_to_ru
import json
import os

CONFIG_FILE = "settings.json"


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"device": 0, "model": "tiny"}


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


def audio_loop(device, model_size: str, loop: asyncio.AbstractEventLoop):
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

        # Уведомляем клиентов о готовности
        asyncio.run_coroutine_threadsafe(
            broadcast(json.dumps({"type": "status", "text": "🎧 Слушаю..."})),
            loop
        )

        with LoopbackStream(device) as stream:
            while True:
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
            loop
        )


async def ws_handler(websocket):
    """Обработчик подключения клиента."""
    clients.add(websocket)
    print(f"[server] Клиент подключён. Всего: {len(clients)}", flush=True)
    try:
        async for _ in websocket:
            pass  # Не ожидаем сообщений от клиента
    finally:
        clients.discard(websocket)
        print(f"[server] Клиент отключён. Всего: {len(clients)}", flush=True)


async def main(device_index: int | None, model_size: str):
    # Загружаем настройки из файла
    config = load_config()
    
    if device_index is None:
        device_index = config.get("device", 0)
    if model_size == "tiny":
        model_size = config.get("model", "tiny")
    
    pa = pyaudio.PyAudio()
    devices = list_output_devices(pa)

    if not devices:
        print("[server] Устройства не найдены!", file=sys.stderr)
        pa.terminate()
        return

    if device_index is not None and device_index < len(devices):
        device = devices[device_index]
    else:
        device = pick_default_output_loopback(pa)

    print(f"[server] Устройство: {device['name']}", flush=True)
    print(f"[server] Модель: {model_size}", flush=True)
    pa.terminate()

    loop = asyncio.get_event_loop()

    audio_thread = threading.Thread(
        target=audio_loop,
        args=(device, model_size, loop),
        daemon=True,
    )
    audio_thread.start()

    async with websockets.serve(ws_handler, "localhost", 8765):
        print("[server] WebSocket запущен: ws://localhost:8765", flush=True)
        await asyncio.Future()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", type=int, default=None)
    parser.add_argument("--model", default="tiny")
    args = parser.parse_args()

    try:
        asyncio.run(main(args.device, args.model))
    except KeyboardInterrupt:
        print("\n[server] Останавливаюсь...", flush=True)