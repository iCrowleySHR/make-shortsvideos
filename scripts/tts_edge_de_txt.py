import os
import asyncio
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import edge_tts

class EdgeTTSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor .txt para Áudio (edge-tts)")
        self.root.geometry("700x550")

        self.folder_path = ""
        self.voices = []
        self.voice_map = {}

        # Interface
        ttk.Button(root, text="Selecionar Pasta", command=self.select_folder).pack(pady=5)
        self.folder_label = ttk.Label(root, text="Nenhuma pasta selecionada")
        self.folder_label.pack()

        ttk.Button(root, text="Carregar Vozes", command=self.load_voices).pack(pady=5)
        self.voice_combo = ttk.Combobox(root, state="readonly", width=60)
        self.voice_combo.pack(pady=5)

        # Input da velocidade
        ttk.Label(root, text="Velocidade da fala (%) [-100 a +100]").pack(pady=5)
        self.speed_entry = ttk.Entry(root, width=10)
        self.speed_entry.insert(0, "0")  # valor padrão
        self.speed_entry.pack(pady=5)

        ttk.Button(root, text="Converter Arquivos", command=self.start_conversion).pack(pady=10)

        ttk.Label(root, text="Log de Conversão:").pack()
        self.log_area = scrolledtext.ScrolledText(root, width=80, height=20, state="disabled")
        self.log_area.pack(pady=5)

    def log(self, message):
        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state="disabled")
        self.root.update_idletasks()

    def select_folder(self):
        self.folder_path = filedialog.askdirectory()
        if self.folder_path:
            self.folder_label.config(text=self.folder_path)

    def load_voices(self):
        async def fetch():
            voices = await edge_tts.list_voices()
            filtered = [v for v in voices if v["Locale"].startswith("pt")]
            self.voices = filtered
            self.voice_map = {f'{v["ShortName"]} - {v["Gender"]} ({v["Locale"]})': v["ShortName"] for v in filtered}
            self.voice_combo["values"] = list(self.voice_map.keys())
            if self.voice_map:
                self.voice_combo.set("Selecione uma voz")
        asyncio.run(fetch())

    def start_conversion(self):
        threading.Thread(target=self.convert_all).start()

    def convert_all(self):
        if not self.folder_path:
            messagebox.showerror("Erro", "Selecione uma pasta.")
            return

        voice_display = self.voice_combo.get()
        if voice_display not in self.voice_map:
            messagebox.showerror("Erro", "Selecione uma voz.")
            return

        voice_short = self.voice_map[voice_display]

        # Validação da velocidade
        try:
            speed_percent = int(self.speed_entry.get().strip())
            if not -100 <= speed_percent <= 100:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Erro", "Informe um valor de velocidade entre -100 e +100.")
            return

        rate_tag = f'<prosody rate="{speed_percent}%">'  # SSML tag

        # Cria a pasta de saída
        output_folder = os.path.join(self.folder_path, "audios_gerados")
        os.makedirs(output_folder, exist_ok=True)

        async def run_conversion():
            arquivos = [f for f in os.listdir(self.folder_path) if f.lower().endswith(".txt")]
            if not arquivos:
                self.log("Nenhum arquivo .txt encontrado.")
                return

            for filename in arquivos:
                txt_path = os.path.join(self.folder_path, filename)
                output = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.mp3")

                if os.path.exists(output):
                    self.log(f"⏩ Pulando (já existe): {filename}")
                    continue

                with open(txt_path, "r", encoding="utf-8") as file:
                    text = file.read()

                ssml_text = f'<speak>{rate_tag}{text}</prosody></speak>'

                self.log(f"Convertendo: {filename} → {output}")
                try:
                    communicate = edge_tts.Communicate(ssml_text, voice=voice_short, ssml=True)
                    await communicate.save(output)
                    self.log(f"✔️ Finalizado: {filename}")
                except Exception as e:
                    self.log(f"❌ Erro em {filename}: {str(e)}")

            self.log("✅ Conversão concluída para todos os arquivos.")

        asyncio.run(run_conversion())

if __name__ == "__main__":
    root = tk.Tk()
    app = EdgeTTSApp(root)
    root.mainloop()
