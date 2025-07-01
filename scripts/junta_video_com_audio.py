import os
import random
from moviepy import VideoFileClip, AudioFileClip
from moviepy import crop
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from pathlib import Path

VIDEO_EXTENSIONS = ['.mp4', '.mkv', '.avi', '.mov']
AUDIO_EXTENSIONS = ['.mp3', '.wav', '.aac', '.ogg', '.m4a'] 

class VideoAudioMixerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Shorts Maker - Vídeo + Áudio")
        self.master.geometry("600x400")

        self.audio_folder = ''
        self.video_folder = ''

        self.create_widgets()

    def create_widgets(self):
        tk.Button(self.master, text="Selecionar Pasta de Áudios", command=self.select_audio_folder).pack(pady=10)
        tk.Button(self.master, text="Selecionar Pasta de Vídeos", command=self.select_video_folder).pack(pady=10)
        tk.Button(self.master, text="Iniciar Criação dos Shorts", command=self.process).pack(pady=20)

        self.log_box = scrolledtext.ScrolledText(self.master, wrap=tk.WORD, width=70, height=15)
        self.log_box.pack(padx=10, pady=10)

    def log(self, text):
        self.log_box.insert(tk.END, text + "\n")
        self.log_box.see(tk.END)
        self.master.update()

    def select_audio_folder(self):
        self.audio_folder = filedialog.askdirectory(title="Selecione a pasta de áudios")
        self.log(f"Pasta de áudios selecionada: {self.audio_folder}")

    def select_video_folder(self):
        self.video_folder = filedialog.askdirectory(title="Selecione a pasta de vídeos")
        self.log(f"Pasta de vídeos selecionada: {self.video_folder}")

    def process(self):
        if not self.audio_folder or not self.video_folder:
            messagebox.showerror("Erro", "Você deve selecionar ambas as pastas!")
            return

        audio_files = [os.path.join(self.audio_folder, f) for f in os.listdir(self.audio_folder) if Path(f).suffix.lower() in AUDIO_EXTENSIONS]
        video_files = [os.path.join(self.video_folder, f) for f in os.listdir(self.video_folder) if Path(f).suffix.lower() in VIDEO_EXTENSIONS]

        if not audio_files or not video_files:
            self.log("Nenhum arquivo de áudio ou vídeo encontrado.")
            return

        output_dir = os.path.join(self.audio_folder, "output")
        os.makedirs(output_dir, exist_ok=True)

        for audio_path in audio_files:
            try:
                audio_clip = AudioFileClip(audio_path)
                audio_duration = audio_clip.duration

                video_path = random.choice(video_files)
                video_clip = VideoFileClip(video_path)

                if video_clip.duration <= audio_duration:
                    start = 0
                else:
                    max_start = video_clip.duration - audio_duration
                    start = random.uniform(0, max_start)

                video_subclip = video_clip.subclip(start, start + audio_duration)

                # Faz crop para 1080x1920 (centralizado)
                w, h = video_subclip.size
                target_w, target_h = 1080, 1920

                # Se vídeo for menor que 1080x1920 em alguma dimensão, avisa e pula crop (ou pode esticar)
                if w < target_w or h < target_h:
                    self.log(f"Vídeo {Path(video_path).name} tem resolução menor que 1080x1920, ignorando crop.")
                    video_cropped = video_subclip.resize((target_w, target_h))  # opcional: redimensiona se quiser forçar
                else:
                    x_center = w // 2
                    y_center = h // 2

                    x1 = max(0, x_center - target_w // 2)
                    y1 = max(0, y_center - target_h // 2)

                    if x1 + target_w > w:
                        x1 = w - target_w
                    if y1 + target_h > h:
                        y1 = h - target_h

                    video_cropped = crop(video_subclip, x1=x1, y1=y1, width=target_w, height=target_h)

                final_video = video_cropped.set_audio(audio_clip)

                audio_name = Path(audio_path).stem
                output_path = os.path.join(output_dir, f"{audio_name}_short.mp4")

                self.log(f"Gerando vídeo: {output_path}")
                final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)

                audio_clip.close()
                video_clip.close()
                final_video.close()
            except Exception as e:
                self.log(f"Erro ao processar {audio_path}: {e}")

        self.log("✅ Todos os vídeos foram gerados.")

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoAudioMixerApp(root)
    root.mainloop()
