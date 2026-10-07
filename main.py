"""
Переводчик Discord/YouTube EN -> RU в реальном времени.
С GUI для выбора настроек при запуске.
"""
import argparse
import sys
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import pyaudiowpatch as pyaudio

from audio_capture import LoopbackStream, list_output_devices
from vad import Segmenter
from asr import ASR
from translator import ensure_en_ru_installed, translate_en_to_ru


def get_config_via_gui(devices):
    """Показывает окно выбора настроек перед запуском."""
    root = tk.Tk()
    root.title("Настройки переводчика")
    root.geometry("450x300")
    root.attributes("-topmost", True)
    
    config = {"device_idx": 0, "model": "small"}
    
    ttk.Label(root, text="Выберите аудиоустройство (Loopback):", font=("Segoe UI", 10)).pack(pady=(10, 0))
    
    device_names = [f"[{i}] {d['name']}" for i, d in enumerate(devices)]
    device_var = tk.StringVar(value=device_names[0] if device_names else "")
    device_cb = ttk.Combobox(root, textvariable=device_var, values=device_names, state="readonly", width=50)
    device_cb.pack(pady=5)
    
    ttk.Label(root, text="Модель распознавания (больше = точнее, но медленнее):", font=("Segoe UI", 10)).pack(pady=(15, 0))
    model_var = tk.StringVar(value="small")
    ttk.Combobox(root, textvariable=model_var, values=["tiny", "base", "small", "medium"], state="readonly", width=20).pack(pady=5)
    
    def on_start():
        if not device_var.get():
            messagebox.showerror("Ошибка", "Не найдено ни одного аудиоустройства!")
            return
        
        config["device_idx"] = int(device_var.get().split("]")[0].strip("["))
        config["model"] = model_var.get()
        root.destroy()
    
    ttk.Button(root, text="Запустить переводчик", command=on_start).pack(pady=20)
    
    root.mainloop()
    return config


class TranslatorApp:
    def __init__(self, root, device, model_size):
        self.root = root
        self.root.title("Переводчик Discord/YouTube EN -> RU")
        self.root.geometry("800x600")
        
        self.device = device
        self.model_size = model_size
        self.stop_event = threading.Event()
        
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Segoe UI", 11))
        self.text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        self.status_label = tk.Label(root, text="Инициализация...", font=("Segoe UI", 10), fg="blue")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        self.worker_thread = threading.Thread(target=self.audio_loop, daemon=True)
        self.worker_thread.start()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_closing(self):
        self.stop_event.set()
        self.root.destroy()
    
    def update_status(self, text):
        self.status_label.config(text=text)
    
    def append_text(self, text_en, text_ru):
        self.text_area.insert(tk.END, f"EN: {text_en}\n", "en")
        self.text_area.insert(tk.END, f"RU: {text_ru}\n\n", "ru")
        self.text_area.see(tk.END)
        self.text_area.tag_config("en", foreground="gray")
        self.text_area.tag_config("ru", foreground="black", font=("Segoe UI", 12, "bold"))
    
    def audio_loop(self):
        try:
            self.root.after(0, lambda: self.update_status("Загрузка моделей перевода и Whisper..."))
            
            ensure_en_ru_installed()
            asr = ASR(model_size=self.model_size)
            # Оптимальные настройки для плавной речи без обрывов:
            # aggressiveness=2: баланс между игнорированием шума и ловлей речи
            # silence_ms=1000: ждем 1 секунду тишины перед тем, как считать фразу законченной (позволяет делать паузы)
            # max_utterance_ms=10000: принудительный разрыв только если говорят дольше 10 секунд без остановки
            # segmenter = Segmenter(aggressiveness=2, silence_ms=1000, max_utterance_ms=10000)
            segmenter = Segmenter(aggressiveness=3, silence_ms=600, max_utterance_ms=4000)
            
            self.root.after(0, lambda: self.update_status("🎧 Слушаю... (говорите или включите аудио)"))
            
            with LoopbackStream(self.device) as stream:
                while not self.stop_event.is_set():
                    chunk = stream.read_chunk()
                    utterance = segmenter.push(chunk)
                    
                    if utterance is None:
                        continue
                    
                    text_en = asr.transcribe(utterance)
                    if not text_en:
                        continue
                    
                    text_ru = translate_en_to_ru(text_en)
                    self.root.after(0, lambda en=text_en, ru=text_ru: self.append_text(en, ru))
        
        except Exception as e:
            self.root.after(0, lambda: self.update_status(f"❌ Ошибка: {e}"))
            print(f"Ошибка в audio_loop: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", type=int, default=None)
    parser.add_argument("--model", default=None)
    args, unknown = parser.parse_known_args()
    
    pa = pyaudio.PyAudio()
    devices = list_output_devices(pa)
    
    if not devices:
        print("Не найдено устройств Loopback. Убедитесь, что вы на Windows 10/11.")
        pa.terminate()
        return
    
    if args.device is None or args.model is None:
        config = get_config_via_gui(devices)
        if not config:
            pa.terminate()
            return
        device = devices[config["device_idx"]]
        model_size = config["model"]
    else:
        device = devices[args.device]
        model_size = args.model
    
    pa.terminate()
    
    root = tk.Tk()
    app = TranslatorApp(root, device, model_size)
    root.mainloop()


if __name__ == "__main__":
    main()