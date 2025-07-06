import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import unicodedata
import re
from datetime import datetime

VIDEO_EXTENSIONS = ['mp4', 'mkv', 'avi', 'mov', 'flv', 'wmv', 'm4v', 'webm', 'mpg', 'mpeg', 'ts', 'ogv', '3gp']

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except:
        return False

def sanitize_filename(name):
    substitutions = {
        ' ': '_', '＂': '', '"': '', "'": '', '´': '', '`': '',
        '<': '', '>': '', '?': '', '|': '', '\\': '', '/': '', ':': '',
        '*': '', '%': '', '&': '', '^': '',
        'ç': 'c', 'ã': 'a', 'á': 'a', 'à': 'a', 'â': 'a',
        'é': 'e', 'ê': 'e', 'í': 'i',
        'ó': 'o', 'ô': 'o', 'õ': 'o',
        'ú': 'u', 'ü': 'u', 'ñ': 'n',
        '｜': '', '¦': '', '#': ''
    }
    for original, replacement in substitutions.items():
        name = name.replace(original, replacement)
    name = unicodedata.normalize('NFKD', name)
    name = name.encode('ASCII', 'ignore').decode('ASCII')
    name = re.sub(r'_+', '_', name).strip('_')
    return name[:200]

class VideoConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor de Vídeos para Vertical 1080x1920")
        self.root.geometry("900x600")
        self.root.configure(bg="#f0f0f0")

        self.create_widgets()
        self.video_list = []
        self.stop_flag = False
        self.current_process = None

    def create_widgets(self):
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        btn_frame = tk.Frame(main_frame, bg="#f0f0f0")
        btn_frame.pack(fill=tk.X, pady=10)

        self.btn_select = tk.Button(btn_frame, text="Selecionar Pasta com Vídeos", font=("Arial", 14), bg="#4CAF50", fg="white", command=self.select_folder)
        self.btn_select.pack(side=tk.LEFT, expand=True)

        self.btn_stop = tk.Button(btn_frame, text="Parar Conversão", font=("Arial", 14), bg="#f44336", fg="white", command=self.stop_conversion, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, expand=True, padx=10)

        mode_frame = tk.Frame(main_frame, bg="#f0f0f0")
        mode_frame.pack(fill=tk.X, pady=10)

        tk.Label(mode_frame, text="Modo de conversão:", bg="#f0f0f0", font=("Arial", 12)).pack(side=tk.LEFT)

        self.conversion_mode = tk.StringVar(value="vertical_blur")
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.conversion_mode, values=["vertical_blur", "crop_scale"], state="readonly", width=20)
        mode_combo.pack(side=tk.LEFT, padx=10)

        progress_frame = tk.Frame(main_frame, bg="#f0f0f0")
        progress_frame.pack(fill=tk.X, pady=10)

        self.label_total = tk.Label(progress_frame, text="Progresso geral: 0/0", bg="#f0f0f0")
        self.label_total.pack(anchor=tk.W)

        self.progress_total = ttk.Progressbar(progress_frame, length=700, mode='determinate')
        self.progress_total.pack(fill=tk.X, pady=5)

        self.label_current = tk.Label(progress_frame, text="Progresso do vídeo atual: 0%", bg="#f0f0f0")
        self.label_current.pack(anchor=tk.W)

        self.progress_current = ttk.Progressbar(progress_frame, length=700, mode='determinate')
        self.progress_current.pack(fill=tk.X, pady=5)

        log_frame = tk.LabelFrame(main_frame, text="Log de Processamento", bg="#f0f0f0")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.log_text = scrolledtext.ScrolledText(log_frame, font=("Consolas", 10), bg="black", fg="white", wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def stop_conversion(self):
        self.stop_flag = True
        if self.current_process:
            self.current_process.terminate()
        self.btn_stop.config(state=tk.DISABLED)
        self.log("Conversão interrompida pelo usuário")

    def select_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return

        self.stop_flag = False
        self.btn_select.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)

        self.log(f"Pasta selecionada: {folder}")

        self.converted_dir = os.path.join(folder, "converted")
        os.makedirs(self.converted_dir, exist_ok=True)
        self.log(f"Pasta de saída: {self.converted_dir}")

        all_videos = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)) and f.split('.')[-1].lower() in VIDEO_EXTENSIONS]

        self.video_list = []
        for video in all_videos:
            base_name, ext = os.path.splitext(video)
            output_path = os.path.join(self.converted_dir, f"{sanitize_filename(base_name)}_vertical{ext}")
            if not os.path.exists(output_path):
                self.video_list.append(video)
            else:
                self.log(f"Arquivo já convertido, pulando: {video}")

        if not self.video_list:
            messagebox.showinfo("Informação", "Todos os vídeos já foram convertidos.")
            self.btn_select.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
            return

        self.log(f"Total de vídeos para converter: {len(self.video_list)}")

        self.folder = folder
        self.progress_total['maximum'] = len(self.video_list)
        self.progress_total['value'] = 0
        self.progress_current['value'] = 0
        self.label_total.config(text=f"Progresso geral: 0/{len(self.video_list)}")
        self.label_current.config(text="Progresso do vídeo atual: 0%")

        threading.Thread(target=self.process_videos, daemon=True).start()

    def process_videos(self):
        for i, video in enumerate(self.video_list, start=1):
            if self.stop_flag:
                break

            self.label_total.config(text=f"Progresso geral: {i-1}/{len(self.video_list)}")
            input_path = os.path.join(self.folder, video)
            base_name, ext = os.path.splitext(video)
            output_path = os.path.join(self.converted_dir, f"{sanitize_filename(base_name)}_vertical{ext}")

            self.log(f"\nIniciando conversão: {video} → {os.path.basename(output_path)}")
            success = self.convert_video(input_path, output_path)

            if success:
                self.log(f"Conversão concluída: {video}")
            else:
                self.log(f"Falha ao converter: {video}")

            self.progress_total['value'] = i
            self.label_total.config(text=f"Progresso geral: {i}/{len(self.video_list)}")

        self.label_current.config(text="Progresso do vídeo atual: 100%")
        self.progress_current['value'] = 0
        self.btn_select.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)

        if not self.stop_flag:
            self.log("\nConversão concluída com sucesso!")
            messagebox.showinfo("Finalizado", f"Todos os vídeos foram processados.\nSaída: {self.converted_dir}")
        else:
            self.log("\nProcesso interrompido pelo usuário")

    def update_progress(self, current_time, total_duration):
        try:
            def time_to_seconds(t):
                h, m, s = t.split(':')
                return int(h)*3600 + int(m)*60 + float(s)

            current = time_to_seconds(current_time)
            total = time_to_seconds(total_duration)

            percent = (current / total) * 100
            self.progress_current['value'] = percent
            self.label_current.config(text=f"Progresso do vídeo atual: {int(percent)}%")
            self.root.update_idletasks()
        except:
            pass

    def convert_video(self, input_path, output_path):
        try:
            if not os.path.exists(input_path):
                self.log(f"Erro: Arquivo de entrada não encontrado: {input_path}")
                return False

            mode = self.conversion_mode.get()

            if mode == "vertical_blur":
                command = [
                    "ffmpeg", "-y", "-i", input_path,
                    "-filter_complex",
                    "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,boxblur=20:5[bg];"
                    "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
                    "[bg][fg]overlay=(W-w)/2:(H-h)/2,crop=1080:1920",
                    "-c:a", "copy", "-movflags", "+faststart",
                    "-preset", "fast", "-crf", "23",
                    output_path
                ]
            else:
                vf_filter = "scale=-2:1920,crop='if(gt(iw,1080),1080,iw)':1920"
                command = [
                    "ffmpeg", "-y", "-i", input_path,
                    "-vf", vf_filter,
                    "-c:v", "libx264", "-preset", "fast", "-b:v", "5000k",
                    "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", "-shortest",
                    output_path
                ]

            self.current_process = subprocess.Popen(command, stderr=subprocess.PIPE, universal_newlines=True, bufsize=1)

            duration = None
            for line in self.current_process.stderr:
                if self.stop_flag:
                    self.current_process.terminate()
                    return False

                if "Duration:" in line:
                    duration = line.split("Duration:")[1].split(",")[0].strip()
                elif "time=" in line:
                    time = line.split("time=")[1].split(" ")[0]
                    if duration:
                        self.update_progress(time, duration)

            self.current_process.wait()
            return self.current_process.returncode == 0

        except Exception as e:
            self.log(f"Erro na conversão: {str(e)}")
            return False
        finally:
            self.current_process = None

if __name__ == "__main__":
    if not check_ffmpeg():
        messagebox.showerror("Erro", "FFmpeg não encontrado no sistema!")
        sys.exit(1)

    root = tk.Tk()
    app = VideoConverterApp(root)
    root.mainloop()
