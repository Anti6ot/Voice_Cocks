"""
HTTP-сервер для управления настройками (устройство, модель).
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import sys

# При запуске через pythonw.exe (без консоли) sys.stdout/stderr = None,
# поэтому направляем вывод в лог-файл, чтобы print() не падал.
if sys.stdout is None:
    sys.stdout = open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "config_server.log"),
        "a", encoding="utf-8", buffering=1,
    )
if sys.stderr is None:
    sys.stderr = sys.stdout


def _get_config_file():
    """Путь к settings.json: в сборке — в APPDATA, иначе рядом с кодом."""
    if getattr(sys, "frozen", False):
        appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
        d = os.path.join(appdata, "VoiceCocks")
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, "settings.json")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")


CONFIG_FILE = _get_config_file()


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

        # server.py сам следит за settings.json и перезапускает аудио-поток.
        print(f"[config] Настройки сохранены: {config}", flush=True)

    def log_message(self, format, *args):
        pass  # Отключаем логирование запросов


def run_config_server():
    try:
        server = HTTPServer(('localhost', 8766), ConfigHandler)
    except OSError as e:
        # порт уже занят (например, прошлый процесс ещё работает)
        print(f"[config] Не удалось занять порт 8766: {e}", flush=True)
        return
    print("[config] HTTP сервер настроек: http://localhost:8766", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass  # обычное закрытие окна / Ctrl+C — не ошибка
    finally:
        server.server_close()


if __name__ == "__main__":
    run_config_server()