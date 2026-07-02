import sys
import argparse
from src.core import database as db

def main():
    parser = argparse.ArgumentParser(
        description="Agente Brunopythonista - Painel CLI Central de Agentes e Ferramentas"
    )
    
    subparsers = parser.add_subparsers(dest="tool", help="Ferramenta a ser executada")
    
    # -------------------------------------------------------------
    # SUBPARSER: instagram
    # -------------------------------------------------------------
    instagram_parser = subparsers.add_parser("instagram", help="Agente de Geração e Design para Instagram")
    instagram_sub = instagram_parser.add_subparsers(dest="action", help="Ação a ser executada")
    
    # instagram generate
    gen_parser = instagram_sub.add_parser("generate", help="Gera um novo post de carrossel")
    gen_parser.add_argument("tema", type=str, help="Tema técnico do post")
    
    # instagram generate-single
    gen_single_parser = instagram_sub.add_parser("generate-single", help="Gera um novo post de imagem única")
    gen_single_parser.add_argument("tema", type=str, help="Tema técnico do post de slide único")
    
    # instagram design
    design_parser = instagram_sub.add_parser("design", help="Gera as imagens PNG dos slides de um post")
    design_parser.add_argument("post_id", type=int, nargs="?", help="ID do post (omita para renderizar o último)")
    
    # instagram list
    instagram_sub.add_parser("list", help="Lista os posts cadastrados no banco de dados local")
    
    # instagram update-status
    status_parser = instagram_sub.add_parser("update-status", help="Atualiza o status de um post específico")
    status_parser.add_argument("post_id", type=int, help="ID do post")
    status_parser.add_argument("status", type=str, choices=["Rascunho", "Pronto para Imagem", "Postado"], help="Novo status")

    # -------------------------------------------------------------
    # SUBPARSER: youtube (Youtube to Obsidian)
    # -------------------------------------------------------------
    youtube_parser = subparsers.add_parser("youtube", help="Transcritor de Vídeos e Integração Obsidian")
    youtube_sub = youtube_parser.add_subparsers(dest="action", help="Ação do Youtube to Obsidian")
    
    youtube_gen_parser = youtube_sub.add_parser("process", help="Baixa, transcreve e resume um vídeo do Youtube no Obsidian")
    youtube_gen_parser.add_argument("--url", type=str, required=True, help="URL do vídeo do Youtube")
    
    # -------------------------------------------------------------
    # SUBPARSER: ebook (E-book Generator)
    # -------------------------------------------------------------
    ebook_parser = subparsers.add_parser("ebook", help="Gerador de E-Books Didáticos (PDF)")
    ebook_sub = ebook_parser.add_subparsers(dest="action", help="Ação do E-book Generator")
    
    # ebook generate
    ebook_gen_parser = ebook_sub.add_parser("generate", help="Gera o conteúdo e o rascunho de um e-book")
    ebook_gen_parser.add_argument("tema", type=str, help="Tema técnico da aula")
    
    # ebook render
    ebook_render_parser = ebook_sub.add_parser("render", help="Gera o PDF final a partir do Markdown")
    ebook_render_parser.add_argument("ebook_id", type=int, help="ID do e-book para renderização")
    
    # ebook list
    ebook_sub.add_parser("list", help="Lista todos os e-books catalogados")
    
    args = parser.parse_args()
    
    if not args.tool:
        parser.print_help()
        sys.exit(0)
        
    if args.tool == "instagram":
        from src.tools.instagram import content, design
        
        if not args.action:
            instagram_parser.print_help()
            sys.exit(0)
            
        if args.action == "generate":
            content.cmd_gerar(args.tema)
        elif args.action == "generate-single":
            content.cmd_gerar_single(args.tema)
        elif args.action == "design":
            pid = args.post_id
            if not pid:
                posts = db.listar_posts()
                if not posts:
                    print("❌ Nenhum post foi encontrado no banco de dados local.", file=sys.stderr)
                    sys.exit(1)
                pid = posts[0]["id"]
            design.gerar_imagens_post(pid)
        elif args.action == "list":
            content.cmd_listar()
        elif args.action == "update-status":
            content.cmd_atualizar_status(args.post_id, args.status)
            
    elif args.tool == "youtube":
        from src.tools.youtube_to_obsidian import estudar_video
        
        if not args.action:
            youtube_parser.print_help()
            sys.exit(0)
            
        if args.action == "process":
            estudar_video.processar_video(args.url)
            
    elif args.tool == "ebook":
        from src.tools.ebook import content, design
        
        if not args.action:
            ebook_parser.print_help()
            sys.exit(0)
            
        if args.action == "generate":
            content.cmd_gerar(args.tema)
        elif args.action == "render":
            design.gerar_pdf_ebook(args.ebook_id)
        elif args.action == "list":
            content.cmd_listar()

if __name__ == "__main__":
    main()
