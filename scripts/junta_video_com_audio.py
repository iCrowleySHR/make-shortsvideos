import os
import random
import threading
import unicodedata
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

VIDEO_EXTENSIONS = ['.mp4', '.mkv', '.avi', '.mov']
AUDIO_EXTENSIONS = ['.mp3', '.wav', '.aac', '.ogg', '.m4a']

def normalize_filename(name):
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    return ''.join(c if c.isalnum() or c in ['-', '_'] else '_' for c in name).strip('_')

def get_media_duration(path):
    cmd = [
        'ffprobe', '-v', 'error', '-show_entries',
        'format=duration', '-of',
        'default=noprint_wrappers=1:nokey=1', str(path)
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return float(result.stdout.strip())

class ShortsMakerSimples:
    def __init__(self, master):
        self.master = master
        self.master.title("Shorts Maker Simples")
        self.master.geometry("750x650")

        self.audio_folder = ""
        self.video_folder = ""
        self.output_resolution = (1080, 1920)

        self.create_widgets()

    def create_widgets(self):
        style = ttk.Style()
        style.configure('TButton', padding=5)
        style.configure('TLabel', padding=5)

        main_frame = ttk.Frame(self.master)
        main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        folder_frame = ttk.LabelFrame(main_frame, text="Selecionar Pastas")
        folder_frame.pack(fill=tk.X, pady=5)

        ttk.Button(folder_frame, text="Selecionar Pasta de Áudios", command=self.select_audio_folder).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.audio_label = ttk.Label(folder_frame, text="Nenhuma pasta selecionada")
        self.audio_label.grid(row=0, column=1, sticky=tk.W)

        ttk.Button(folder_frame, text="Selecionar Pasta de Vídeos", command=self.select_video_folder).grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.video_label = ttk.Label(folder_frame, text="Nenhuma pasta selecionada")
        self.video_label.grid(row=1, column=1, sticky=tk.W)

        resolution_frame = ttk.LabelFrame(main_frame, text="Configurações de Resolução")
        resolution_frame.pack(fill=tk.X, pady=5)

        ttk.Label(resolution_frame, text="Resolução de saída:").pack(side=tk.LEFT, padx=5)
        self.resolution_combo = ttk.Combobox(resolution_frame, state="readonly", values=["720x1280", "1080x1920"], width=15)
        self.resolution_combo.pack(side=tk.LEFT, padx=5)
        self.resolution_combo.set("1080x1920")
        self.resolution_combo.bind("<<ComboboxSelected>>", self.on_resolution_change)

        progress_frame = ttk.LabelFrame(main_frame, text="Progresso")
        progress_frame.pack(fill=tk.X, pady=5)

        self.progress = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(fill=tk.X, expand=True)
        self.progress_label = ttk.Label(progress_frame, text="Pronto")
        self.progress_label.pack()

        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)

        self.generate_btn = ttk.Button(control_frame, text="GERAR SHORTS EM LOTE", command=self.process_batch)
        self.generate_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="Limpar Log", command=self.clear_log).pack(side=tk.LEFT, padx=5)

        log_frame = ttk.LabelFrame(main_frame, text="Log de Processamento")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def on_resolution_change(self, event=None):
        selected = self.resolution_combo.get()
        if selected == "720x1280":
            self.output_resolution = (720, 1280)
        elif selected == "1080x1920":
            self.output_resolution = (1080, 1920)

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.master.update_idletasks()
        print(message)

    def clear_log(self):
        self.log_area.delete(1.0, tk.END)

    def select_audio_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.audio_folder = path
            self.audio_label.config(text=path)
            self.log(f"📁 Pasta de áudios selecionada: {path}")

    def select_video_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.video_folder = path
            self.video_label.config(text=path)
            self.log(f"🎞️ Pasta de vídeos selecionada: {path}")

    def process_batch(self):
        if not self.audio_folder or not self.video_folder:
            messagebox.showerror("Erro", "Selecione as pastas de áudio e vídeo antes de começar.")
            return

        self.generate_btn.config(state=tk.DISABLED)
        threading.Thread(target=self.generate_shorts, daemon=True).start()

    def generate_shorts(self):
        audio_files = [f for f in Path(self.audio_folder).glob("*") if f.suffix.lower() in AUDIO_EXTENSIONS]
        video_files = [f for f in Path(self.video_folder).glob("*") if f.suffix.lower() in VIDEO_EXTENSIONS]

        if not audio_files or not video_files:
            messagebox.showerror("Erro", "Não foram encontrados áudios ou vídeos válidos.")
            self.generate_btn.config(state=tk.NORMAL)
            return

        shorts_folder = Path(self.audio_folder) / "SHORTS_GERADOS"
        shorts_folder.mkdir(exist_ok=True)

        self.progress["maximum"] = 100
        self.progress["value"] = 0
        self.log(f"🔊 Áudios encontrados: {len(audio_files)}")
        self.log(f"🎥 Vídeos encontrados: {len(video_files)}")
        self.log(f"📐 Resolução escolhida: {self.output_resolution[0]}x{self.output_resolution[1]}")
        self.log("⏳ Processando...")

        for idx, audio_path in enumerate(audio_files):
            self.progress_label.config(text=f"Processando: {audio_path.name}")

            try:
                video_path = random.choice(video_files)

                audio_duration = get_media_duration(audio_path)
                video_duration = get_media_duration(video_path)

                if video_duration < 1 or audio_duration < 1:
                    raise Exception("Arquivo com duração inválida")

                max_start = max(0, video_duration - audio_duration)
                start_time = random.uniform(0, max_start)

                target_w, target_h = self.output_resolution
                normalized_name = normalize_filename(audio_path.stem)
                output_name = f"short_{normalized_name}.mp4"
                output_path = shorts_folder / output_name

                if output_path.exists():
                    self.log(f"⏭️ Pulado (já existe): {output_name}")
                    continue

                vf_filter = f"scale=-2:{target_h},crop='if(gt(iw,{target_w}),{target_w},iw)':{target_h}"

                cmd = [
                    "ffmpeg",
                    "-ss", str(start_time),
                    "-i", str(video_path),
                    "-ss", "0",
                    "-i", str(audio_path),
                    "-t", str(audio_duration),
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-vf", vf_filter,
                    "-c:v", "libx264",
                    "-preset", "fast",
                    "-b:v", "5000k",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-shortest",
                    "-y",
                    str(output_path)
                ]

                process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                if process.returncode != 0:
                    raise Exception(f"FFmpeg erro: {process.stderr}")

                self.log(f"✅ Gerado: {output_name}")

            except Exception as e:
                self.log(f"❌ Erro em {audio_path.name}: {str(e)}")

            self.progress["value"] = ((idx + 1) / len(audio_files)) * 100
            self.master.update_idletasks()

        self.progress_label.config(text="Finalizado")
        self.progress["value"] = 100
        self.generate_btn.config(state=tk.NORMAL)
        messagebox.showinfo("Concluído", "Todos os shorts foram gerados!")
        self.log("✅ Finalizado com sucesso!")

if __name__ == "__main__":
    root = tk.Tk()
    app = ShortsMakerSimples(root)
    root.mainloop()
