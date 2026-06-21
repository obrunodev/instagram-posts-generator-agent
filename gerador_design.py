import os
import sys
import re
import argparse
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

import config
import db

# Garante a codificação UTF-8 no terminal Windows para evitar UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def highlight_code(code: str) -> str:
    """
    Aplica colorização sintática básica em código Python para exibição no terminal HTML.
    Segrega strings e comentários com placeholders para evitar conflitos com marcações HTML.
    """
    # Escapa caracteres HTML
    code = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    placeholders = {}
    counter = 0

    # 1. Comentários (linha inteira ou final de linha)
    def comment_repl(match):
        nonlocal counter
        ph = f"___COMMENT_PH_{counter}___"
        placeholders[ph] = f'<span class="code-comment">{match.group(0)}</span>'
        counter += 1
        return ph
    code = re.sub(r"(#.*)$", comment_repl, code, flags=re.MULTILINE)

    # 2. Strings
    def string_repl(match):
        nonlocal counter
        ph = f"___STRING_PH_{counter}___"
        placeholders[ph] = f'<span class="code-string">{match.group(0)}</span>'
        counter += 1
        return ph
    code = re.sub(r'("(.*?)"|\'(.*?)\')', string_repl, code)

    # 3. Palavras-chave
    keywords = r"\b(def|class|import|from|return|if|elif|else|try|except|finally|for|while|in|is|not|and|or|as|with|lambda|yield|pass|raise|async|await)\b"
    code = re.sub(keywords, r'<span class="code-keyword">\1</span>', code)

    # 4. Decoradores
    code = re.sub(r"(@\w+(\.\w+)*)", r'<span class="code-decorator">\1</span>', code)

    # 5. Built-ins comuns
    builtins = r"\b(print|len|range|str|int|float|dict|list|set|tuple|abs|bool|enumerate|zip|isinstance|any|all)\b"
    code = re.sub(builtins, r'<span class="code-builtin">\1</span>', code)

    # Restaurar strings e comentários salvos
    for ph, val in placeholders.items():
        code = code.replace(ph, val)

    return code

def parse_card_text(text: str) -> dict:
    """
    Parseia o texto cru de um card para HTML:
    - Extrai blocos de código python, aplicando colorização.
    - Converte marcações de negrito (**texto**) para <strong>.
    - Identifica e monta listas não ordenadas (linhas que começam com - ou *).
    """
    # 1. Detectar bloco de código Python
    code_match = re.search(r"```python\s*(.*?)\s*```", text, re.DOTALL)
    code_html = ""
    if code_match:
        raw_code = code_match.group(1).strip()
        highlighted = highlight_code(raw_code)
        code_html = (
            f'<div class="terminal">'
            f'  <div class="terminal-header">'
            f'    <span class="terminal-file">main.py</span>'
            f'    <span class="terminal-lang">python</span>'
            f'  </div>'
            f'  <pre><code>{highlighted}</code></pre>'
            f'</div>'
        )
        # Remove o bloco de código do texto cru para processar o texto separadamente
        text = text.replace(code_match.group(0), "").strip()

    # 2. Processar texto restante linha por linha
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    card_title = None
    processed_paragraphs = []
    
    # Se a primeira linha for curta ou estiver em negrito, tratamos como título de slide
    if lines:
        first_line = lines[0]
        if first_line.startswith("**") and first_line.endswith("**"):
            card_title = first_line.replace("**", "")
            lines = lines[1:]
        elif len(first_line) < 45 and not first_line.startswith("-") and not first_line.startswith("*"):
            card_title = first_line
            lines = lines[1:]

    in_list = False
    list_items = []
    
    for line in lines:
        if line.startswith("- ") or line.startswith("* "):
            in_list = True
            item_text = line[2:]
            item_text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", item_text)
            list_items.append(f"<li>{item_text}</li>")
        else:
            if in_list:
                processed_paragraphs.append("<ul>" + "".join(list_items) + "</ul>")
                list_items = []
                in_list = False
            
            p_text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", line)
            processed_paragraphs.append(f"<p>{p_text}</p>")
            
    if in_list:
        processed_paragraphs.append("<ul>" + "".join(list_items) + "</ul>")

    html_content = "".join(processed_paragraphs)
    
    # Adiciona o terminal de código formatado ao fim do conteúdo do card
    if code_html:
        html_content += code_html

    return {
        "html_content": html_content,
        "card_title": card_title
    }

def gerar_imagens_post(post_id: int) -> bool:
    # 1. Recupera o post do banco local
    posts = db.listar_posts()
    post = next((p for p in posts if p["id"] == post_id), None)
    if not post:
        print(f"❌ Erro: Post com ID {post_id} não foi encontrado no banco de dados.", file=sys.stderr)
        return False
        
    print(f"🎨 Iniciando geração visual para o post ID {post_id}: '{post['title']}'...")
    
    # 2. Processa cada card de texto bruto para HTML estruturado
    processed_cards = []
    for card_text in post["carousel_cards"]:
        processed = parse_card_text(card_text)
        processed_cards.append(processed)
        
    total_cards = len(processed_cards)
    
    # 3. Compila o template com Jinja2
    template_dir = config.BASE_DIR / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    try:
        template = env.get_template("card_template.html")
    except Exception as e:
        print(f"❌ Erro ao carregar o template html: {e}", file=sys.stderr)
        return False
        
    html_output = template.render(
        post_title=post["title"],
        cards=processed_cards,
        total_cards=total_cards
    )
    
    # Grava um HTML temporário para navegação do Playwright
    temp_html_path = config.BASE_DIR / f"temp_post_{post_id}.html"
    with open(temp_html_path, "w", encoding="utf-8") as f:
        f.write(html_output)
        
    # 4. Prepara o diretório de destino das imagens
    output_dir = config.BASE_DIR / "posts_gerados" / f"post_{post_id}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📸 Iniciando o motor do Playwright em modo headless...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Carrega o arquivo HTML local
            page.goto(temp_html_path.as_uri())
            
            # Aguarda as fontes carregarem corretamente
            page.wait_for_timeout(1000)
            
            # Tira capturas de tela dos elementos do card (1080x1350px)
            for idx in range(1, total_cards + 1):
                card_selector = f"#card-{idx}"
                card_element = page.locator(card_selector)
                
                if card_element.count() > 0:
                    output_file = output_dir / f"card_{idx}.png"
                    print(f"📸 Capturando card {idx}/{total_cards} -> {output_file.name}...")
                    
                    # Tira captura de tela com fundo transparente omitido se necessário
                    card_element.screenshot(
                        path=str(output_file),
                        type="png",
                        omit_background=True
                    )
                else:
                    print(f"⚠️ Elemento {card_selector} não localizado no HTML.", file=sys.stderr)
                    
            browser.close()
            
        # Atualiza o status do post no SQLite
        db.atualizar_status(post_id, "Pronto para Imagem")
        print(f"\n✅ Imagens geradas com sucesso no diretório: {output_dir.relative_to(config.BASE_DIR)}")
        print(f"🗃️ Status do post ID {post_id} atualizado para 'Pronto para Imagem'.")
        return True
        
    except Exception as e:
        print(f"❌ Falha ao processar capturas no Playwright: {e}", file=sys.stderr)
        return False
    finally:
        # Remove arquivo temporário de HTML
        if temp_html_path.exists():
            temp_html_path.unlink()

def main():
    parser = argparse.ArgumentParser(
        description="Agente CLI do Instagram @djangiota - Motor de Design (HTML para PNG)"
    )
    parser.add_argument(
        "post_id",
        type=int,
        nargs="?",
        help="ID do post a ser renderizado. Se omitido, renderiza o último post cadastrado."
    )
    
    args = parser.parse_args()
    
    post_id = args.post_id
    if not post_id:
        posts = db.listar_posts()
        if not posts:
            print("❌ Nenhum post foi encontrado no banco de dados local.", file=sys.stderr)
            sys.exit(1)
        post_id = posts[0]["id"]
        
    gerar_imagens_post(post_id)

if __name__ == "__main__":
    main()
