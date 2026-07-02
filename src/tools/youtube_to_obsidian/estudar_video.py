import sys
from pathlib import Path
from src.core import config
from src.tools.youtube_to_obsidian import downloader, processador_audio, gerenciador_obsidian

def processar_video(url: str):
    """
    Orquestra o fluxo completo:
    1. Baixa o áudio temporariamente
    2. Transcreve e gera o resumo com IA
    3. Salva no Obsidian Vault
    4. Limpa o áudio temporário local
    """
    audio_path = None
    try:
        # 1. Diretório temporário dentro da pasta de dados local
        temp_dir = config.BASE_DIR / "data" / "temp_audio"
        
        # 2. Baixar áudio
        audio_path = downloader.baixar_audio(url, temp_dir)
        
        # O título do vídeo é obtido a partir do nome do arquivo baixado (sem extensão)
        titulo_video = audio_path.stem
        
        # 3. Enviar ao Gemini para transcrição e resumo
        resumo_markdown = processador_audio.transcrever_e_resumir(audio_path)
        
        # 4. Salvar nota no Obsidian Vault
        gerenciador_obsidian.salvar_nota_obsidian(
            titulo_video=titulo_video,
            url_original=url,
            conteudo_markdown=resumo_markdown
        )
        
        print("\n🎉 Processo concluído com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro durante o processamento do vídeo: {e}", file=sys.stderr)
        
    finally:
        # 5. Cleanup: Remove o arquivo de áudio temporário do disco local
        if audio_path and audio_path.exists():
            try:
                print(f"🧹 Limpando arquivo de áudio local: {audio_path}...")
                audio_path.unlink()
                # Deleta a pasta temporária se estiver vazia
                if not any(audio_path.parent.iterdir()):
                    audio_path.parent.rmdir()
                print("✨ Limpeza concluída!")
            except Exception as e:
                print(f"⚠️ Não foi possível deletar o arquivo temporário: {e}", file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python estudar_video.py <URL_DO_VIDEO>")
        sys.exit(1)
        
    video_url = sys.argv[1]
    processar_video(video_url)
