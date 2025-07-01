import os
import asyncio
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import edge_tts

class EdgeTTSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor .txt para Áudio (edge-tts) - Avançado")
        self.root.geometry("750x600")
        
        # Variáveis de estado
        self.folder_path = ""
        self.voices = []
        self.voice_map = {}
        self.is_processing = False
        
        # Configurar estilo
        self.style = ttk.Style()
        self.style.configure('TButton', padding=5)
        self.style.configure('TLabel', padding=5)
        
        # Frame principal
        main_frame = ttk.Frame(root)
        main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Frame de configuração
        config_frame = ttk.LabelFrame(main_frame, text="Configurações", padding=10)
        config_frame.pack(fill=tk.X, pady=5)
        
        # Seleção de pasta
        ttk.Button(config_frame, text="Selecionar Pasta", command=self.select_folder).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.folder_label = ttk.Label(config_frame, text="Nenhuma pasta selecionada")
        self.folder_label.grid(row=0, column=1, padx=5, sticky=tk.W)
        
        # Carregar vozes
        ttk.Button(config_frame, text="Carregar Vozes", command=self.load_voices).grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.voice_combo = ttk.Combobox(config_frame, state="readonly", width=50)
        self.voice_combo.grid(row=1, column=1, padx=5, sticky=tk.W)
        ttk.Button(config_frame, text="Testar Voz", command=self.test_voice).grid(row=1, column=2, padx=5, sticky=tk.W)
        
        # Configurações de voz
        ttk.Label(config_frame, text="Velocidade (-100 a +100):").grid(row=2, column=0, padx=5, sticky=tk.E)
        self.speed_entry = ttk.Entry(config_frame, width=10)
        self.speed_entry.insert(0, "0")
        self.speed_entry.grid(row=2, column=1, padx=5, sticky=tk.W)
        
        # Frame de progresso
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        self.progress = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(fill=tk.X, expand=True)
        self.progress_label = ttk.Label(progress_frame, text="Pronto")
        self.progress_label.pack()
        
        # Controles
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)
        self.convert_btn = ttk.Button(control_frame, text="Converter Arquivos", command=self.start_conversion)
        self.convert_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Limpar Log", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Abrir Pasta de Saída", command=self.open_output_folder).pack(side=tk.RIGHT, padx=5)
        
        # Log
        log_frame = ttk.LabelFrame(main_frame, text="Log de Conversão", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_area = scrolledtext.ScrolledText(log_frame, width=85, height=20, state="disabled")
        self.log_area.pack(fill=tk.BOTH, expand=True)
        
        # Desabilitar botões inicialmente
        self.toggle_buttons(False)

    def toggle_buttons(self, enable):
        state = "normal" if enable else "disabled"
        self.convert_btn.config(state=state)
        
    def log(self, message):
        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state="disabled")
        self.root.update_idletasks()

    def clear_log(self):
        self.log_area.config(state="normal")
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state="disabled")

    def select_folder(self):
        self.folder_path = filedialog.askdirectory()
        if self.folder_path:
            self.folder_label.config(text=self.folder_path)
            if self.voice_combo['values']:
                self.toggle_buttons(True)

    def load_voices(self):
        async def fetch():
            try:
                voices = await edge_tts.list_voices()
                filtered = [v for v in voices if v["Locale"].startswith(("pt", "en"))]  # Português e Inglês
                self.voices = sorted(filtered, key=lambda x: (x["Locale"], x["Gender"]))
                self.voice_map = {f'{v["ShortName"]} - {v["Gender"]} ({v["Locale"]})': v["ShortName"] for v in self.voices}
                self.voice_combo["values"] = list(self.voice_map.keys())
                if self.voice_map:
                    self.voice_combo.current(0)
                    if self.folder_path:
                        self.toggle_buttons(True)
                    self.log(f"✅ {len(self.voices)} vozes carregadas")
            except Exception as e:
                self.log(f"❌ Erro ao carregar vozes: {str(e)}")
                messagebox.showerror("Erro", f"Não foi possível carregar as vozes: {str(e)}")

        threading.Thread(target=lambda: asyncio.run(fetch()), daemon=True).start()

    def test_voice(self):
        voice_display = self.voice_combo.get()
        if not voice_display or voice_display not in self.voice_map:
            messagebox.showwarning("Aviso", "Selecione uma voz primeiro.")
            return

        text = "Esta é uma prévia de como ficará a voz selecionada."
        threading.Thread(target=self.preview_voice, args=(text,), daemon=True).start()

    def preview_voice(self, text):
        voice_short = self.voice_map[self.voice_combo.get()]
        speed = self.get_speed()
        
        async def speak():
            try:
                communicate = edge_tts.Communicate(text, voice=voice_short, rate=speed)
                await communicate.save("preview.mp3")
                os.startfile("preview.mp3")
            except Exception as e:
                self.log(f"❌ Erro na prévia: {str(e)}")

        asyncio.run(speak())

    def get_speed(self):
        try:
            speed_percent = int(self.speed_entry.get().strip())
            if not -100 <= speed_percent <= 100:
                raise ValueError()
            return f"{'+' if speed_percent >= 0 else ''}{speed_percent}%"
        except ValueError:
            messagebox.showerror("Erro", "Velocidade inválida. Use um valor entre -100 e +100.")
            return "+0%"

    def start_conversion(self):
        if self.is_processing:
            return
            
        self.is_processing = True
        self.toggle_buttons(False)
        threading.Thread(target=self.convert_all, daemon=True).start()

    def convert_all(self):
        try:
            if not self.folder_path:
                messagebox.showerror("Erro", "Selecione uma pasta.")
                return

            voice_display = self.voice_combo.get()
            if voice_display not in self.voice_map:
                messagebox.showerror("Erro", "Selecione uma voz.")
                return

            voice_short = self.voice_map[voice_display]
            speed = self.get_speed()

            # Cria a pasta de saída
            output_folder = os.path.join(self.folder_path, "audios_gerados")
            os.makedirs(output_folder, exist_ok=True)

            # Encontra todos os arquivos de texto
            arquivos = [f for f in os.listdir(self.folder_path) 
                      if f.lower().endswith((".txt", ".md", ".docx", ".pdf"))]  # Adicione mais extensões se necessário
            
            if not arquivos:
                self.log("ℹ️ Nenhum arquivo de texto encontrado.")
                return

            self.progress["maximum"] = len(arquivos)
            self.progress["value"] = 0
            self.progress_label.config(text="Preparando...")

            async def run_conversion():
                for i, filename in enumerate(arquivos):
                    if not self.is_processing:  # Permite cancelar
                        break
                        
                    txt_path = os.path.join(self.folder_path, filename)
                    output = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.mp3")

                    self.progress_label.config(text=f"Processando: {filename}")
                    self.progress["value"] = i + 1
                    self.root.update_idletasks()

                    if os.path.exists(output):
                        self.log(f"⏩ Pulando (já existe): {filename}")
                        continue

                    try:
                        with open(txt_path, "r", encoding="utf-8") as file:
                            text = file.read().strip()

                        if not text:
                            self.log(f"⚠️ Arquivo vazio: {filename}")
                            continue

                        # Formatação correta sem o parâmetro ssml
                        communicate = edge_tts.Communicate(text, voice=voice_short, rate=speed)
                        await communicate.save(output)
                        self.log(f"✅ Finalizado: {filename}")

                    except Exception as e:
                        self.log(f"❌ Erro em {filename}: {str(e)}")

                    except Exception as e:
                        self.log(f"❌ Erro em {filename}: {str(e)}")

                self.progress_label.config(text="Concluído" if self.is_processing else "Cancelado")
                self.is_processing = False
                self.toggle_buttons(True)
                if self.is_processing:
                    self.log("🎉 Conversão concluída para todos os arquivos!")
                self.root.bell()  # Notificação sonora

            asyncio.run(run_conversion())
            
        except Exception as e:
            self.log(f"❌ Erro inesperado: {str(e)}")
            self.is_processing = False
            self.toggle_buttons(True)
            self.progress_label.config(text="Erro")

    def open_output_folder(self):
        if not self.folder_path:
            messagebox.showwarning("Aviso", "Nenhuma pasta selecionada.")
            return
            
        output_folder = os.path.join(self.folder_path, "audios_gerados")
        if os.path.exists(output_folder):
            os.startfile(output_folder)
        else:
            messagebox.showinfo("Informação", "A pasta de saída ainda não foi criada.")

if __name__ == "__main__":
    root = tk.Tk()
    app = EdgeTTSApp(root)
    root.mainloop()