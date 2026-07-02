import os
from pathlib import Path
import yt_dlp

def baixar_audio(url: str, output_dir: Path) -> Path:
    """
    Baixa apenas o áudio do vídeo do YouTube no formato m4a/mp3 compactado.
    Retorna o caminho do arquivo de áudio baixado.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
        }],
        'quiet': False,
    }
    
    print(f"📥 Baixando áudio de: {url}...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        # Substitui a extensão original pela do codec extraído (m4a)
        path = Path(filename).with_suffix('.m4a')
        print(f"✨ Áudio baixado com sucesso em: {path}")
        return path
