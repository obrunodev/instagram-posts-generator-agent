from pathlib import Path
from google import genai
from google.genai import types
from src.core import config

def transcrever_e_resumir(caminho_audio: Path) -> str:
    """
    Faz o upload do arquivo de áudio para a API do Gemini Files e solicita
    a transcrição detalhada e o resumo técnico em formato Markdown.
    """
    config.validate_config()
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    
    print(f"📤 Enviando arquivo de áudio para a API de arquivos do Gemini ({caminho_audio.name})...")
    # Faz o upload do áudio usando a API de Files do SDK google-genai
    audio_file = client.files.upload(file=caminho_audio)
    print(f"✅ Arquivo enviado. ID do Recurso: {audio_file.name}")
    
    system_instruction = (
        "Você é um Engenheiro de Software Sênior especialista em Backend e Ciência de Dados, altamente didático.\n"
        "Seu papel é transcrever e resumir o conteúdo do áudio técnico fornecido em formato Markdown limpo.\n\n"
        "DIRETRIZES DO OUTPUT:\n"
        "1. Transcreva o áudio com alta fidelidade para termos técnicos (Python, Django, FastAPI, Docker, bancos de dados, etc).\n"
        "2. Formate o documento final estritamente usando o seguinte padrão Markdown:\n"
        "   # [Título Principal do Vídeo]\n\n"
        "   ## Conceitos Chave\n"
        "   (Apresente uma lista em bullet points com as ideias centrais e termos chave explicados de forma concisa)\n\n"
        "   ## Explicação Detalhada\n"
        "   (Desenvolva um texto completo resumindo o aprendizado de forma detalhada e dividida por seções lógicas)\n\n"
        "   ## Código e Exemplos Práticos\n"
        "   (Inclua blocos de código com a sintaxe correta e comentários didáticos explicativos do que foi ensinado)\n"
        "3. Não adicione tags de bloco adicionais ou explicações fora do Markdown solicitado."
    )
    
    prompt = "Transcreva este áudio detalhadamente e formate o resumo técnico seguindo as diretrizes especificadas."
    
    print("🤖 Solicitando transcrição e resumo ao Gemini 2.5 Flash...")
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[audio_file, prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3, # Baixa temperatura para maior precisão factual
            )
        )
        
        # Opcional: deletar o arquivo da nuvem da API do Gemini para cleanup
        try:
            print("Cleanup: Removendo arquivo da API de Files do Gemini...")
            client.files.delete(name=audio_file.name)
        except Exception as e:
            print(f"⚠️ Alerta no cleanup do Gemini Files: {e}")
            
        return response.text
        
    except Exception as e:
        print(f"❌ Erro ao processar áudio no Gemini: {e}")
        raise
