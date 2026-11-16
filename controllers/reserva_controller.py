"""Valida data, Cat Fee e lotação (US04, US05, RN01-RN03)."""
from datetime import date, datetime

from controllers.pedido_controller import validar_contato
from models import reserva_model
from models.reserva_model import LotacaoExcedida

CAT_FEE_POR_PESSOA = 25.00  # RN01
MAX_PESSOAS_POR_RESERVA = 10


def calcular_cat_fee(qtd_pessoas):
    return round(CAT_FEE_POR_PESSOA * qtd_pessoas, 2)


def _parse_data(texto):
    try:
        return datetime.strptime(texto or "", "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Informe uma data válida.")


def criar(nome, telefone, data_texto, horario, qtd_texto):
    """Cria a reserva e retorna (reserva_id, cat_fee_total). Levanta ValueError com mensagem ao usuário."""
    nome, telefone = validar_contato(nome, telefone)
    data_reserva = _parse_data(data_texto)
    if data_reserva < date.today():  # RN03
        raise ValueError("Não é possível agendar em data anterior a hoje.")
    try:
        qtd = int(qtd_texto)
    except (TypeError, ValueError):
        raise ValueError("Informe o número de pessoas.")
    if not 1 <= qtd <= MAX_PESSOAS_POR_RESERVA:
        raise ValueError(f"O número de pessoas deve ficar entre 1 e {MAX_PESSOAS_POR_RESERVA}.")
    if horario not in {c["horario"] for c in reserva_model.listar_capacidades()}:
        raise ValueError("Escolha um horário válido.")

    total = calcular_cat_fee(qtd)
    try:
        reserva_id = reserva_model.criar_reserva(
            nome, telefone, data_reserva.isoformat(), horario, qtd, total)
    except LotacaoExcedida as e:  # RN02
        if e.vagas_restantes == 0:
            raise ValueError(f"Horário {horario} esgotado nesta data. Escolha outro horário.")
        raise ValueError(
            f"Lotação excedida. Restam apenas {e.vagas_restantes} vaga(s) às {horario} nesta data.")
    return reserva_id, total


def dados_formulario():
    return {"capacidades": reserva_model.listar_capacidades(),
            "hoje": date.today().isoformat(),
            "cat_fee": CAT_FEE_POR_PESSOA,
            "max_pessoas": MAX_PESSOAS_POR_RESERVA}


def vagas(data_texto):
    data_reserva = _parse_data(data_texto)
    if data_reserva < date.today():
        raise ValueError("Data anterior a hoje.")
    return reserva_model.vagas_por_horario(data_reserva.isoformat())
