import whisper
import os
import srt
import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk, colorchooser
from tkinter import font as tkfont
import subprocess
from pathlib import Path
import threading
from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip
from moviepy.config import change_settings

change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe"})

class LegendadorApp:
    # Configurações padrão
    VIDEO_EXTENSIONS = ['mp4', 'mkv', 'avi', 'mov', 'flv', 'wmv', 'm4v', 'webm', 'mpg', 'mpeg', 'ts', 'ogv', '3gp']
    MODELO_WHISPER = "small"
    FONTE_PADRAO = "Arial"
    TAMANHO_PADRAO = 54
    COR_PADRAO = "#DAA520"  # Amarelo mostarda
    POSICAO_VERTICAL_PADRAO = 20  # Porcentagem (0=topo, 100=base)

    def __init__(self, root):
        self.root = root
        self.root.title("Legendador Automático")
        self.root.geometry("850x600")
        self.root.configure(bg="#f0f0f0")

        # Variáveis de configuração
        self.fonte_legenda = tk.StringVar(value=self.FONTE_PADRAO)
        self.tamanho_legenda = tk.IntVar(value=self.TAMANHO_PADRAO)
        self.cor_legenda = tk.StringVar(value=self.COR_PADRAO)
        self.posicao_vertical = tk.IntVar(value=self.POSICAO_VERTICAL_PADRAO)
        self.modelo_whisper = tk.StringVar(value=self.MODELO_WHISPER)

        self.criar_interface()

    def criar_interface(self):
        # Frame de configurações
        config_frame = tk.LabelFrame(self.root, text="Configurações das Legendas", bg="#f0f0f0", padx=10, pady=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)

        # Linha 1 - Fonte e Tamanho
        tk.Label(config_frame, text="Fonte:", bg="#f0f0f0").grid(row=0, column=0, sticky=tk.W)

        fontes = self.listar_fontes_imagemagick()
        if not fontes:
            fontes = [self.FONTE_PADRAO] 

        fonte_menu = ttk.Combobox(config_frame, textvariable=self.fonte_legenda, values=fontes, width=30)
        fonte_menu.grid(row=0, column=1, sticky=tk.W, padx=5)


        tk.Label(config_frame, text="Tamanho:", bg="#f0f0f0").grid(row=0, column=2, sticky=tk.W)
        ttk.Spinbox(config_frame, from_=10, to=50, textvariable=self.tamanho_legenda, width=5).grid(row=0, column=3, sticky=tk.W, padx=5)

        tk.Label(config_frame, text="Cor:", bg="#f0f0f0").grid(row=0, column=4, sticky=tk.W)
        cor_btn = tk.Button(config_frame, text="Selecionar", command=self.selecionar_cor, bg=self.cor_legenda.get())
        cor_btn.grid(row=0, column=5, sticky=tk.W, padx=5)
        self.cor_btn = cor_btn

        # Linha 2 - Posição e Modelo
        tk.Label(config_frame, text="Posição Vertical (%):", bg="#f0f0f0").grid(row=1, column=0, sticky=tk.W)
        ttk.Scale(config_frame, from_=0, to=100, variable=self.posicao_vertical, command=self.atualizar_posicao).grid(row=1, column=1, sticky=tk.W, padx=5)
        self.posicao_label = tk.Label(config_frame, text=f"{self.POSICAO_VERTICAL_PADRAO}%", bg="#f0f0f0")
        self.posicao_label.grid(row=1, column=2, sticky=tk.W)

        tk.Label(config_frame, text="Modelo Whisper:", bg="#f0f0f0").grid(row=1, column=5, sticky=tk.W)
        modelos = ['tiny', 'base', 'small', 'medium', 'large']
        modelo_menu = ttk.Combobox(config_frame, textvariable=self.modelo_whisper, values=modelos, width=10)
        modelo_menu.grid(row=1, column=6, sticky=tk.W, padx=5)

        # Botão de processamento
        btn_frame = tk.Frame(self.root, bg="#f0f0f0")
        btn_frame.pack(pady=10)
        tk.Button(
            btn_frame, 
            text="Selecionar Pasta com Vídeos", 
            command=self.selecionar_pasta,
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=10
        ).pack()

        tk.Button(
            btn_frame, 
            text="Selecionar Vídeo Único", 
            command=self.selecionar_video,
            font=("Arial", 12),
            bg="#2196F3",
            fg="white",
            padx=20,
            pady=10
        ).pack(pady=5)

        # Área de log
        log_frame = tk.LabelFrame(self.root, text="Log de Processamento", bg="#f0f0f0")
        log_frame.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            width=80,
            height=20,
            font=("Consolas", 10),
            bg="black",
            fg="white"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def atualizar_posicao(self, val):
        self.posicao_label.config(text=f"{int(float(val))}%")

    def selecionar_cor(self):
        cor = colorchooser.askcolor(title="Selecione a cor da legenda", initialcolor=self.cor_legenda.get())
        if cor[1]:
            self.cor_legenda.set(cor[1])
            self.cor_btn.config(bg=cor[1])

    def log(self, mensagem):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {mensagem}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def transcrever_video(self, video_path):
        model = whisper.load_model(self.modelo_whisper.get())
        result = model.transcribe(video_path)
        return result["segments"]

    def listar_fontes_imagemagick(self):
        try:
            resultado = subprocess.run(
                ['magick', '-list', 'font'],
                capture_output=True,
                text=True,
                check=True
            )
            saida = resultado.stdout
            nomes_fontes = []
            for linha in saida.splitlines():
                if linha.strip().startswith("Font:"):
                    partes = linha.split(":", 1)
                    if len(partes) == 2:
                        nome_fonte = partes[1].strip()
                        nomes_fontes.append(nome_fonte)
            return sorted(nomes_fontes)
        except Exception as e:
            self.log(f"Erro ao listar fontes do ImageMagick: {e}")
            return []

    def gerar_srt(self, segments, srt_path):
        legendas = []

        for i, seg in enumerate(segments):
            start = seg['start']
            end = seg['end']

            start_time = datetime.timedelta(seconds=start)
            end_time = datetime.timedelta(seconds=end)
            texto = ' '.join(seg['text'].strip().split())

            legenda = srt.Subtitle(
                index=i+1,
                start=start_time,
                end=end_time,
                content=texto
            )
            legendas.append(legenda)

        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt.compose(legendas))
        
    def processar_video(self, video_path, output_path):
        try:
            base_name = os.path.splitext(video_path)[0]
            srt_path = f"{base_name}.srt"

            self.log("Transcrevendo áudio...")
            segments = self.transcrever_video(video_path)

            self.log("Gerando legendas SRT...")
            self.gerar_srt(segments, srt_path)

            self.log("Carregando vídeo com MoviePy...")
            video = VideoFileClip(video_path)
            legendas = []

            fonte_nome = self.fonte_legenda.get()
            tamanho = int(self.tamanho_legenda.get())
            cor = self.cor_legenda.get()
            cor_contorno = "black"  # Cor do contorno
            espessura_contorno = 5   # Espessura do contorno
            posicao_pct = self.posicao_vertical.get() / 100

            altura_legenda = int(video.h * posicao_pct)

            self.log("Renderizando legendas no vídeo...")

            for seg in segments:
                texto = seg['text'].strip()
                if not texto:
                    continue

                # Configurações comuns para contorno e texto principal
                text_kwargs = {
                    'txt': texto,
                    'fontsize': tamanho,
                    'font': fonte_nome,
                    'method': 'caption',  # Ou 'pango' se disponível
                    'size': (video.w * 0.9, None),  # Largura fixa, altura automática
                    'align': 'center',
                    'print_cmd': True  # Debug (opcional)
                }

                # Camada de contorno (stroke externo)
                contorno = TextClip(
                    **text_kwargs,
                    color=cor_contorno,
                    stroke_color=cor_contorno,
                    stroke_width=espessura_contorno * 2,  # Stroke mais largo
                ).set_position(("center", altura_legenda)).set_duration(seg['end'] - seg['start']).set_start(seg['start'])

                # Camada de texto principal (sem stroke)
                texto_principal = TextClip(
                    **text_kwargs,
                    color=cor,
                    stroke_width=0,  # Sem contorno
                ).set_position(("center", altura_legenda)).set_duration(seg['end'] - seg['start']).set_start(seg['start'])

                # Adiciona ambas as camadas (contorno primeiro)
                legendas.extend([contorno, texto_principal])

            video_final = CompositeVideoClip([video] + legendas)
            video_final.write_videofile(output_path, codec="libx264", audio_codec="aac")

            os.remove(srt_path)
            return True

        except Exception as e:
            self.log(f"Erro ao processar vídeo com MoviePy: {e}")
            return False

    def cor_para_ass(self, cor_hex):
        """Converte cor hex para formato ASS (BGR)"""
        if cor_hex.startswith('#'):
            cor_hex = cor_hex[1:]
        r = int(cor_hex[0:2], 16)
        g = int(cor_hex[2:4], 16)
        b = int(cor_hex[4:6], 16)
        return f"&H{b:02X}{g:02X}{r:02X}&"

    def selecionar_pasta(self):
        pasta = filedialog.askdirectory()
        if not pasta:
            return
        
        thread = threading.Thread(target=self.processar_pasta, args=(pasta,), daemon=True)
        thread.start()
    
    def selecionar_video(self):
        caminho_video = filedialog.askopenfilename(
            filetypes=[("Vídeos", "*.mp4 *.mkv *.avi *.mov *.flv *.wmv *.m4v *.webm *.mpg *.mpeg *.ts *.ogv *.3gp")]
        )
        if not caminho_video:
            return

        pasta_origem = os.path.dirname(caminho_video)
        nome_arquivo = Path(caminho_video).stem
        extensao = Path(caminho_video).suffix

        output_dir = os.path.join(pasta_origem, "legendados")
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, f"{nome_arquivo}_legendado{extensao}")

        self.log(f"\nProcessando vídeo único: {nome_arquivo + extensao}")
        thread = threading.Thread(target=self.processar_unico, args=(caminho_video, output_path), daemon=True)
        thread.start()

    def processar_unico(self, video_path, output_path):
        if os.path.exists(output_path):
            self.log("Versão legendada já existe. Pulando.")
        else:
            if self.processar_video(video_path, output_path):
                self.log(f"Concluído: {os.path.basename(video_path)}")
                self.root.after(0, lambda: messagebox.showinfo("Finalizado", "Vídeo legendado com sucesso!"))
            else:
                self.log(f"Erro ao processar: {os.path.basename(video_path)}")


    def processar_pasta(self, pasta):
        self.log(f"Pasta selecionada: {pasta}")
        
        output_dir = os.path.join(pasta, "legendados")
        os.makedirs(output_dir, exist_ok=True)
        self.log(f"Pasta de saída criada: {output_dir}")
        
        self.log("Procurando vídeos...")
        
        videos = []
        for f in os.listdir(pasta):
            file_path = os.path.join(pasta, f)
            if os.path.isfile(file_path):
                ext = Path(f).suffix[1:].lower()
                if ext in self.VIDEO_EXTENSIONS:
                    videos.append(f)
        
        if not videos:
            self.root.after(0, lambda: messagebox.showwarning(
                "Aviso", 
                f"Nenhum vídeo encontrado na pasta. Formatos suportados: {', '.join(self.VIDEO_EXTENSIONS)}"
            ))
            return
        
        self.log(f"Encontrados {len(videos)} vídeos para processar.")
        
        for video in videos:
            video_path = os.path.join(pasta, video)
            output_name = f"{Path(video).stem}_legendado{Path(video).suffix}"
            output_path = os.path.join(output_dir, output_name)
            
            if os.path.exists(output_path):
                self.log(f"Pulando {video} (já existe versão legendada)")
                continue
            
            self.log(f"\nProcessando: {video}")
            if self.processar_video(video_path, output_path):
                self.log(f"Concluído: {video}")
            else:
                self.log(f"Falha ao processar: {video}")
        
        self.log("\nProcessamento concluído!")
        self.root.after(0, lambda: messagebox.showinfo(
            "Finalizado", 
            f"Todos os vídeos foram processados e salvos em:\n{output_dir}"
        ))


if __name__ == "__main__":
    root = tk.Tk()
    app = LegendadorApp(root)
    root.mainloop()
