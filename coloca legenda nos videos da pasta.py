import whisper
import os
import srt
import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk, colorchooser
import subprocess

# Configurações padrão
MODELO_WHISPER = "small"
FONTE_PADRAO = "Arial"
TAMANHO_PADRAO = 8
COR_PADRAO = "#DAA520"  # Amarelo mostarda
POSICAO_VERTICAL_PADRAO = 20  # Porcentagem (0=topo, 100=base)
ESPACAMENTO_PADRAO = 0.2  # Fator de espaçamento entre legendas

class LegendadorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Legendador Automático")
        self.root.geometry("850x600")
        self.root.configure(bg="#f0f0f0")

        # Variáveis de configuração
        self.fonte_legenda = tk.StringVar(value=FONTE_PADRAO)
        self.tamanho_legenda = tk.IntVar(value=TAMANHO_PADRAO)
        self.cor_legenda = tk.StringVar(value=COR_PADRAO)
        self.posicao_vertical = tk.IntVar(value=POSICAO_VERTICAL_PADRAO)
        self.espacamento_legenda = tk.DoubleVar(value=ESPACAMENTO_PADRAO)
        self.modelo_whisper = tk.StringVar(value=MODELO_WHISPER)

        self.criar_interface()

    def criar_interface(self):
        # Frame de configurações
        config_frame = tk.LabelFrame(self.root, text="Configurações das Legendas", bg="#f0f0f0", padx=10, pady=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)

        # Linha 1 - Fonte e Tamanho
        tk.Label(config_frame, text="Fonte:", bg="#f0f0f0").grid(row=0, column=0, sticky=tk.W)
        fontes = ['Arial', 'Helvetica', 'Times New Roman', 'Courier New', 'Verdana']
        fonte_menu = ttk.Combobox(config_frame, textvariable=self.fonte_legenda, values=fontes, width=15)
        fonte_menu.grid(row=0, column=1, sticky=tk.W, padx=5)

        tk.Label(config_frame, text="Tamanho:", bg="#f0f0f0").grid(row=0, column=2, sticky=tk.W)
        ttk.Spinbox(config_frame, from_=10, to=50, textvariable=self.tamanho_legenda, width=5).grid(row=0, column=3, sticky=tk.W, padx=5)

        tk.Label(config_frame, text="Cor:", bg="#f0f0f0").grid(row=0, column=4, sticky=tk.W)
        cor_btn = tk.Button(config_frame, text="Selecionar", command=self.selecionar_cor, bg=self.cor_legenda.get())
        cor_btn.grid(row=0, column=5, sticky=tk.W, padx=5)
        self.cor_btn = cor_btn

        # Linha 2 - Posição e Espaçamento
        tk.Label(config_frame, text="Posição Vertical (%):", bg="#f0f0f0").grid(row=1, column=0, sticky=tk.W)
        ttk.Scale(config_frame, from_=0, to=100, variable=self.posicao_vertical, command=self.atualizar_posicao).grid(row=1, column=1, sticky=tk.W, padx=5)
        self.posicao_label = tk.Label(config_frame, text="90%", bg="#f0f0f0")
        self.posicao_label.grid(row=1, column=2, sticky=tk.W)

        tk.Label(config_frame, text="Espaçamento:", bg="#f0f0f0").grid(row=1, column=3, sticky=tk.W)
        ttk.Spinbox(config_frame, from_=0.1, to=2, increment=0.1, textvariable=self.espacamento_legenda, width=5).grid(row=1, column=4, sticky=tk.W, padx=5)

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
        self.log_text.insert(tk.END, mensagem + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def transcrever_video(self, video_path):
        model = whisper.load_model(self.modelo_whisper.get())
        result = model.transcribe(video_path)
        return result["segments"]

    def gerar_srt(self, segments, srt_path):
        legendas = []
        espacamento = self.espacamento_legenda.get()
        
        for i, seg in enumerate(segments):
            start = seg['start']
            end = seg['end']
            
            if i > 0:
                tempo_anterior = legendas[-1].end.total_seconds()
                diferenca = start - tempo_anterior
                start = tempo_anterior + (diferenca * espacamento)
            
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
            
            self.log("Adicionando legendas ao vídeo...")
            
            # Configurações de estilo
            fonte = self.fonte_legenda.get()
            tamanho = self.tamanho_legenda.get()
            cor = self.cor_legenda.get()
            posicao_pct = self.posicao_vertical.get() / 100
            
            # Filtro de legenda com posicionamento vertical correto
            filtro_legenda = (
                f"subtitles='{srt_path.replace('\\', '/').replace(':', '\\:')}':"
                f"force_style='FontName={fonte},FontSize={tamanho},"
                f"PrimaryColour={self.cor_para_ass(cor)},"
                f"Alignment=2,MarginV={int((1-posicao_pct)*100)},Outline=1,Shadow=0'"
            )
            
            cmd = [
                'ffmpeg',
                '-y',
                '-i', video_path,
                '-vf', filtro_legenda,
                '-c:a', 'copy',
                output_path
            ]
            
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            os.remove(srt_path)
            return True
            
        except Exception as e:
            self.log(f"Erro: {str(e)}")
            if os.path.exists(srt_path):
                try:
                    os.remove(srt_path)
                except:
                    pass
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
        
        self.log(f"Pasta selecionada: {pasta}")
        
        output_dir = os.path.join(pasta, "legendados")
        os.makedirs(output_dir, exist_ok=True)
        self.log(f"Pasta de saída criada: {output_dir}")
        
        self.log("Procurando vídeos...")
        
        videos = [f for f in os.listdir(pasta) if f.lower().endswith('.mp4')]
        
        if not videos:
            messagebox.showwarning("Aviso", "Nenhum vídeo MP4 encontrado na pasta.")
            return
        
        self.log(f"Encontrados {len(videos)} vídeos para processar.")
        
        for video in videos:
            video_path = os.path.join(pasta, video)
            output_path = os.path.join(output_dir, video)
            
            if os.path.exists(output_path):
                self.log(f"Pulando {video} (já existe versão legendada)")
                continue
            
            self.log(f"\nProcessando: {video}")
            if self.processar_video(video_path, output_path):
                self.log(f"Concluído: {video}")
            else:
                self.log(f"Falha ao processar: {video}")
        
        self.log("\nProcessamento concluído!")
        messagebox.showinfo("Finalizado", f"Todos os vídeos foram processados e salvos em:\n{output_dir}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LegendadorApp(root)
    root.mainloop()