import tkinter as tk
from tkinter import filedialog, messagebox
import yt_dlp as ytdlp
import moviepy as mp
import os

def download_video_or_playlist():
    url = url_entry.get()
    output_format = format_var.get()
    
    if not url:
        messagebox.showwarning("Aviso", "Por favor, insira o link do YouTube.")
        return
    
    save_path = filedialog.askdirectory(title="Escolha a pasta de destino")
    if not save_path:
        return
    
    download_button.config(state=tk.DISABLED)
    root.update()
    
    ydl_opts = {
        'format': 'bestaudio/best' if output_format == 'mp3' else 'best',
        'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
        'ignoreerrors': True,
        'quiet': True,
        'no_warnings': True,
        # Para facilitar o controle dos arquivos baixados
        'progress_hooks': [],
    }
    
    downloaded_files = []
    errors = []
    
    def progress_hook(d):
        if d['status'] == 'finished':
            downloaded_files.append(d['filename'])
    
    ydl_opts['progress_hooks'].append(progress_hook)
    
    try:
        with ytdlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
        
        # Depois do download, se mp3, converte os arquivos baixados (que não forem mp3)
        if output_format == 'mp3':
            converted = 0
            for file_path in downloaded_files:
                ext = os.path.splitext(file_path)[1].lower()
                if ext != '.mp3':
                    mp3_file_path = os.path.splitext(file_path)[0] + '.mp3'
                    try:
                        audio_clip = mp.AudioFileClip(file_path)
                        audio_clip.write_audiofile(mp3_file_path)
                        audio_clip.close()
                        os.remove(file_path)
                        converted += 1
                    except Exception as e:
                        errors.append(f"Erro ao converter {file_path}: {e}")
            
            message = f"Download finalizado.\nArquivos convertidos para MP3: {converted}.\n"
            if errors:
                message += "\nErros durante a conversão:\n" + "\n".join(errors)
            messagebox.showinfo("Sucesso", message)
        else:
            messagebox.showinfo("Sucesso", f"Download finalizado.\nTotal de arquivos baixados: {len(downloaded_files)}")
    
    except Exception as e:
        messagebox.showerror("Erro", f'Erro ao baixar: {e}')
    
    finally:
        download_button.config(state=tk.NORMAL)

# Interface
root = tk.Tk()
root.title("YouTube Downloader Playlist / Vídeo")

window_width = 600
window_height = 170
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x_cordinate = int((screen_width/2) - (window_width/2))
y_cordinate = int((screen_height/2) - (window_height/2))
root.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

tk.Label(root, text="Link do YouTube (vídeo ou playlist):").grid(row=0, column=0, padx=10, pady=10, sticky="e")
url_entry = tk.Entry(root, width=50)
url_entry.grid(row=0, column=1, padx=10, pady=10)

tk.Label(root, text="Formato:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
format_var = tk.StringVar(value="mp4")
tk.Radiobutton(root, text="MP4", variable=format_var, value="mp4").grid(row=1, column=1, sticky="w", padx=10)
tk.Radiobutton(root, text="MP3", variable=format_var, value="mp3").grid(row=1, column=1, padx=100, sticky="w")

download_button = tk.Button(root, text="Baixar", command=download_video_or_playlist)
download_button.grid(row=2, column=0, columnspan=2, pady=15)

root.mainloop()
