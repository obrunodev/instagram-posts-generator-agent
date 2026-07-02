import argparse
import sys
from google import genai
from google.genai import types
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal

from src.core import config, database as db

# Garante a codificação UTF-8 no terminal Windows para evitar UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

class PostInstagram(BaseModel):
    title: str = Field(
        ...,
        description="Título interno ou técnico curto do post (ex: 'Prefetch Related no Django' ou 'Injeção de Dependência no FastAPI')."
    )
    carousel_cards: List[str] = Field(
        ...,
        description="Textos que irão em cada card do carrossel (de 5 até 15 cards). Cada item representa um slide/card. O primeiro slide deve ser um hook irresistível. O último slide deve conter a CTA para curtir, comentar, compartilhar ou seguir o perfil @brunopythonista."
    )
    caption: str = Field(
        ...,
        description="Legenda altamente engajadora para o feed. Deve conter introdução cativante, desenvolvimento sucinto, CTA clara e exatamente 5 hashtags estratégicas."
    )
    theme: Literal['blue', 'green', 'black'] = Field(
        ...,
        description="O tema visual/modelo de cores do post. Escolha 'green' para Django/FastAPI; 'blue' para Python/Pandas/Polars/libs genéricas; 'black' para assuntos genéricos/outros (ex: Git, Docker)."
    )

    @field_validator('carousel_cards')
    @classmethod
    def validate_carousel_cards(cls, v: List[str]) -> List[str]:
        if not (5 <= len(v) <= 20):
            raise ValueError("O carrossel precisa ter entre 5 e 20 cards.")
        return v

class SinglePostInstagram(BaseModel):
    title: str = Field(
        ...,
        description="Título interno ou técnico curto do post de imagem única (ex: 'Métodos de Inteiros no Python')."
    )
    card_content: str = Field(
        ...,
        description="Texto e bloco de código que irão no único slide do post. Deve conter um título em negrito no topo (ex: '**Métodos de Inteiros**'), seguido de uma introdução curta e um bloco de código Python formatado em ```python ... ```."
    )
    caption: str = Field(
        ...,
        description="Legenda altamente engajadora para o feed. Deve conter introdução cativante, desenvolvimento sucinto dos pontos do slide, CTA clara e exatamente 5 hashtags estratégicas."
    )
    theme: Literal['blue', 'green', 'black'] = Field(
        ...,
        description="O tema visual/modelo de cores do post. Escolha 'green' para Django/FastAPI; 'blue' para Python/Pandas/Polars/libs genéricas; 'black' para assuntos genéricos/outros."
    )

def gerar_post_ia(tema: str) -> PostInstagram:
    """
    Invoca o Gemini 2.5 Flash para gerar o post com base no tema e usando Structured Outputs.
    """
    # Valida se a chave de API está definida no ambiente
    config.validate_config()
    
    # Inicializa o cliente do SDK oficial google-genai
    client = genai.Client(api_key=config.GEMINI_API_KEY)

    system_instruction = (
        "Você é um Engenheiro de Software Sênior especialista em Python, Django, FastAPI e Engenharia de Dados, "
        "e atua como um criador de conteúdo viral de alta performance para o Instagram no perfil @brunopythonista.\n\n"
        "Seu papel é criar posts de carrossel educativos e cativantes baseados em um tema técnico fornecido.\n\n"
        "DIRETRIZES DO CONTEÚDO:\n"
        "1. Linguagem clara, moderna, técnica e direta ao ponto (estilo dev experiente que ensina de forma simples).\n"
        "2. Use emojis estrategicamente (sem exagerar) para facilitar a leitura rápida.\n"
        "3. Exemplos de código fornecidos nos cards devem ser extremamente concisos e caber em um slide (máximo 4-5 linhas de código).\n"
        "4. O público-alvo são desenvolvedores que buscam dominar boas práticas, hacks e arquitetura.\n"
        "5. IMPORTANTE: Use obrigatoriamente quebras de linha (\\n) para separar elementos de texto dentro de cada card (como o título do card, explicações secundárias, itens de lista e blocos de código). O código Python dentro dos blocos ```python ... ``` deve conter quebras de linha reais e recuos adequados (4 espaços) para cada instrução. Nunca retorne o código ou o texto de um card em uma única linha contínua.\n\n"
        "DIRETRIZES DA ESTRUTURA (Retorne EXATAMENTE os campos solicitados no schema):\n"
        "- title: Um título curto que represente o post de forma organizada.\n"
        "- carousel_cards (Dinâmico: de 5 até 15 cards dependendo da complexidade do tema):\n"
        "  * Avalie a complexidade do tema fornecido: se for simples ou direto, gere de 5 a 6 cards. Se for um guia aprofundado, arquitetura complexa ou tutorial passo a passo denso, expanda a explicação técnica gerando mais cards intermediários (entre 8 e 12 cards, com limite máximo de 15 cards).\n"
        "  * Card 1: Hook (Gancho) - Um título chamativo e um subtítulo instigante (use quebra de linha entre eles).\n"
        "  * Cards intermediários (do Card 2 até o penúltimo card): O núcleo técnico. Explicações curtas progressivas, conceitos chave ou códigos práticos ilustrativos (use quebras de linha para formatar).\n"
        "  * Card Final: Chamada para Ação (CTA) - Incentive o usuário a interagir, curtir, comentar sua opinião e seguir o perfil @brunopythonista (use quebras de linha).\n"
        "- caption:\n"
        "  * Legenda completa e formatada com quebras de linha para o feed do Instagram.\n"
        "  * Comece com um gancho em texto.\n"
        "  * Explique resumidamente o aprendizado.\n"
        "  * Termine com CTA e obrigatoriamente exatamente 5 hashtags relevantes para o nicho (ex: #python #django #fastapi #backend #brunopythonista).\n"
        "- theme: O tema de cores do post:\n"
        "  * 'green' se o assunto for FastAPI ou Django.\n"
        "  * 'blue' se o assunto for Python em geral, Pandas, Polars ou outras bibliotecas/packages.\n"
        "  * 'black' se o assunto for genérico ou outras ferramentas (ex: Git, Docker)."
    )

    prompt = f"Crie um post completo para o Instagram sobre o seguinte tema técnico: '{tema}'"

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=PostInstagram,
                temperature=0.7,
            ),
        )
        return response.parsed
    except Exception as e:
        print(f"Erro ao gerar conteúdo na API do Gemini: {e}", file=sys.stderr)
        raise

def cmd_gerar(tema: str):
    """Gera o post, exibe na tela e salva no banco de dados SQLite local."""
    print(f"🤖 Solicitando ao Gemini 2.5 Flash a geração do post sobre: '{tema}'...")
    try:
        post = gerar_post_ia(tema)
        print("\n✨ Conteúdo gerado com sucesso pelo Gemini!\n")
        
        print("=" * 60)
        print(f"TÍTULO: {post.title}")
        print("=" * 60)
        
        print("\n--- SLIDES DO CARROSSEL ---")
        for idx, card in enumerate(post.carousel_cards, 1):
            print(f"[CARD {idx}]")
            print(card)
            print("-" * 40)
            
        print("\n--- LEGENDA DO POST ---")
        print(post.caption)
        print("=" * 60)
        
        # Salva no banco de dados SQLite local
        post_id = db.salvar_post(
            tema=tema,
            title=post.title,
            carousel_cards=post.carousel_cards,
            caption=post.caption,
            theme=post.theme
        )
        print(f"\n💾 Post salvo com sucesso no banco de dados local com ID: {post_id} (Status: Rascunho)")
        
    except Exception as e:
        print(f"❌ Falha ao gerar e salvar o post: {e}", file=sys.stderr)
        sys.exit(1)

def gerar_post_unico_ia(tema: str) -> SinglePostInstagram:
    """
    Invoca o Gemini 2.5 Flash para gerar um post de slide único (imagem única) com base no tema e usando Structured Outputs.
    """
    config.validate_config()
    client = genai.Client(api_key=config.GEMINI_API_KEY)

    system_instruction = (
        "Você é um Engenheiro de Software Sênior especialista em Python, Django, FastAPI e Engenharia de Dados, "
        "e atua como um criador de conteúdo viral de alta performance para o Instagram no perfil @brunopythonista.\n\n"
        "Seu papel é criar um post de slide/imagem única (formato Reels/Feed estático rápido) baseado em um tema técnico fornecido.\n\n"
        "DIRETRIZES DO CONTEÚDO:\n"
        "1. Linguagem clara, moderna, técnica, séria e direta ao ponto.\n"
        "2. O slide único deve conter um título em negrito no topo (ex: '**Título do Post**'), uma explicação curta e um bloco de código Python elegante, limpo e didático (máximo 8-10 linhas de código no total).\n"
        "3. Não adicione hooks infantis ou frases do tipo 'Sua chance de ser o Bruno Pythonista'. Mantenha o tom profissional.\n"
        "4. IMPORTANTE: Use quebras de linha (\\n) para estruturar o texto do slide.\n\n"
        "DIRETRIZES DA ESTRUTURA:\n"
        "- title: Um título curto que represente o post de forma organizada.\n"
        "- card_content: O texto completo do slide único, contendo obrigatoriamente o título em negrito, breve introdução e o código em ```python ... ```.\n"
        "- caption: Legenda completa e formatada com quebras de linha para o feed, introdução, explicação curta, CTA e exatamente 5 hashtags estratégicas.\n"
        "- theme: O tema de cores do post ('green', 'blue' ou 'black')."
    )

    prompt = f"Crie um post de slide único para o Instagram sobre o seguinte tema técnico: '{tema}'"

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=SinglePostInstagram,
                temperature=0.7,
            ),
        )
        return response.parsed
    except Exception as e:
        print(f"Erro ao gerar conteúdo na API do Gemini: {e}", file=sys.stderr)
        raise

def cmd_gerar_single(tema: str):
    """Gera um post de slide único, exibe na tela e salva no banco de dados SQLite local."""
    print(f"🤖 Solicitando ao Gemini 2.5 Flash a geração de post único sobre: '{tema}'...")
    try:
        post = gerar_post_unico_ia(tema)
        print("\n✨ Conteúdo de slide único gerado com sucesso pelo Gemini!\n")
        
        print("=" * 60)
        print(f"TÍTULO: {post.title}")
        print("=" * 60)
        
        print("\n--- SLIDE ÚNICO ---")
        print(post.card_content)
        print("-" * 40)
            
        print("\n--- LEGENDA DO POST ---")
        print(post.caption)
        print("=" * 60)
        
        # Salva no banco de dados SQLite local (convertendo card_content em uma lista de tamanho 1)
        post_id = db.salvar_post(
            tema=tema,
            title=post.title,
            carousel_cards=[post.card_content],
            caption=post.caption,
            theme=post.theme
        )
        print(f"\n💾 Post único salvo com sucesso no banco de dados local com ID: {post_id} (Status: Rascunho)")
        
    except Exception as e:
        print(f"❌ Falha ao gerar e salvar o post único: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_listar():
    """Lista todos os posts gerados e salvos no banco SQLite."""
    posts = db.listar_posts()
    if not posts:
        print("Nenhum post encontrado no banco de dados local.")
        return
        
    print(f"{'ID':<4} | {'STATUS':<18} | {'TÍTULO':<35} | {'DATA DE CRIAÇÃO'}")
    print("-" * 85)
    for p in posts:
        title_truncated = p['title'][:32] + "..." if len(p['title']) > 32 else p['title']
        print(f"{p['id']:<4} | {p['status']:<18} | {title_truncated:<35} | {p['created_at']}")

def cmd_atualizar_status(post_id: int, novo_status: str):
    """Atualiza o status de um post no banco de dados."""
    try:
        updated = db.atualizar_status(post_id, novo_status)
        if updated:
            print(f"✅ Status do post ID {post_id} atualizado com sucesso para: '{novo_status}'")
        else:
            print(f"❌ Post com ID {post_id} não foi encontrado.", file=sys.stderr)
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)

if __name__ == "__main__":
    # Mantém compatibilidade caso o script seja executado de forma direta
    parser = argparse.ArgumentParser(description="Instagram Content Generator CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("tema", type=str, nargs="?", help="Tema técnico")
    group.add_argument("-l", "--list", action="store_true")
    group.add_argument("-u", "--update-status", nargs=2, metavar=("ID", "STATUS"))
    
    args = parser.parse_args()
    if args.list:
        cmd_listar()
    elif args.update_status:
        try:
            pid = int(args.update_status[0])
            status = args.update_status[1]
            cmd_atualizar_status(pid, status)
        except ValueError:
            print("❌ O ID do post deve ser um número inteiro.", file=sys.stderr)
            sys.exit(1)
    elif args.tema:
        cmd_gerar(args.tema)
