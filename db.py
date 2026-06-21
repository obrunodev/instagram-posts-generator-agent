import sqlite3
import json
from typing import List, Dict, Any
import config

def get_connection():
    """Retorna uma conexão ativa com o banco de dados SQLite."""
    return sqlite3.connect(config.DB_NAME)

def init_db():
    """Cria a tabela de posts no banco de dados se ela não existir."""
    query = """
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
    with get_connection() as conn:
        conn.execute(query)
        conn.commit()

def salvar_post(tema: str, title: str, carousel_cards: List[str], caption: str) -> int:
    """
    Salva um novo post no banco de dados local com o status padrão 'Rascunho'.
    Retorna o ID do post criado.
    """
    init_db()
    query = """
    INSERT INTO posts (tema, title, carousel_cards, caption, status)
    VALUES (?, ?, ?, ?, 'Rascunho');
    """
    cards_json = json.dumps(carousel_cards, ensure_ascii=False)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (tema, title, cards_json, caption))
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
    SELECT id, tema, title, carousel_cards, caption, status, created_at 
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
                "status": row["status"],
                "created_at": row["created_at"]
            })
    return posts
