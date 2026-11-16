"""Painel administrativo: lotação, status de adoção e histórico (US05)."""
import os

from models import pedido_model, produto_model, reserva_model
from models.database import STATUS_ADOCAO

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")


def autenticar(senha):
    return (senha or "") == ADMIN_PASSWORD


def dados_painel():
    return {"capacidades": reserva_model.listar_capacidades(),
            "gatos": produto_model.listar_gatos(),
            "status_opcoes": STATUS_ADOCAO,
            "pedidos": pedido_model.listar_pedidos(),
            "reservas": reserva_model.listar_reservas()}


def alterar_limite(horario, limite_texto):
    try:
        limite = int(limite_texto)
    except (TypeError, ValueError):
        raise ValueError("Informe um limite numérico.")
    if not 1 <= limite <= 100:
        raise ValueError("O limite deve ficar entre 1 e 100.")
    if not reserva_model.atualizar_limite(horario, limite):
        raise ValueError("Horário não encontrado.")


def alterar_status_gato(gato_id, status):
    if status not in STATUS_ADOCAO:
        raise ValueError("Status inválido.")
    if not produto_model.atualizar_status_gato(gato_id, status):
        raise ValueError("Gato não encontrado.")
