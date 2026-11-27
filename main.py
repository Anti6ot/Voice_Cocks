"""
Переводчик Discord/YouTube EN -> RU в реальном времени.
Окно выбора настроек + прозрачный оверлей субтитров поверх всех окон.
"""
import argparse
import sys
import threading
import traceback
import tkinter as tk
from tkinter import ttk, messagebox

import pyaudiowpatch as pyaudio

from audio_capture import LoopbackStream, list_output_devices
from vad import Segmenter
from asr import ASR
from translator import ensure_en_ru_installed, translate_en_to_ru


def get_config_via_gui(root, devices):
    """Показывает модальное окно выбора настроек и возвращает конфиг."""
    win = tk.Toplevel(root)
    win.title("Настройки переводчика")
    win.geometry("460x300")
    win.resizable(False, False)
    win.attributes("-topmost", True)
    win.configure(bg="#f5f5f5")

    config = {"device_idx": 0, "model": "small", "cancelled": False}

    style = ttk.Style()
    style.configure("TLabel", background="#f5f5f5", font=("Segoe UI", 10))
    style.configure("TButton", font=("Segoe UI", 10))
    style.configure("TCombobox", font=("Segoe UI", 10))

    ttk.Label(win, text="Выберите аудиоустройство (Loopback):").pack(pady=(14, 0))
    device_names = [f"[{i}] {d['name']}" for i, d in enumerate(devices)]
    device_var = tk.StringVar(value=device_names[0] if device_names else "")
    ttk.Combobox(win, textvariable=device_var, values=device_names,
                 state="readonly", width=52).pack(pady=6)

    ttk.Label(win, text="Модель распознавания (больше = точнее, но медленнее):").pack(pady=(14, 0))
    model_var = tk.StringVar(value="small")
    ttk.Combobox(win, textvariable=model_var, values=["tiny", "base", "small", "medium"],
                 state="readonly", width=20).pack(pady=6)

    def on_start():
        if not device_var.get():
            messagebox.showerror("Ошибка", "Не найдено ни одного аудиоустройства!", parent=win)
            return
        config["device_idx"] = int(device_var.get().split("]")[0].strip("["))
        config["model"] = model_var.get()
        win.destroy()

    def on_close():
        config["cancelled"] = True
        win.destroy()

    ttk.Button(win, text="Запустить переводчик", command=on_start).pack(pady=18)

    win.grab_set()
    win.protocol("WM_DELETE_WINDOW", on_close)
    root.wait_window(win)
    return config


class SubtitleOverlay:
    """Прозрачное окно субтитров поверх всех окон (переиспользует корневой Tk).

    Перетаскивание за любую область, растягивание за нижний правый угол,
    закрепление поверх окон (📌), закрытие (✕ / Esc).
    """

    def __init__(self, root, device, model_size):
        self.root = root
        self.device = device
        self.model_size = model_size
        self.stop_event = threading.Event()
        self.pinned = True

        self.root.title("Voice Cocks — субтитры")
        self.root.overrideredirect(True)          # без рамки
        self.root.attributes("-topmost", True)    # поверх всех окон
        self.root.attributes("-alpha", 0.92)      # лёгкая прозрачность
        self.root.configure(bg="#000000")

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.width = 900
        self.height = 180
        x = (screen_w - self.width) // 2
        y = screen_h - self.height - 60
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")

        self._build_ui()
        self._bind_events()

        self._drag_offset = (0, 0)
        self._resize_start = (0, 0, 0, 0)

        self.root.deiconify()

        self.worker_thread = threading.Thread(target=self.audio_loop, daemon=True)
        self.worker_thread.start()

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.mainloop()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        self.topbar = tk.Frame(self.root, bg="#1b1b1b", height=30)
        self.topbar.pack(fill="x")
        self.topbar.pack_propagate(False)

        self.pin_btn = tk.Label(
            self.topbar, text="📌", bg="#1b1b1b", fg="#ffffff",
            font=("Segoe UI", 11), cursor="hand2",
        )
        self.pin_btn.pack(side="left", padx=10, pady=2)

        self.title_lbl = tk.Label(
            self.topbar, text="Voice Cocks", bg="#1b1b1b", fg="#7a7a7a",
            font=("Segoe UI", 9),
        )
        self.title_lbl.pack(side="left", pady=2)

        self.close_btn = tk.Label(
            self.topbar, text="✕", bg="#1b1b1b", fg="#ffffff",
            font=("Segoe UI", 11), cursor="hand2",
        )
        self.close_btn.pack(side="right", padx=10, pady=2)

        self.body = tk.Frame(self.root, bg="#0f0f0f",
                             highlightbackground="#333333", highlightthickness=1)
        self.body.pack(fill="both", expand=True)

        self.orig_label = tk.Label(
            self.body, text="", bg="#0f0f0f", fg="#b0b0b0",
            font=("Segoe UI", 13), wraplength=self.width - 48, justify="center",
        )
        self.orig_label.pack(pady=(12, 2))

        self.ru_label = tk.Label(
            self.body, text="🎧 Загрузка...", bg="#0f0f0f", fg="#ffffff",
            font=("Segoe UI", 21, "bold"), wraplength=self.width - 48, justify="center",
        )
        self.ru_label.pack(pady=(2, 14))

        self.grip = tk.Frame(self.root, bg="#444444", width=18, height=18,
                             cursor="size_nw_se")
        self.grip.place(relx=1.0, rely=1.0, anchor="se")

    def _bind_events(self):
        for w in (self.topbar, self.body, self.title_lbl, self.orig_label, self.ru_label):
            w.bind("<Button-1>", self._start_drag)
            w.bind("<B1-Motion>", self._on_drag)

        self.pin_btn.bind("<Button-1>", lambda e: self.toggle_pin())
        self.close_btn.bind("<Button-1>", lambda e: self.close())
        self.grip.bind("<Button-1>", self._start_resize)
        self.grip.bind("<B1-Motion>", self._on_resize)
        self.root.bind("<Escape>", lambda e: self.close())

    # --------------------------------------------------- перемещение/размер
    def _start_drag(self, event):
        self._drag_offset = (
            event.x_root - self.root.winfo_x(),
            event.y_root - self.root.winfo_y(),
        )

    def _on_drag(self, event):
        self.root.geometry(
            f"+{event.x_root - self._drag_offset[0]}"
            f"+{event.y_root - self._drag_offset[1]}"
        )

    def _start_resize(self, event):
        self._resize_start = (
            event.x_root,
            event.y_root,
            self.root.winfo_width(),
            self.root.winfo_height(),
        )

    def _on_resize(self, event):
        dx = event.x_root - self._resize_start[0]
        dy = event.y_root - self._resize_start[1]
        w = max(360, self._resize_start[2] + dx)
        h = max(110, self._resize_start[3] + dy)
        self.root.geometry(f"{w}x{h}")
        self.orig_label.configure(wraplength=w - 48)
        self.ru_label.configure(wraplength=w - 48)

    # ------------------------------------------------------------ закрепление
    def toggle_pin(self):
        self.pinned = not self.pinned
        self.root.attributes("-topmost", self.pinned)
        self.pin_btn.config(text="📌" if self.pinned else "📍")

    def close(self):
        self.stop_event.set()
        self.root.destroy()

    # ------------------------------------------------------ обновление UI
    def _set_status(self, text, hint=None):
        self.root.after(0, lambda: self._update_status(text, hint))

    def _update_status(self, text, hint=None):
        self.ru_label.config(text=text)
        self.orig_label.config(text=hint or "")

    def _set_subtitle(self, en, ru):
        self.root.after(0, lambda: self._update_subtitle(en, ru))

    def _update_subtitle(self, en, ru):
        self.orig_label.config(text=en)
        self.ru_label.config(text=ru)

    # ------------------------------------------------------ аудио-конвейер
    def audio_loop(self):
        try:
            self._set_status("Загрузка моделей перевода и Whisper...")

            ensure_en_ru_installed()
            asr = ASR(model_size=self.model_size)
            segmenter = Segmenter(aggressiveness=3, silence_ms=600, max_utterance_ms=4000)

            self._set_status(
                "🎧 Слушаю...",
                hint="Перетаскивайте за текст · угол — размер · 📌 — закрепить · Esc — закрыть",
            )

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
                    self._set_subtitle(text_en, text_ru)

        except Exception as e:
            self._set_status(f"❌ Ошибка: {e}")
            traceback.print_exc(file=sys.stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", type=int, default=None)
    parser.add_argument("--model", default=None)
    args, _ = parser.parse_known_args()

    root = tk.Tk()
    root.withdraw()

    try:
        pa = pyaudio.PyAudio()
        devices = list_output_devices(pa)
        pa.terminate()

        if not devices:
            root.deiconify()
            messagebox.showerror(
                "Ошибка",
                "Не найдено ни одного Loopback-устройства.\n"
                "Убедитесь, что у вас Windows 10/11 и есть устройство вывода.",
                parent=root,
            )
            root.destroy()
            return

        if args.device is not None and args.model is not None:
            device = devices[args.device]
            model_size = args.model
        else:
            config = get_config_via_gui(root, devices)
            if config.get("cancelled"):
                root.destroy()
                return
            device = devices[config["device_idx"]]
            model_size = config["model"]

        SubtitleOverlay(root, device, model_size)

    except Exception:
        traceback.print_exc(file=sys.stderr)
        with open("main_error.log", "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        try:
            root.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    main()
