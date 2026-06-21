import argparse
import sys
import config
import db
from google import genai
from google.genai import types
from pydantic import BaseModel, Field, field_validator
from typing import List

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
        description="Textos que irão em cada card do carrossel (máximo de 5 cards). Cada item representa um slide/card. O primeiro slide deve ser um hook irresistível. O último slide deve conter a CTA para curtir, comentar, compartilhar ou seguir o perfil @djangiota."
    )
    caption: str = Field(
        ...,
        description="Legenda altamente engajadora para o feed. Deve conter introdução cativante, desenvolvimento sucinto e CTA clara + hashtags estratégicas."
    )

    @field_validator('carousel_cards')
    @classmethod
    def validate_carousel_cards(cls, v: List[str]) -> List[str]:
        if not (1 <= len(v) <= 5):
            raise ValueError("O carrossel precisa ter entre 1 e 5 cards.")
        return v

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
        "e atua como um criador de conteúdo viral de alta performance para o Instagram no perfil @djangiota.\n\n"
        "Seu papel é criar posts de carrossel educativos e cativantes baseados em um tema técnico fornecido.\n\n"
        "DIRETRIZES DO CONTEÚDO:\n"
        "1. Linguagem clara, moderna, técnica e direta ao ponto (estilo dev experiente que ensina de forma simples).\n"
        "2. Use emojis estrategicamente (sem exagerar) para facilitar a leitura rápida.\n"
        "3. Exemplos de código fornecidos nos cards devem ser extremamente concisos e caber em um slide (máximo 4-5 linhas de código).\n"
        "4. O público-alvo são desenvolvedores que buscam dominar boas práticas, hacks e arquitetura.\n"
        "5. IMPORTANTE: Use obrigatoriamente quebras de linha (\\n) para separar elementos de texto dentro de cada card (como o título do card, explicações secundárias, itens de lista e blocos de código). O código Python dentro dos blocos ```python ... ``` deve conter quebras de linha reais e recuos adequados (4 espaços) para cada instrução. Nunca retorne o código ou o texto de um card em uma única linha contínua.\n\n"
        "DIRETRIZES DA ESTRUTURA (Retorne EXATAMENTE os campos solicitados no schema):\n"
        "- title: Um título curto que represente o post de forma organizada.\n"
        "- carousel_cards (Máximo 5 cards):\n"
        "  * Card 1: Hook (Gancho) - Um título chamativo e um subtítulo instigante (use quebra de linha entre eles).\n"
        "  * Cards 2, 3 e 4: O núcleo técnico. Explicações curtas ou códigos práticos ilustrativos (use quebras de linha para formatar).\n"
        "  * Card 5: Chamada para Ação (CTA) - Incentive o usuário a interagir, curtir, comentar sua opinião e seguir o perfil @djangiota (use quebras de linha).\n"
        "- caption:\n"
        "  * Legenda completa e formatada com quebras de linha para o feed do Instagram.\n"
        "  * Comece com um gancho em texto.\n"
        "  * Explique resumidamente o aprendizado.\n"
        "  * Termine com CTA e hashtags relevantes para o nicho (ex: #python #django #fastapi #backend #dataengineering #djangiota)."
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
            caption=post.caption
        )
        print(f"\n💾 Post salvo com sucesso no banco de dados local com ID: {post_id} (Status: Rascunho)")
        
    except Exception as e:
        print(f"❌ Falha ao gerar e salvar o post: {e}", file=sys.stderr)
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

def main():
    parser = argparse.ArgumentParser(
        description="Agente CLI do Instagram @djangiota - Automação de Geração de Conteúdo"
    )
    
    # Define os argumentos CLI
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "tema", 
        type=str, 
        nargs="?",
        help="Tema técnico do post para geração (ex: 'Como funciona middleware no FastAPI')"
    )
    group.add_argument(
        "-l", "--list", 
        action="store_true", 
        help="Lista todos os posts salvos no banco de dados local"
    )
    group.add_argument(
        "-u", "--update-status",
        nargs=2,
        metavar=("ID", "STATUS"),
        help="Atualiza o status de um post. Exemplo: -u 1 'Pronto para Imagem' (Status válidos: 'Rascunho', 'Pronto para Imagem', 'Postado')"
    )

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
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
