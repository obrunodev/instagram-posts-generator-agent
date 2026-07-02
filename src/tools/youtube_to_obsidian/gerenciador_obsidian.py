import re
from datetime import datetime
from pathlib import Path
from src.core import config

def limpar_nome_arquivo(nome: str) -> str:
    """Remove caracteres inválidos para nomes de arquivos no Windows/Linux."""
    return re.sub(r'[\\/*?:"<>|]', "", nome).strip()

def salvar_nota_obsidian(titulo_video: str, url_original: str, conteudo_markdown: str) -> Path:
    """
    Formata os metadados (Frontmatter YAML) e salva o markdown final
    diretamente na pasta configurada do Vault do Obsidian.
    """
    if not config.OBSIDIAN_VAULT_PATH:
        raise ValueError(
            "A variável 'OBSIDIAN_VAULT_PATH' não está definida no arquivo .env.\n"
            "Por favor, configure o caminho para o seu Vault para salvar a nota."
        )
        
    vault_dir = Path(config.OBSIDIAN_VAULT_PATH)
    if not vault_dir.exists():
        raise FileNotFoundError(f"O diretório do Vault do Obsidian não foi localizado: {vault_dir}")
        
    # Adiciona metadados Frontmatter no topo do arquivo
    data_hoje = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    frontmatter = (
        "---\n"
        f"title: \"{titulo_video}\"\n"
        f"date: \"{data_hoje}\"\n"
        f"source: \"{url_original}\"\n"
        "tags:\n"
        "  - estudos\n"
        "  - resumo-youtube\n"
        "---\n\n"
    )
    
    nota_completa = frontmatter + conteudo_markdown
    
    nome_arquivo = limpar_nome_arquivo(titulo_video) + ".md"
    caminho_nota = vault_dir / nome_arquivo
    
    print(f"💾 Salvando nota no Obsidian Vault: {caminho_nota}...")
    with open(caminho_nota, "w", encoding="utf-8") as f:
        f.write(nota_completa)
        
    print(f"✨ Nota criada com sucesso!")
    return caminho_nota
