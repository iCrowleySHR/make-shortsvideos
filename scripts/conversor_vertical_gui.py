import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import unicodedata
import re

VIDEO_EXTENSIONS = ['mp4', 'mkv', 'avi', 'mov', 'flv', 'wmv', 'm4v', 'webm', 'mpg', 'mpeg', 'ts', 'ogv', '3gp']

def sanitize_filename(name):
    substitutions = {
        ' ': '_', '＂': '', '"': '', "'": '', '´': '', '`': '',
        '<': '', '>': '', '?': '', '|': '', '\\': '', '/': '', ':': '',
        '*': '', '%': '', '&': '', '^': '',
        'ç': 'c', 'ã': 'a', 'á': 'a', 'à': 'a', 'â': 'a',
        'é': 'e', 'ê': 'e', 'í': 'i',
        'ó': 'o', 'ô': 'o', 'õ': 'o',
        'ú': 'u', 'ü': 'u', 'ñ': 'n',
        '｜': '',  # FULLWIDTH VERTICAL LINE
        '¦': '',   # BROKEN BAR
        '|': '',   # ASCII pipe
        '#': '', ':': '', '"': '', '\'': '',
        '“': '', '”': '', '<': '', '>': '',
        '/': '', '\\': '', '?': '', '|': '', '＂': ''
    }
    for original, replacement in substitutions.items():
        name = name.replace(original, replacement)
    name = unicodedata.normalize('NFKD', name)
    name = name.encode('ASCII', 'ignore').decode('ASCII')
    name = re.sub(r'_+', '_', name).strip('_')
    return name

def sanitize_filename_bat_old_style(name):
    name = name.replace(' ', '_')
    for ch in ['#', ':', '"', '\'', '“', '”', '<', '>', '/', '\\', '?', '|', '＂']:
        name = name.replace(ch, '')
    return name

def sanitize_filename_bat_new_style(name):
    substitutions = {
        ' ': '_', '＂': '', '"': '', "'": '', '´': '', '`': '',
        '<': '', '>': '', '?': '', '|': '', '\\': '', '/': '', ':': '',
        '*': '', '%': '', '&': '', '^': '',
        'ç': 'c', 'ã': 'a', 'á': 'a', 'à': 'a', 'â': 'a',
        'é': 'e', 'ê': 'e', 'í': 'i',
        'ó': 'o', 'ô': 'o', 'õ': 'o',
        'ú': 'u', 'ü': 'u', 'ñ': 'n',
        '｜': '', '¦': '', '|': '',
        '#': '', ':': '', '"': '', '\'': '',
        '“': '', '”': '', '<': '', '>',
        '/': '', '\\': '', '?': '', '|': '', '＂': ''
    }
    for original, replacement in substitutions.items():
        name = name.replace(original, replacement)
    name = unicodedata.normalize('NFKD', name)
    name = name.encode('ASCII', 'ignore').decode('ASCII')
    name = re.sub(r'_+', '_', name).strip('_')
    return name


class VideoConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor de Vídeos para Vertical 1080x1920")
        self.root.geometry("900x600")
        self.root.configure(bg="#f0f0f0")

        self.create_widgets()
        self.video_list = []
        self.stop_flag = False

    def create_widgets(self):
        btn = tk.Button(self.root, text="Selecionar Pasta com Vídeos", font=("Arial", 14), bg="#4CAF50", fg="white",
                        command=self.select_folder)
        btn.pack(pady=15)

        self.progress_total = ttk.Progressbar(self.root, length=700, mode='determinate')
        self.progress_total.pack(pady=10)
        self.label_total = tk.Label(self.root, text="Progresso geral: 0/0", bg="#f0f0f0")
        self.label_total.pack()

        self.progress_current = ttk.Progressbar(self.root, length=700, mode='determinate')
        self.progress_current.pack(pady=10)
        self.label_current = tk.Label(self.root, text="Progresso do vídeo atual: 0%", bg="#f0f0f0")
        self.label_current.pack()

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

        self.converted_dir = os.path.join(folder, "converted")
        os.makedirs(self.converted_dir, exist_ok=True)
        self.log(f"Pasta de saída criada: {self.converted_dir}")

        all_videos = [f for f in os.listdir(folder) if f.split('.')[-1].lower() in VIDEO_EXTENSIONS]
        if not all_videos:
            messagebox.showwarning("Aviso", "Nenhum vídeo encontrado na pasta.")
            return

        # Filtra só vídeos NÃO convertidos
        self.video_list = []
        for video in all_videos:
            base_name, ext = os.path.splitext(video)
            if not self.already_converted(base_name, ext):
                self.video_list.append(video)
            else:
                self.log(f"Arquivo já convertido encontrado, pulando: {video}")

        if not self.video_list:
            messagebox.showinfo("Informação", "Todos os vídeos já foram convertidos.")
            return

        self.log(f"Total de vídeos para converter: {len(self.video_list)}")

        self.folder = folder
        self.progress_total['maximum'] = len(self.video_list)
        self.progress_total['value'] = 0
        self.progress_current['value'] = 0
        self.label_total.config(text=f"Progresso geral: 0/{len(self.video_list)}")
        self.label_current.config(text="Progresso do vídeo atual: 0%")

        threading.Thread(target=self.process_videos, daemon=True).start()

    def already_converted(self, base_name, ext):
        sanitized_current = sanitize_filename(base_name)
        path_current = os.path.join(self.converted_dir, f"{sanitized_current}_vertical{ext}")
        if os.path.exists(path_current):
            return True

        sanitized_bat_old = sanitize_filename_bat_old_style(base_name)
        path_bat_old = os.path.join(self.converted_dir, f"{sanitized_bat_old}_vertical{ext}")
        if os.path.exists(path_bat_old):
            return True

        sanitized_bat_new = sanitize_filename_bat_new_style(base_name)
        path_bat_new = os.path.join(self.converted_dir, f"{sanitized_bat_new}_vertical{ext}")
        if os.path.exists(path_bat_new):
            return True

        return False

    def process_videos(self):
        for i, video in enumerate(self.video_list, start=1):
            if self.stop_flag:
                break
            self.label_total.config(text=f"Progresso geral: {i-1}/{len(self.video_list)}")
            input_path = os.path.join(self.folder, video)
            base_name, ext = os.path.splitext(video)

            sanitized_name = sanitize_filename(base_name)
            output_path = os.path.join(self.converted_dir, f"{sanitized_name}_vertical{ext}")

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

        try:
            process = subprocess.Popen(command, stderr=subprocess.PIPE, universal_newlines=True)
            for line in process.stderr:
                # Você pode adicionar lógica para progresso do vídeo aqui
                pass
            process.wait()
            return process.returncode == 0
        except Exception as e:
            self.log(f"Erro na conversão: {e}")
            return False

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoConverterApp(root)
    root.mainloop()
