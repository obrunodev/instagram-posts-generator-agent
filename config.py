import os
from pathlib import Path
from dotenv import load_dotenv

# Caminho base do projeto
BASE_DIR = Path(__file__).resolve().parent

# Carrega as variáveis de ambiente do arquivo .env no diretório base
dotenv_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=dotenv_path)

# Chave da API do Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Nome do banco de dados SQLite local
DB_NAME = os.getenv("DB_NAME", str(BASE_DIR / "posts.db"))

def validate_config():
    """Valida as configurações essenciais para o funcionamento do agente."""
    if not GEMINI_API_KEY:
        raise ValueError(
            "A variável de ambiente 'GEMINI_API_KEY' não está definida.\n"
            "Por favor, copie o arquivo '.env.example' para '.env' e insira sua chave da API do Gemini."
        )
