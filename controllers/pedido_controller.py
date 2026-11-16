"""Valida checkout e fecha pedido (US03, RN04)."""
import re

from controllers import carrinho_controller
from models import pedido_model

FORMAS_PAGAMENTO = ("Pix", "Cartão de Crédito")


def validar_contato(nome, telefone):
    nome = (nome or "").strip()
    telefone = (telefone or "").strip()
    if not nome:
        raise ValueError("Informe o seu nome.")
    if len(re.sub(r"\D", "", telefone)) < 10:
        raise ValueError("Informe um telefone válido com DDD.")
    return nome, telefone


def finalizar(sessao, nome, telefone, pagamento, endereco=None):
    """Registra o pedido, limpa o carrinho e retorna (pedido_id, total)."""
    nome, telefone = validar_contato(nome, telefone)
    if pagamento not in FORMAS_PAGAMENTO:
        raise ValueError("Escolha Pix ou Cartão de Crédito.")

    resumo = carrinho_controller.resumo(sessao)
    if not resumo["itens"]:
        raise ValueError("Seu carrinho está vazio.")

    modalidade = resumo["modalidade"]
    endereco = (endereco or "").strip() or None
    if modalidade == "Delivery" and not endereco:
        raise ValueError("Informe o endereço para o delivery.")
    if modalidade != "Delivery":
        endereco = None

    pedido_id = pedido_model.criar_pedido(
        nome, telefone, modalidade, endereco, pagamento,
        [{"produto_id": i["produto_id"], "quantidade": i["quantidade"],
          "preco_unitario": i["preco_unitario"]} for i in resumo["itens"]])
    carrinho_controller.limpar(sessao)
    return pedido_id, resumo["subtotal"]
