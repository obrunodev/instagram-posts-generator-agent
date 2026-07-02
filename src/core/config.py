import os
from pathlib import Path
from dotenv import load_dotenv

# Caminho base do projeto (três níveis acima de src/core/config.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Carrega as variáveis de ambiente do arquivo .env no diretório base
dotenv_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=dotenv_path)

# Chave da API do Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Caminho padrão do banco de dados SQLite dentro da pasta data
DB_NAME = os.getenv("DB_NAME", str(BASE_DIR / "data" / "posts.db"))

# Caminho padrão do vault do Obsidian
OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH")

def validate_config():
    """Valida as configurações essenciais para o funcionamento do agente."""
    if not GEMINI_API_KEY:
        raise ValueError(
            "A variável de ambiente 'GEMINI_API_KEY' não está definida.\n"
            "Por favor, copie o arquivo '.env.example' para '.env' e insira sua chave da API do Gemini."
        )
