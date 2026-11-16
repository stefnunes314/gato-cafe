"""Transação de pedidos e itens_pedido."""
from models.database import get_connection


def criar_pedido(cliente_nome, telefone, modalidade, endereco, forma_pagamento, itens):
    """Grava cabeçalho e itens em uma única transação (RN04).

    itens: lista de dicts com produto_id, quantidade, preco_unitario.
    Retorna o id do pedido. Em qualquer falha, nada é gravado.
    """
    if not itens:
        raise ValueError("O pedido precisa ter ao menos 1 item.")
    total = round(sum(i["quantidade"] * i["preco_unitario"] for i in itens), 2)
    conn = get_connection()
    try:
        conn.execute("BEGIN")
        try:
            cur = conn.execute(
                "INSERT INTO pedidos (cliente_nome, telefone, modalidade, endereco, "
                "forma_pagamento, total) VALUES (?,?,?,?,?,?)",
                (cliente_nome, telefone, modalidade, endereco, forma_pagamento, total),
            )
            pedido_id = cur.lastrowid
            conn.executemany(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
                "VALUES (?,?,?,?)",
                [(pedido_id, i["produto_id"], i["quantidade"], i["preco_unitario"]) for i in itens],
            )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        return pedido_id
    finally:
        conn.close()


def listar_pedidos():
    conn = get_connection()
    try:
        pedidos = [dict(r) for r in conn.execute(
            "SELECT * FROM pedidos ORDER BY id DESC LIMIT 100").fetchall()]
        for p in pedidos:
            p["itens"] = [dict(r) for r in conn.execute(
                "SELECT i.quantidade, i.preco_unitario, pr.nome FROM itens_pedido i "
                "JOIN produtos pr ON pr.id = i.produto_id WHERE i.pedido_id = ?",
                (p["id"],)).fetchall()]
        return pedidos
    finally:
        conn.close()
