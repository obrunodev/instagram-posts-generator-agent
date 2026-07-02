import sqlite3
import json
from typing import List, Dict, Any
from src.core import config

def get_connection():
    """Retorna uma conexão ativa com o banco de dados SQLite."""
    return sqlite3.connect(config.DB_NAME)

def init_db():
    """Cria as tabelas de posts e ebooks no banco de dados se não existirem."""
    query_posts = """
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tema TEXT NOT NULL,
        title TEXT NOT NULL,
        carousel_cards TEXT NOT NULL, -- Lista de strings serializada em JSON
        caption TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('Rascunho', 'Pronto para Imagem', 'Postado')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    query_ebooks = """
    CREATE TABLE IF NOT EXISTS ebooks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tema TEXT NOT NULL,
        title TEXT NOT NULL,
        subtitle TEXT NOT NULL,
        content_json TEXT NOT NULL, -- Dados completos do e-book serializados em JSON
        status TEXT NOT NULL CHECK(status IN ('Rascunho', 'Gerado', 'Finalizado')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    # Garante a criação do diretório pai do DB se ele não existir
    from pathlib import Path
    db_path = Path(config.DB_NAME)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        conn.execute(query_posts)
        # Migração: Adiciona a coluna 'theme' caso ela não exista em bases já criadas
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(posts)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'theme' not in columns:
            conn.execute("ALTER TABLE posts ADD COLUMN theme TEXT DEFAULT 'blue'")
        conn.execute(query_ebooks)
        conn.commit()

def salvar_post(tema: str, title: str, carousel_cards: List[str], caption: str, theme: str = 'blue') -> int:
    """
    Salva um novo post no banco de dados local com o status padrão 'Rascunho'.
    Retorna o ID do post criado.
    """
    init_db()
    query = """
    INSERT INTO posts (tema, title, carousel_cards, caption, theme, status)
    VALUES (?, ?, ?, ?, ?, 'Rascunho');
    """
    cards_json = json.dumps(carousel_cards, ensure_ascii=False)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (tema, title, cards_json, caption, theme))
        conn.commit()
        return cursor.lastrowid

def atualizar_status(post_id: int, novo_status: str) -> bool:
    """
    Atualiza o status de um post (Rascunho -> Pronto para Imagem -> Postado).
    Retorna True se o registro foi atualizado, False caso contrário.
    """
    init_db()
    if novo_status not in ('Rascunho', 'Pronto para Imagem', 'Postado'):
        raise ValueError("Status inválido. Deve ser 'Rascunho', 'Pronto para Imagem' ou 'Postado'.")

    query = "UPDATE posts SET status = ? WHERE id = ?;"
    with get_connection() as conn:
        cursor = conn.execute(query, (novo_status, post_id))
        conn.commit()
        return cursor.rowcount > 0

def listar_posts() -> List[Dict[str, Any]]:
    """
    Recupera e lista todos os posts ordenados por data de criação.
    """
    init_db()
    query = """
    SELECT id, tema, title, carousel_cards, caption, theme, status, created_at 
    FROM posts 
    ORDER BY created_at DESC;
    """
    posts = []
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query)
        for row in cursor.fetchall():
            posts.append({
                "id": row["id"],
                "tema": row["tema"],
                "title": row["title"],
                "carousel_cards": json.loads(row["carousel_cards"]),
                "caption": row["caption"],
                "theme": row["theme"] if row["theme"] else "blue",
                "status": row["status"],
                "created_at": row["created_at"]
            })
    return posts

def salvar_ebook(tema: str, title: str, subtitle: str, content_json: str) -> int:
    """
    Salva um novo e-book no banco de dados local com o status padrão 'Rascunho'.
    Retorna o ID do e-book criado.
    """
    init_db()
    query = """
    INSERT INTO ebooks (tema, title, subtitle, content_json, status)
    VALUES (?, ?, ?, ?, 'Rascunho');
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (tema, title, subtitle, content_json))
        conn.commit()
        return cursor.lastrowid

def atualizar_status_ebook(ebook_id: int, novo_status: str) -> bool:
    """
    Atualiza o status de um e-book.
    Retorna True se o registro foi atualizado, False caso contrário.
    """
    init_db()
    if novo_status not in ('Rascunho', 'Gerado', 'Finalizado'):
        raise ValueError("Status inválido. Deve ser 'Rascunho', 'Gerado' ou 'Finalizado'.")

    query = "UPDATE ebooks SET status = ? WHERE id = ?;"
    with get_connection() as conn:
        cursor = conn.execute(query, (novo_status, ebook_id))
        conn.commit()
        return cursor.rowcount > 0

def listar_ebooks() -> List[Dict[str, Any]]:
    """
    Recupera e lista todos os e-books ordenados por data de criação.
    """
    init_db()
    query = """
    SELECT id, tema, title, subtitle, content_json, status, created_at 
    FROM ebooks 
    ORDER BY created_at DESC;
    """
    ebooks = []
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query)
        for row in cursor.fetchall():
            ebooks.append({
                "id": row["id"],
                "tema": row["tema"],
                "title": row["title"],
                "subtitle": row["subtitle"],
                "content_json": row["content_json"],
                "status": row["status"],
                "created_at": row["created_at"]
            })
    return ebooks

def obter_ebook(ebook_id: int) -> Dict[str, Any]:
    """
    Busca um e-book específico pelo ID. Retorna None se não for encontrado.
    """
    init_db()
    query = """
    SELECT id, tema, title, subtitle, content_json, status, created_at 
    FROM ebooks 
    WHERE id = ?;
    """
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, (ebook_id,))
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "tema": row["tema"],
                "title": row["title"],
                "subtitle": row["subtitle"],
                "content_json": row["content_json"],
                "status": row["status"],
                "created_at": row["created_at"]
            }
    return None

