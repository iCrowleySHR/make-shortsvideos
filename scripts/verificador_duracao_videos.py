import os
import subprocess
import shutil
from datetime import timedelta
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext

class VideoDurationChecker:
    def __init__(self, root):
        self.root = root
        self.root.title("Verificador de Duração de Vídeos")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Variáveis
        self.pasta_videos = tk.StringVar()
        self.duracao_maxima = tk.IntVar(value=180)  # 3 minutos padrão
        
        # Configurar interface
        self.setup_ui()
        
    def setup_ui(self):
        # Frame principal
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Seletor de pasta
        tk.Label(main_frame, text="Pasta com Vídeos:").grid(row=0, column=0, sticky="w", pady=5)
        path_frame = tk.Frame(main_frame)
        path_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        
        self.path_entry = tk.Entry(path_frame, textvariable=self.pasta_videos, width=50)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Button(
            path_frame, 
            text="Procurar...", 
            command=self.selecionar_pasta
        ).pack(side=tk.LEFT, padx=5)
        
        # Configuração de duração
        tk.Label(main_frame, text="Duração Máxima (segundos):").grid(row=2, column=0, sticky="w", pady=5)
        tk.Entry(main_frame, textvariable=self.duracao_maxima, width=10).grid(row=2, column=1, sticky="w", pady=5)
        
        # Botão de processamento
        tk.Button(
            main_frame, 
            text="Verificar Vídeos", 
            command=self.verificar_videos,
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=10
        ).grid(row=3, column=0, columnspan=2, pady=20)
        
        # Área de log
        tk.Label(main_frame, text="Log de Processamento:").grid(row=4, column=0, sticky="w", pady=5)
        
        self.log_text = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            width=80,
            height=20,
            font=("Consolas", 10)
        )
        self.log_text.grid(row=5, column=0, columnspan=2, sticky="nsew")
        
        # Barra de progresso
        self.progress = ttk.Progressbar(
            main_frame,
            orient=tk.HORIZONTAL,
            length=400,
            mode='determinate'
        )
        self.progress.grid(row=6, column=0, columnspan=2, pady=10, sticky="ew")
        
        # Configurar expansão
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
    def selecionar_pasta(self):
        pasta = filedialog.askdirectory()
        if pasta:
            self.pasta_videos.set(pasta)
            self.log("Pasta selecionada: " + pasta)
    
    def log(self, mensagem):
        self.log_text.insert(tk.END, mensagem + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def obter_duracao_video(self, caminho_video):
        """Obtém a duração do vídeo em segundos usando ffprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                caminho_video
            ]
            
            resultado = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(resultado.stdout.strip())
        except subprocess.CalledProcessError as e:
            self.log(f"Erro ao verificar {os.path.basename(caminho_video)}: {e.stderr}")
            return None
        except Exception as e:
            self.log(f"Erro inesperado com {os.path.basename(caminho_video)}: {e}")
            return None
    
    def formatar_duracao(self, segundos):
        """Formata segundos para formato HH:MM:SS"""
        return str(timedelta(seconds=segundos)).split('.')[0]
    
    def verificar_videos(self):
        if not self.pasta_videos.get():
            messagebox.showerror("Erro", "Selecione uma pasta primeiro!")
            return
        
        if not shutil.which('ffprobe'):
            messagebox.showerror("Erro", "ffprobe não encontrado. Instale o FFmpeg primeiro.")
            return
        
        self.log("\n" + "="*50)
        self.log(f"Verificando vídeos em: {self.pasta_videos.get()}")
        self.log(f"Duração máxima permitida: {self.duracao_maxima.get()}s ({self.formatar_duracao(self.duracao_maxima.get())})")
        
        try:
            videos = [
                f for f in os.listdir(self.pasta_videos.get()) 
                if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))
            ]
            total_videos = len(videos)
            
            if total_videos == 0:
                self.log("Nenhum vídeo encontrado na pasta!")
                return
            
            self.log(f"\nEncontrados {total_videos} vídeos para análise...")
            
            excluidos = 0
            erros = 0
            self.progress['maximum'] = total_videos
            self.progress['value'] = 0
            
            for i, video in enumerate(videos):
                caminho = os.path.join(self.pasta_videos.get(), video)
                try:
                    duracao = self.obter_duracao_video(caminho)
                    self.progress['value'] = i + 1
                    self.root.update_idletasks()
                    
                    if duracao is None:
                        erros += 1
                        continue
                    
                    self.log(f"\n{video}: {self.formatar_duracao(duracao)}")
                    
                    if duracao > self.duracao_maxima.get():
                        self.log("EXCLUINDO (maior que o limite)")
                        os.remove(caminho)
                        excluidos += 1
                    else:
                        self.log("OK (dentro do limite)")
                        
                except Exception as e:
                    self.log(f"Erro ao processar {video}: {e}")
                    erros += 1
            
            # Relatório final
            self.log("\n" + "="*50)
            self.log("RELATÓRIO FINAL:")
            self.log(f"- Vídeos analisados: {total_videos}")
            self.log(f"- Vídeos excluídos: {excluidos}")
            self.log(f"- Vídeos mantidos: {total_videos - excluidos - erros}")
            self.log(f"- Erros encontrados: {erros}")
            self.log("="*50)
            
            messagebox.showinfo("Concluído", "Processamento finalizado!")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoDurationChecker(root)
    root.mainloop()