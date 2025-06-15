import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import unicodedata
import re

# Extensões de vídeo suportadas
VIDEO_EXTENSIONS = ['mp4', 'mkv', 'avi', 'mov', 'flv', 'wmv', 'm4v', 'webm', 'mpg', 'mpeg', 'ts', 'ogv', '3gp']

def sanitize_filename(name):
    # Remove acentos
    nfkd = unicodedata.normalize('NFKD', name)
    only_ascii = nfkd.encode('ASCII', 'ignore').decode('ASCII')
    # Substitui espaços por underline e remove caracteres inválidos
    sanitized = re.sub(r'[^\w\-]', '_', only_ascii)
    sanitized = re.sub(r'_{2,}', '_', sanitized)  # evita underscores repetidos
    sanitized = sanitized.strip('_')
    return sanitized

class VideoConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor de Vídeos para Vertical 1080x1920")
        self.root.geometry("900x600")
        self.root.configure(bg="#f0f0f0")

        # UI
        self.create_widgets()
        self.video_list = []
        self.stop_flag = False

    def create_widgets(self):
        # Botão selecionar pasta
        btn = tk.Button(self.root, text="Selecionar Pasta com Vídeos", font=("Arial", 14), bg="#4CAF50", fg="white",
                        command=self.select_folder)
        btn.pack(pady=15)

        # Barra progresso geral
        self.progress_total = ttk.Progressbar(self.root, length=700, mode='determinate')
        self.progress_total.pack(pady=10)
        self.label_total = tk.Label(self.root, text="Progresso geral: 0/0", bg="#f0f0f0")
        self.label_total.pack()

        # Barra progresso vídeo atual
        self.progress_current = ttk.Progressbar(self.root, length=700, mode='determinate')
        self.progress_current.pack(pady=10)
        self.label_current = tk.Label(self.root, text="Progresso do vídeo atual: 0%", bg="#f0f0f0")
        self.label_current.pack()

        # Log
        log_frame = tk.LabelFrame(self.root, text="Log de Processamento", bg="#f0f0f0")
        log_frame.pack(padx=10, pady=15, fill=tk.BOTH, expand=True)
        self.log_text = scrolledtext.ScrolledText(log_frame, font=("Consolas", 10), bg="black", fg="white", wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def select_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        self.log(f"Pasta selecionada: {folder}")

        # Criar pasta "converted"
        self.converted_dir = os.path.join(folder, "converted")
        os.makedirs(self.converted_dir, exist_ok=True)
        self.log(f"Pasta de saída criada: {self.converted_dir}")

        # Listar vídeos válidos
        self.video_list = [f for f in os.listdir(folder) if f.split('.')[-1].lower() in VIDEO_EXTENSIONS]
        if not self.video_list:
            messagebox.showwarning("Aviso", "Nenhum vídeo encontrado na pasta.")
            return
        self.folder = folder
        self.log(f"Encontrados {len(self.video_list)} vídeos para processar.")

        # Reset progress bars
        self.progress_total['maximum'] = len(self.video_list)
        self.progress_total['value'] = 0
        self.progress_current['value'] = 0
        self.label_total.config(text=f"Progresso geral: 0/{len(self.video_list)}")
        self.label_current.config(text="Progresso do vídeo atual: 0%")

        # Desabilitar botão enquanto processa
        self.root.after(100, lambda: self.root.focus_force())
        threading.Thread(target=self.process_videos, daemon=True).start()

    def process_videos(self):
        for i, video in enumerate(self.video_list, start=1):
            if self.stop_flag:
                break
            self.label_total.config(text=f"Progresso geral: {i-1}/{len(self.video_list)}")
            input_path = os.path.join(self.folder, video)
            base_name = os.path.splitext(video)[0]
            ext = os.path.splitext(video)[1]
            sanitized_name = sanitize_filename(base_name)
            output_path = os.path.join(self.converted_dir, f"{sanitized_name}_vertical{ext}")

            if os.path.exists(output_path):
                self.log(f"Arquivo {output_path} já existe. Pulando...")
                self.progress_total['value'] = i
                continue

            self.log(f"\nConvertendo: {video} → {os.path.basename(output_path)}")
            success = self.convert_video(input_path, output_path)
            if success:
                self.log(f"Concluído: {video}")
            else:
                self.log(f"Falha ao converter: {video}")
            self.progress_total['value'] = i
            self.label_total.config(text=f"Progresso geral: {i}/{len(self.video_list)}")
        self.label_current.config(text="Progresso do vídeo atual: 100%")
        self.progress_current['value'] = 0
        self.log("\nConversão concluída!")
        messagebox.showinfo("Finalizado", f"Todos os vídeos foram processados.\nSaída: {self.converted_dir}")

    def convert_video(self, input_path, output_path):
        # Comando ffmpeg baseado no seu .bat, ajustado
        # Usamos subprocess.Popen para monitorar progresso
        command = [
            "ffmpeg",
            "-y",
            "-i", input_path,
            "-filter_complex",
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,boxblur=20:5[bg];"
            "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
            "[bg][fg]overlay=(W-w)/2:(H-h)/2,crop=1080:1920",
            "-c:a", "copy",
            "-movflags", "+faststart",
            "-preset", "fast",
            "-crf", "23",
            output_path,
            "-progress", "pipe:1",  # saída progressiva para monitorar
            "-nostats"
        ]

        # Para monitorar o progresso do vídeo, precisamos do duration do vídeo
        duration = self.get_video_duration(input_path)
        if duration == 0:
            self.log("Falha ao obter duração do vídeo. Progresso não será exibido.")
            duration = None

        try:
            # Recriar comando sem -progress, pois gera saída diferente
            command = [
                "ffmpeg",
                "-y",
                "-i", input_path,
                "-filter_complex",
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,boxblur=20:5[bg];"
                "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2,crop=1080:1920",
                "-c:a", "copy",
                "-movflags", "+faststart",
                "-preset", "fast",
                "-crf", "23",
                output_path
            ]

            process = subprocess.Popen(command, stderr=subprocess.PIPE, universal_newlines=True)

            for line in process.stderr:
                if duration:
                    time_match = re.search(r'time=(\d+):(\d+):(\d+).(\d+)', line)
                    if time_match:
                        hours = int(time_match.group(1))
                        minutes = int(time_match.group(2))
                        seconds = int(time_match.group(3))
                        milliseconds = int(time_match.group(4))
                        current_time = hours * 3600 + minutes * 60 + seconds + milliseconds / 100
                        percent = min(100, (current_time / duration) * 100)
                        self.progress_current['value'] = percent
                        self.label_current.config(text=f"Progresso do vídeo atual: {percent:.1f}%")
                        self.root.update_idletasks()
            process.wait()
            return process.returncode == 0
        except Exception as e:
            self.log(f"Erro na conversão: {e}")
            return False

    def get_video_duration(self, video_path):
        # Usa ffprobe para pegar duração em segundos
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ]
            output = subprocess.check_output(cmd, universal_newlines=True)
            return float(output.strip())
        except:
            return 0


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoConverterApp(root)
    root.mainloop()
