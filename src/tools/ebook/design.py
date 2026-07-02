import os
import sys
import re
import argparse
import textwrap
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

from src.core import config, database as db

# Garante a codificação UTF-8 no terminal Windows para evitar UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def sanitize_filename(name: str) -> str:
    """
    Remove caracteres inválidos para nomes de arquivos (especialmente no Windows).
    """
    # Remove caracteres inválidos: \ / : * ? " < > |
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    # Substitui espaços por sublinhados
    name = name.replace(" ", "_").lower()
    # Remove múltiplos sublinhados seguidos
    name = re.sub(r'_+', "_", name)
    return name

def highlight_code(code: str, lang: str = "python") -> str:
    """
    Aplica colorização sintática básica em código Python para exibição no terminal HTML.
    """
    # Escapa caracteres HTML
    code = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    if lang.lower() != "python":
        return code

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

def format_inline_styles(text: str) -> str:
    """
    Formata marcações inline do Markdown para HTML:
    - Código inline (backticks: `exemplo`)
    - Negrito (**texto**)
    - Itálico (*texto*)
    - Links ([texto](url))
    Protege o conteúdo dentro de backticks para evitar que caracteres de código sejam formatados.
    """
    inline_codes = []
    def save_inline_code(match):
        placeholder = f"___INLINE_CODE_{len(inline_codes)}___"
        # Escapa caracteres HTML dentro do código inline
        code_escaped = match.group(1).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        inline_codes.append(f'<code class="inline-code">{code_escaped}</code>')
        return placeholder

    # 1. Proteger e salvar código inline
    text = re.sub(r"`([^`\n]+)`", save_inline_code, text)

    # 2. Formatar outras marcações inline
    # Negrito
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
    # Itálico
    text = re.sub(r"\*(.*?)\*", r"<em>\1</em>", text)
    # Links
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2">\1</a>', text)

    # 3. Restaurar código inline
    for idx, code_html in enumerate(inline_codes):
        text = text.replace(f"___INLINE_CODE_{idx}___", code_html)

    return text

def md_to_html(md_text: str) -> str:
    """
    Converte uma string contendo Markdown em HTML estruturado.
    Implementa suporte a cabeçalhos (H1 a H5), parágrafos, negritos, itálicos,
    listas não ordenadas, alertas (GitHub style) e blocos de código com highlight.
    """
    # 1. Extrair e proteger blocos de código
    code_blocks = []
    def save_code_block(match):
        lang = match.group(1) or "python"
        code = match.group(2)
        # Remove a indentação comum do bloco de código (ex: quando aninhado em listas markdown)
        code = textwrap.dedent(code).strip()
        highlighted = highlight_code(code, lang)
        placeholder = f"___CODE_BLOCK_{len(code_blocks)}___"
        
        # Nome do arquivo ilustrativo
        filename = "main.py" if lang.lower() == "python" else f"script.{lang}"
        if lang.lower() == "bash":
            filename = "terminal"
            
        code_html = (
            f'<div class="terminal">'
            f'  <div class="terminal-header">'
            f'    <span class="terminal-file">{filename}</span>'
            f'    <span class="terminal-lang">{lang}</span>'
            f'  </div>'
            f'  <pre><code>{highlighted}</code></pre>'
            f'</div>'
        )
        code_blocks.append(code_html)
        return placeholder

    md_text = re.sub(r"^[ \t]*```(\w+)?\r?\n(.*?)\r?\n[ \t]*```", save_code_block, md_text, flags=re.MULTILINE | re.DOTALL)

    # 2. Extrair e proteger âncoras HTML (ex: <a id="id"></a>)
    anchors = []
    def save_anchor(match):
        placeholder = f"___ANCHOR_BLOCK_{len(anchors)}___"
        anchors.append(match.group(0))
        return placeholder
    
    md_text = re.sub(r'<a id="[^"]+"></a>', save_anchor, md_text)

    # 3. Processar blocos de citações e alertas
    lines = md_text.split("\n")
    processed_lines = []
    in_quote = False
    quote_lines = []

    def process_quote(q_lines):
        if not q_lines:
            return ""
        first = q_lines[0].strip()
        alert_type = None
        alert_title = ""
        
        if first.startswith("[!") and first.endswith("]"):
            type_str = first[2:-1].upper()
            if type_str in ("NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION"):
                alert_type = type_str.lower()
                alert_title = type_str.capitalize()
                # Traduções didáticas
                if alert_type == "note": alert_title = "Nota"
                elif alert_type == "tip": alert_title = "Dica"
                elif alert_type == "important": alert_title = "Importante"
                elif alert_type == "warning": alert_title = "Atenção"
                elif alert_type == "caution": alert_title = "Cuidado"
                q_lines = q_lines[1:]
                
        content = " ".join(q_lines).strip()
        content = format_inline_styles(content)
        
        if alert_type:
            return f'<div class="alert alert-{alert_type}"><strong>{alert_title}:</strong> {content}</div>'
        else:
            return f'<blockquote>{content}</blockquote>'

    for line in lines:
        line_stripped = line.rstrip()
        if line_stripped.startswith(">"):
            in_quote = True
            content_line = line_stripped[1:].strip()
            quote_lines.append(content_line)
        else:
            if in_quote:
                processed_lines.append(process_quote(quote_lines))
                quote_lines = []
                in_quote = False
            processed_lines.append(line_stripped)
            
    if in_quote:
        processed_lines.append(process_quote(quote_lines))

    # 4. Processar cabeçalhos, listas, links e parágrafos
    output = []
    in_list = False
    list_items = []

    for line in processed_lines:
        line_stripped = line.strip()
        if not line_stripped:
            if in_list:
                output.append("<ul>\n" + "\n".join(list_items) + "\n</ul>")
                list_items = []
                in_list = False
            output.append("")
            continue

        # Cabeçalhos H1 a H5 (avaliados em ordem decrescente de hashes para evitar conflitos)
        if line_stripped.startswith("##### "):
            if in_list:
                output.append("<ul>\n" + "\n".join(list_items) + "\n</ul>")
                list_items = []
                in_list = False
            title = format_inline_styles(line_stripped[6:])
            output.append(f"<h5>{title}</h5>")
            
        elif line_stripped.startswith("#### "):
            if in_list:
                output.append("<ul>\n" + "\n".join(list_items) + "\n</ul>")
                list_items = []
                in_list = False
            title = format_inline_styles(line_stripped[5:])
            output.append(f"<h4>{title}</h4>")
            
        elif line_stripped.startswith("### "):
            if in_list:
                output.append("<ul>\n" + "\n".join(list_items) + "\n</ul>")
                list_items = []
                in_list = False
            title = format_inline_styles(line_stripped[4:])
            output.append(f"<h3>{title}</h3>")
            
        elif line_stripped.startswith("## "):
            if in_list:
                output.append("<ul>\n" + "\n".join(list_items) + "\n</ul>")
                list_items = []
                in_list = False
            title = format_inline_styles(line_stripped[3:])
            output.append(f"<h2>{title}</h2>")
            
        elif line_stripped.startswith("# "):
            if in_list:
                output.append("<ul>\n" + "\n".join(list_items) + "\n</ul>")
                list_items = []
                in_list = False
            title = format_inline_styles(line_stripped[2:])
            output.append(f"<h1>{title}</h1>")

        # Listas não ordenadas
        elif line_stripped.startswith("- ") or line_stripped.startswith("* "):
            in_list = True
            item_text = format_inline_styles(line_stripped[2:])
            list_items.append(f"  <li>{item_text}</li>")

        # Linhas de quebra / Divisores
        elif line_stripped == "---":
            if in_list:
                output.append("<ul>\n" + "\n".join(list_items) + "\n</ul>")
                list_items = []
                in_list = False
            output.append("<hr>")

        # Placeholders
        elif line_stripped.startswith("___CODE_BLOCK_") or line_stripped.startswith("___ANCHOR_BLOCK_"):
            if in_list:
                output.append("<ul>\n" + "\n".join(list_items) + "\n</ul>")
                list_items = []
                in_list = False
            output.append(line_stripped)

        # Parágrafos padrões
        else:
            if in_list:
                output.append("<ul>\n" + "\n".join(list_items) + "\n</ul>")
                list_items = []
                in_list = False
            p_text = format_inline_styles(line_stripped)
            output.append(f"<p>{p_text}</p>")

    if in_list:
        output.append("<ul>\n" + "\n".join(list_items) + "\n</ul>")

    html_text = "\n".join(output)

    # 5. Restaurar blocos de código
    for idx, code_html in enumerate(code_blocks):
        html_text = html_text.replace(f"___CODE_BLOCK_{idx}___", code_html)

    # 6. Restaurar âncoras
    for idx, anchor_html in enumerate(anchors):
        html_text = html_text.replace(f"___ANCHOR_BLOCK_{idx}___", anchor_html)

    return html_text

def gerar_pdf_ebook(ebook_id: int) -> bool:
    """
    Carrega o e-book do banco SQLite, lê o Markdown 'ebook.md' correspondente
    no disco (permitindo renderizar versões editadas manualmente), compila o HTML
    e gera o arquivo PDF usando Playwright.
    """
    ebook = db.obter_ebook(ebook_id)
    if not ebook:
        print(f"❌ Erro: E-book com ID {ebook_id} não foi encontrado no banco de dados.", file=sys.stderr)
        return False

    output_dir = config.BASE_DIR / "data" / "generated" / "ebooks" / f"ebook_{ebook_id}"
    md_path = output_dir / "ebook.md"
    
    if not md_path.exists():
        print(f"❌ Erro: O arquivo Markdown '{md_path}' não foi encontrado.", file=sys.stderr)
        return False
        
    print(f"📚 Iniciando renderização do E-book ID {ebook_id}: '{ebook['title']}'...")
    
    # 1. Lê o Markdown (possivelmente editado pelo usuário)
    with open(md_path, "r", encoding="utf-8") as f:
        markdown_content = f.read()

    # 2. Converte Markdown para HTML
    parsed_html_content = md_to_html(markdown_content)

    # 3. Carrega o template Jinja2
    template_dir = Path(__file__).resolve().parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    try:
        template = env.get_template("ebook_template.html")
    except Exception as e:
        print(f"❌ Erro ao carregar o template do e-book: {e}", file=sys.stderr)
        return False

    # 4. Compila o template
    html_output = template.render(
        title=ebook["title"],
        subtitle=ebook["subtitle"],
        content=parsed_html_content
    )

    preview_html_path = output_dir / "preview.html"
    with open(preview_html_path, "w", encoding="utf-8") as f:
        f.write(html_output)
    print(f"🖥️ Visualização HTML do e-book gerada: {preview_html_path.relative_to(config.BASE_DIR)}")

    # 5. Renderização do PDF via Playwright
    pdf_filename = f"{sanitize_filename(ebook['title'])}.pdf"
    pdf_path = output_dir / pdf_filename
    
    print("📸 Iniciando o motor do Playwright em modo headless para gerar o PDF...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Carrega o HTML
            page.goto(preview_html_path.as_uri())
            
            # Aguarda renderização completa
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(1500)
            
            # Gera o PDF
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                display_header_footer=True,
                header_template=(
                    '<div style="font-size: 8px; font-family: \'Plus Jakarta Sans\', sans-serif; width: 100%; '
                    'display: flex; justify-content: space-between; padding-left: 25mm; padding-right: 25mm; '
                    'color: #94a3b8; border-bottom: 1px solid #e2e8f0; padding-bottom: 3px;">'
                    '<span>E-book Didático</span>'
                    '<span>Brunopythonista - Mentorias</span>'
                    '</div>'
                ),
                footer_template=(
                    '<div style="font-size: 8px; font-family: \'Plus Jakarta Sans\', sans-serif; width: 100%; '
                    'text-align: center; color: #94a3b8; padding-top: 3px;">'
                    '<span class="pageNumber"></span> / <span class="totalPages"></span>'
                    '</div>'
                )
            )
            
            browser.close()

        # Atualiza status no banco de dados SQLite
        db.atualizar_status_ebook(ebook_id, "Gerado")
        print(f"PDF gerado com sucesso em: {pdf_path.relative_to(config.BASE_DIR)}")
        
        # Abre a pasta no Windows se aplicável
        if os.name == "nt":
            try:
                os.startfile(pdf_path)
                print("📂 E-book aberto automaticamente.")
            except Exception as e:
                print(f"⚠️ Não foi possível abrir o arquivo automaticamente: {e}")
                
        return True
    except Exception as e:
        print(f"❌ Falha ao exportar PDF usando o Playwright: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="E-book PDF Renderer CLI")
    parser.add_argument("ebook_id", type=int, help="ID do e-book para renderizar")
    args = parser.parse_args()
    
    gerar_pdf_ebook(args.ebook_id)
