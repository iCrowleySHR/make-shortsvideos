# 📝 legendador_whisper_gui.py

Este script oferece uma interface gráfica para transcrever e legendar vídeos automaticamente usando o modelo Whisper da OpenAI. Ele permite ao usuário personalizar a aparência da legenda (fonte, cor, tamanho, posição vertical e espaçamento) e aplica as legendas diretamente no vídeo com auxílio do FFmpeg. Os vídeos legendados são salvos em uma subpasta chamada `legendados`.

---

# 🔄 conversor_vertical_gui.py

Este script converte vídeos de vários formatos para o formato vertical (1080x1920) com efeito de fundo borrado (blur). Ele possui uma interface gráfica com barras de progresso que mostram o avanço do processo por vídeo e no total. Os arquivos convertidos são salvos em uma pasta chamada `converted` dentro da pasta selecionada.

---

# ⏱️ verificador_duracao_videos.py

Este script oferece uma interface gráfica para verificar a duração de vídeos dentro de uma pasta. Caso algum vídeo ultrapasse o limite de tempo definido (ex: 180 segundos), ele é automaticamente excluído. Exibe um log com todos os resultados e um relatório final com estatísticas dos vídeos analisados, mantidos e excluídos.

---

# 📥 youtube_channel_downloader.py

Este script permite baixar todos os vídeos de um canal do YouTube (usando URL do tipo `/@handle` ou `/channel/ID`) através de uma interface gráfica. O usuário pode escolher entre baixar os vídeos em formato MP4 ou converter o áudio para MP3 após o download. Os arquivos são salvos na pasta selecionada.

---

# 📥 youtube_video_playlist_downloader.py

Este script oferece uma interface gráfica para baixar vídeos individuais ou playlists completas do YouTube. Ele permite ao usuário escolher entre os formatos MP4 (vídeo) e MP3 (áudio). Após o download, os arquivos são convertidos conforme necessário e salvos na pasta de destino definida pelo usuário.
