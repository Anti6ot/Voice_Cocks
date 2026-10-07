"""
HTTP-сервер для управления настройками (устройство, модель).
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import sys

CONFIG_FILE = "settings.json"


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"device": 0, "model": "tiny"}


def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)


class ConfigHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/devices':
            self.send_devices()
        elif self.path == '/settings':
            self.send_settings()
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/settings':
            self.update_settings()
        else:
            self.send_error(404)

    def send_devices(self):
        import pyaudiowpatch as pyaudio
        from audio_capture import list_output_devices

        pa = pyaudio.PyAudio()
        devices = list_output_devices(pa)
        pa.terminate()

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(devices).encode())

    def send_settings(self):
        config = load_config()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(config).encode())

    def update_settings(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        config = json.loads(body)
        save_config(config)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')

        # Перезапускаем основной сервер с новыми настройками
        print(f"[config] Настройки обновлены: {config}", flush=True)
        print("[config] Перезапуск сервера...", flush=True)
        os.execl(sys.executable, sys.executable, *sys.argv)

    def log_message(self, format, *args):
        pass  # Отключаем логирование запросов


def run_config_server():
    server = HTTPServer(('localhost', 8766), ConfigHandler)
    print("[config] HTTP сервер настроек: http://localhost:8766", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    run_config_server()