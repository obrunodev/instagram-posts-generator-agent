import argparse
import sys
import json
from pathlib import Path
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List

from src.core import config, database as db

# Garante a codificação UTF-8 no terminal Windows para evitar UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

class Chapter(BaseModel):
    title: str = Field(..., description="Título curto, direto e puramente técnico do capítulo, sem subtítulos ou floreios (ex: 'Introdução aos Decoradores', 'Decoradores com Argumentos')")
    content: str = Field(..., description="Conteúdo pedagógico aprofundado do capítulo em formato Markdown. Use parágrafos claros, subseções secundárias se necessário com ###, listas com marcadores e blocos de código com quebras de linha normais. Não use saudações, introduções emotivas ou parágrafos de transição enfeitados. Vá direto à explicação técnica.")
    summary_points: List[str] = Field(..., description="Lista de 3 a 5 pontos-chave estritamente técnicos para memorizar neste capítulo")

class EbookSchema(BaseModel):
    title: str = Field(..., description="Título principal curto, direto e técnico do e-book (ex: 'Git para Desenvolvimento de Software')")
    subtitle: str = Field(..., description="Subtítulo descritivo simples indicando o escopo da aula, sem termos de venda ou adjetivos dramáticos (ex: 'Fluxo de trabalho local, ramificação, stash e resolução de conflitos')")
    chapters: List[Chapter] = Field(..., description="Lista de 3 a 5 capítulos cobrindo o tema de forma progressiva e didática")
    practical_exercise_title: str = Field(..., description="Título curto do exercício prático/desafio final")
    practical_exercise: str = Field(..., description="Um desafio prático detalhado simulando cenários reais de mercado e de nível profissional relacionado ao tema do e-book. Deve conter: (1) O Cenário do Problema, (2) Instruções de Execução Passo a Passo e (3) Gabarito/Resolução sugerida com código ou comandos comentados de forma extremamente direta e sem floreios.")

def gerar_ebook_ia(tema: str) -> EbookSchema:
    """
    Invoca o Gemini 2.5 Flash para gerar a estrutura completa do e-book
    usando Structured Outputs.
    """
    config.validate_config()
    client = genai.Client(api_key=config.GEMINI_API_KEY)

    system_instruction = (
        "Você é um Engenheiro de Software Sênior e Mentor de Programação especializado em Python, Django, FastAPI, Git, Docker e Engenharia de Dados.\n"
        "Seu papel é criar e-books didáticos técnicos, profundos, claros e minimalistas sobre o tema fornecido.\n\n"
        "DIRETRIZES DE TONE OF VOICE (CRÍTICO - SEJA EXTREMAMENTE DIRETO):\n"
        "1. Tom extremamente seco, estritamente objetivo, direto ao ponto e focado 100% na explicação técnica.\n"
        "2. NUNCA use saudações entusiasmadas, emotivas ou conversacionais (ex: NÃO use 'Olá, futuro mestre', 'Seja bem-vindo', 'Olá, dev!', 'Neste capítulo vamos aprender...', 'Prepare-se para...'). Comece cada capítulo diretamente com a definição do conceito.\n"
        "3. NUNCA use floreios literários, metáforas dramáticas, adjetivos exagerados ou jargão de marketing (ex: evite expressões como 'com maestria', 'desvendando o poder', 'o coração de', 'segredos revelados', 'excelência', 'mestre', 'mágico', 'essencial para o sucesso').\n"
        "4. NUNCA use títulos ou subtítulos longos ou com frases de efeito após dois pontos (ex: NÃO use 'Fundamentos do Git: O Coração do Controle de Versão' ou 'Git do Zero ao Profissional: Domine com Maestria'). Use apenas títulos simples e diretos como 'Fundamentos do Git' ou 'Git para Desenvolvimento de Software'.\n"
        "5. Explique os conceitos e vá direto ao código/prática de forma profissional e concisa, similar ao estilo de uma documentação técnica oficial (como docs.python.org ou git-scm.com).\n"
        "6. Evite o uso desnecessário de pontos de exclamação (!).\n\n"
        "DIRETRIZES DE CONTEÚDO E ESTRUTURA:\n"
        "- title: Título curto, técnico e direto.\n"
        "- subtitle: Subtítulo descritivo simples indicando o escopo (sem palavras vagas ou promessas exageradas).\n"
        "- chapters: Lista de 3 a 5 capítulos. Cada capítulo deve conter explicações profundas porém secas e objetivas, com código realista bem estruturado em ```python ... ``` ou na linguagem correspondente, e finalizar com pontos chave diretos.\n"
        "- practical_exercise_title: Título curto do desafio.\n"
        "- practical_exercise: Desafio prático focado em resolver problemas reais de mercado, com instruções passo a passo claras e a resolução recomendada comentada de forma concisa."
    )

    prompt = f"Gere um e-book completo e aprofundado para mentoria sobre o seguinte tema técnico: '{tema}'"

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=EbookSchema,
                temperature=0.7,
            ),
        )
        return response.parsed
    except Exception as e:
        print(f"Erro ao gerar conteúdo na API do Gemini: {e}", file=sys.stderr)
        raise

def compilar_markdown(ebook: EbookSchema) -> str:
    """
    Agrupa o conteúdo estruturado do Pydantic em uma string Markdown unificada.
    """
    md = []
    md.append(f"# {ebook.title}")
    md.append(f"### {ebook.subtitle}")
    md.append("\n---\n")
    
    # Adicionar Sumário
    md.append("## Sumário")
    for idx, chap in enumerate(ebook.chapters, 1):
        # Cria âncora simples
        anchor = chap.title.lower().replace(" ", "-").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ç", "c").replace("ã", "a").replace("õ", "o")
        # Remove caracteres especiais para o link do markdown
        anchor = "".join([c for c in anchor if c.isalnum() or c == "-"])
        md.append(f"{idx}. [{chap.title}](#{anchor})")
    
    exercise_anchor = ebook.practical_exercise_title.lower().replace(" ", "-").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ç", "c").replace("ã", "a").replace("õ", "o")
    exercise_anchor = "".join([c for c in exercise_anchor if c.isalnum() or c == "-"])
    ex_title = ebook.practical_exercise_title
    if ex_title.lower().startswith("desafio prático") or ex_title.lower().startswith("desafio pratico"):
        md.append(f"*. [{ex_title}](#{exercise_anchor})")
    else:
        md.append(f"*. [Desafio Prático: {ex_title}](#{exercise_anchor})")
    
    md.append("\n---\n")
    
    # Adicionar Capítulos
    for idx, chap in enumerate(ebook.chapters, 1):
        anchor = chap.title.lower().replace(" ", "-").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ç", "c").replace("ã", "a").replace("õ", "o")
        anchor = "".join([c for c in anchor if c.isalnum() or c == "-"])
        
        md.append(f'<a id="{anchor}"></a>')
        # Evita duplicar prefixos do tipo 'Capítulo X'
        title_clean = chap.title
        if title_clean.lower().startswith("capítulo") or title_clean.lower().startswith("capitulo"):
            md.append(f"## {title_clean}")
        else:
            md.append(f"## Capítulo {idx}: {title_clean}")
        md.append(f"\n{chap.content.strip()}\n")
        
        if chap.summary_points:
            md.append("### 💡 Conceitos Chave")
            for pt in chap.summary_points:
                md.append(f"- {pt}")
        md.append("\n---\n")
        
    # Adicionar Exercício Prático
    exercise_anchor = ebook.practical_exercise_title.lower().replace(" ", "-").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ç", "c").replace("ã", "a").replace("õ", "o")
    exercise_anchor = "".join([c for c in exercise_anchor if c.isalnum() or c == "-"])
    
    md.append(f'<a id="{exercise_anchor}"></a>')
    # Evita duplicar prefixo do tipo 'Desafio Prático'
    ex_title = ebook.practical_exercise_title
    if ex_title.lower().startswith("desafio prático") or ex_title.lower().startswith("desafio pratico"):
        md.append(f"## {ex_title}")
    else:
        md.append(f"## Desafio Prático: {ex_title}")
    md.append(f"\n{ebook.practical_exercise.strip()}")
    
    return "\n".join(md)

def cmd_gerar(tema: str):
    """Gera o e-book, salva os arquivos locais e persiste no banco de dados SQLite."""
    print(f"🤖 Solicitando ao Gemini 2.5 Flash a geração do e-book sobre: '{tema}'...")
    try:
        ebook_data = gerar_ebook_ia(tema)
        print("\n✨ Conteúdo do e-book gerado com sucesso pelo Gemini!\n")
        
        print("=" * 60)
        print(f"TÍTULO: {ebook_data.title}")
        print(f"SUBTÍTULO: {ebook_data.subtitle}")
        print("=" * 60)
        
        # Salva no SQLite (salva o JSON estruturado)
        content_json_str = json.dumps(ebook_data.model_dump(), ensure_ascii=False)
        ebook_id = db.salvar_ebook(
            tema=tema,
            title=ebook_data.title,
            subtitle=ebook_data.subtitle,
            content_json=content_json_str
        )
        print(f"💾 E-book catalogado no SQLite com ID: {ebook_id} (Status: Rascunho)")
        
        # Cria diretório específico para o e-book
        output_dir = config.BASE_DIR / "data" / "generated" / "ebooks" / f"ebook_{ebook_id}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Salva JSON estruturado
        json_path = output_dir / "ebook.json"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(content_json_str)
            
        # Compila e salva o Markdown unificado
        markdown_content = compilar_markdown(ebook_data)
        md_path = output_dir / "ebook.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
            
        print(f"📄 Arquivo JSON salvo em: {json_path.relative_to(config.BASE_DIR)}")
        print(f"📝 Arquivo Markdown editável gerado em: {md_path.relative_to(config.BASE_DIR)}")
        print(f"\n💡 Dica: Você pode abrir e editar o Markdown '{md_path.name}' para customizar o conteúdo antes de gerar o PDF.")
        print(f"👉 Para gerar o PDF final, execute: uv run python -m src.cli ebook render {ebook_id}")
        
    except Exception as e:
        print(f"❌ Falha ao gerar e salvar o e-book: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_listar():
    """Lista todos os e-books registrados no banco SQLite local."""
    ebooks = db.listar_ebooks()
    if not ebooks:
        print("Nenhum e-book encontrado no banco de dados local.")
        return
        
    print(f"{'ID':<4} | {'STATUS':<10} | {'TÍTULO':<35} | {'DATA DE CRIAÇÃO'}")
    print("-" * 80)
    for eb in ebooks:
        title_truncated = eb['title'][:32] + "..." if len(eb['title']) > 32 else eb['title']
        print(f"{eb['id']:<4} | {eb['status']:<10} | {title_truncated:<35} | {eb['created_at']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="E-book Content Generator CLI")
    parser.add_argument("tema", type=str, nargs="?", help="Tema do e-book")
    parser.add_argument("-l", "--list", action="store_true", help="Listar e-books")
    args = parser.parse_args()
    
    if args.list:
        cmd_listar()
    elif args.tema:
        cmd_gerar(args.tema)
