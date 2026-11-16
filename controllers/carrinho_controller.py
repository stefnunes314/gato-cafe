"""Gerencia o carrinho na sessão e os cálculos (US02).

A sessão guarda apenas {produto_id: quantidade}. Preços sempre vêm do banco.
"""
from models import produto_model

MODALIDADES = ("Consumo Local", "Delivery")
QTD_MAX_POR_ITEM = 20


def _carrinho(sessao):
    return sessao.setdefault("carrinho", {})


def _validar_produto(produto_id):
    if not produto_model.buscar_produtos_por_ids([produto_id]):
        raise ValueError("Produto não encontrado.")


def adicionar(sessao, produto_id):
    _validar_produto(produto_id)
    c = _carrinho(sessao)
    chave = str(produto_id)
    c[chave] = min(c.get(chave, 0) + 1, QTD_MAX_POR_ITEM)
    sessao.modified = True


def decrementar(sessao, produto_id):
    c = _carrinho(sessao)
    chave = str(produto_id)
    if chave in c:
        c[chave] -= 1
        if c[chave] <= 0:
            del c[chave]
    sessao.modified = True


def remover(sessao, produto_id):
    _carrinho(sessao).pop(str(produto_id), None)
    sessao.modified = True


def limpar(sessao):
    sessao["carrinho"] = {}
    sessao.modified = True


def definir_modalidade(sessao, modalidade):
    if modalidade not in MODALIDADES:
        raise ValueError("Modalidade inválida.")
    sessao["modalidade"] = modalidade


def resumo(sessao):
    """Retorna itens detalhados, subtotal e quantidade total (recalculado a cada chamada)."""
    c = _carrinho(sessao)
    produtos = {str(p["id"]): p for p in produto_model.buscar_produtos_por_ids(
        [int(k) for k in c])}
    itens = []
    for chave, qtd in c.items():
        p = produtos.get(chave)
        if p is None:
            continue
        itens.append({"produto_id": p["id"], "nome": p["nome"], "preco_unitario": p["preco"],
                      "quantidade": qtd, "subtotal": round(p["preco"] * qtd, 2)})
    return {
        "itens": itens,
        "subtotal": round(sum(i["subtotal"] for i in itens), 2),
        "quantidade": sum(i["quantidade"] for i in itens),
        "modalidade": sessao.get("modalidade", MODALIDADES[0]),
    }
