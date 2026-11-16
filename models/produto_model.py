"""Persistência de produtos e gatos."""
from models.database import get_connection


def _query(sql, params=()):
    conn = get_connection()
    try:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def listar_produtos(categoria=None):
    if categoria:
        return _query("SELECT * FROM produtos WHERE categoria = ? ORDER BY nome", (categoria,))
    return _query("SELECT * FROM produtos ORDER BY categoria, nome")


def buscar_produtos_por_ids(ids):
    ids = list(ids)
    if not ids:
        return []
    marcadores = ",".join("?" * len(ids))
    return _query(f"SELECT * FROM produtos WHERE id IN ({marcadores})", ids)


def listar_gatos():
    return _query("SELECT * FROM gatos ORDER BY nome")


def atualizar_status_gato(gato_id, status):
    conn = get_connection()
    try:
        cur = conn.execute("UPDATE gatos SET status_adocao = ? WHERE id = ?", (status, gato_id))
        return cur.rowcount > 0
    finally:
        conn.close()
