import os
import random
import threading
from pathlib import Path
from moviepy.editor import VideoFileClip, AudioFileClip
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

VIDEO_EXTENSIONS = ['.mp4', '.mkv', '.avi', '.mov']
AUDIO_EXTENSIONS = ['.mp3', '.wav', '.aac', '.ogg', '.m4a']

class ShortsMakerSimples:
    def __init__(self, master):
        self.master = master
        self.master.title("Shorts Maker Simples")
        self.master.geometry("700x500")

        self.audio_folder = ""
        self.video_folder = ""

        # Interface
        self.create_widgets()

    def create_widgets(self):
        btn_audio = tk.Button(self.master, text="Selecionar Pasta de Áudios", command=self.select_audio_folder)
        btn_audio.pack(pady=5)

        btn_video = tk.Button(self.master, text="Selecionar Pasta de Vídeos", command=self.select_video_folder)
        btn_video.pack(pady=5)

        btn_generate = tk.Button(self.master, text="GERAR SHORTS EM LOTE", bg="green", fg="white", command=self.process_batch)
        btn_generate.pack(pady=10)

        self.log_area = scrolledtext.ScrolledText(self.master, wrap=tk.WORD, height=20)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        print(message)

    def select_audio_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.audio_folder = path
            self.log(f"📁 Pasta de áudios selecionada: {path}")

    def select_video_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.video_folder = path
            self.log(f"🎞️ Pasta de vídeos selecionada: {path}")

    def process_batch(self):
        if not self.audio_folder or not self.video_folder:
            messagebox.showerror("Erro", "Selecione as pastas de áudio e vídeo antes de começar.")
            return

        threading.Thread(target=self.generate_shorts, daemon=True).start()

    def generate_shorts(self):
        audio_files = [f for f in Path(self.audio_folder).glob("*") if f.suffix.lower() in AUDIO_EXTENSIONS]
        video_files = [f for f in Path(self.video_folder).glob("*") if f.suffix.lower() in VIDEO_EXTENSIONS]

        if not audio_files or not video_files:
            messagebox.showerror("Erro", "Não foram encontrados áudios ou vídeos válidos.")
            return

        shorts_folder = Path(self.audio_folder) / "SHORTS_GERADOS"
        shorts_folder.mkdir(exist_ok=True)

        self.log(f"🔊 Áudios encontrados: {len(audio_files)}")
        self.log(f"🎥 Vídeos encontrados: {len(video_files)}")
        self.log("⏳ Processando... (isso pode demorar)")

        for audio_path in audio_files:
            try:
                video_path = random.choice(video_files)
                audio_clip = AudioFileClip(str(audio_path))
                video_clip = VideoFileClip(str(video_path))

                if video_clip.duration < 1 or audio_clip.duration < 1:
                    raise Exception("Arquivo com duração inválida")

                max_start = max(0, video_clip.duration - audio_clip.duration)
                start_time = random.uniform(0, max_start)
                end_time = start_time + audio_clip.duration
                subclip = video_clip.subclip(start_time, end_time)

                # Redimensionar ou cortar o vídeo para 1080x1920 mantendo o centro
                subclip = subclip.resize(height=1920)
                if subclip.w > 1080:
                    x_center = subclip.w / 2
                    subclip = subclip.crop(x_center=x_center, width=1080)
                elif subclip.w < 1080:
                    subclip = subclip.resize(width=1080)

                final_clip = subclip.set_audio(audio_clip)

                output_name = f"short_{audio_path.stem}.mp4"
                output_path = shorts_folder / output_name

                # Verifica se o short já foi gerado
                if output_path.exists():
                    self.log(f"⏭️ Pulado (já existe): {output_name}")
                    continue

                final_clip.write_videofile(str(output_path), codec="libx264", audio_codec="aac", threads=4, verbose=False, logger=None)

                self.log(f"✅ Gerado: {output_name}")

                # Cleanup
                audio_clip.close()
                video_clip.close()
                subclip.close()
                final_clip.close()

            except Exception as e:
                self.log(f"❌ Erro em {audio_path.name}: {str(e)}")

        messagebox.showinfo("Concluído", "Todos os shorts foram gerados!")
        self.log("✅ Finalizado com sucesso!")

if __name__ == "__main__":
    root = tk.Tk()
    app = ShortsMakerSimples(root)
    root.mainloop()
