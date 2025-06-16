import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from datetime import datetime

VIDEO_EXTENSIONS = ['mp4', 'mkv', 'avi', 'mov', 'flv', 'wmv', 'm4v', 'webm']

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False

def parse_duration(text):
    parts = text.strip().split(':')
    try:
        if len(parts) == 1:
            minutes = int(parts[0])
            return minutes * 60
        elif len(parts) == 2:
            minutes = int(parts[0])
            seconds = int(parts[1])
            return minutes * 60 + seconds
        else:
            raise ValueError("Formato inválido")
    except Exception:
        raise ValueError("Duração inválida. Use mm:ss ou minutos apenas.")

class ClipExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Extrator de Trechos - Sem Whisper")
        self.root.geometry("900x600")
        self.create_widgets()

    def create_widgets(self):
        frame_top = tk.Frame(self.root)
        frame_top.pack(pady=10)

        tk.Label(frame_top, text="Duração máxima por trecho (min ou mm:ss):").pack(side=tk.LEFT)
        self.max_minutes_var = tk.StringVar(value="3")
        tk.Entry(frame_top, textvariable=self.max_minutes_var, width=7).pack(side=tk.LEFT, padx=5)

        tk.Button(frame_top, text="Selecionar Pasta", command=self.select_folder, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=10)

        self.progress = ttk.Progressbar(self.root, length=850)
        self.progress.pack(pady=5)

        self.log_area = scrolledtext.ScrolledText(self.root, height=25, bg="black", fg="white", font=("Consolas", 10))
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_area.see(tk.END)
        self.root.update()

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder = folder
            threading.Thread(target=self.process_folder, daemon=True).start()

    def process_folder(self):
        try:
            max_seconds = parse_duration(self.max_minutes_var.get())
        except ValueError as e:
            messagebox.showerror("Erro", str(e))
            return

        video_files = [f for f in os.listdir(self.folder) if f.split('.')[-1].lower() in VIDEO_EXTENSIONS]
        total = len(video_files)
        if not total:
            self.log("Nenhum vídeo encontrado na pasta.")
            return

        output_dir = os.path.join(self.folder, "trechos")
        os.makedirs(output_dir, exist_ok=True)

        self.progress["maximum"] = total
        self.progress["value"] = 0

        for index, video in enumerate(video_files, start=1):
            video_path = os.path.join(self.folder, video)
            base_name = os.path.splitext(video)[0]
            self.log(f"Processando vídeo: {video}")

            try:
                # Obtem duração total do vídeo via ffprobe
                result = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries",
                     "format=duration", "-of",
                     "default=noprint_wrappers=1:nokey=1", video_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
                duration = float(result.stdout)

                # Quantidade de partes
                parts = int(duration // max_seconds) + (1 if duration % max_seconds > 0 else 0)
                self.log(f"Duração total: {duration:.2f} segundos. Dividindo em {parts} trecho(s).")

                for i in range(parts):
                    start = i * max_seconds
                    length = min(max_seconds, duration - start)
                    output_path = os.path.join(output_dir, f"{base_name}_trecho{i+1:02}.mp4")

                    cmd = [
                        "ffmpeg", "-y",
                        "-ss", str(start),
                        "-i", video_path,
                        "-t", str(length),
                        "-c", "copy",
                        output_path
                    ]

                    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                    self.log(f"Trecho {i+1} salvo: {os.path.basename(output_path)}")

            except Exception as e:
                self.log(f"Erro ao processar {video}: {e}")

            self.progress["value"] = index

        self.log("✅ Processamento concluído!")

if __name__ == "__main__":
    if not check_ffmpeg():
        print("FFmpeg não encontrado. Instale e configure no PATH.")
        exit(1)

    root = tk.Tk()
    app = ClipExtractorApp(root)
    root.mainloop()
