"""Persistência de reservas e capacidade_horarios."""
from models.database import get_connection


class LotacaoExcedida(Exception):
    def __init__(self, vagas_restantes):
        self.vagas_restantes = vagas_restantes
        super().__init__("Lotação excedida")


def listar_capacidades():
    conn = get_connection()
    try:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM capacidade_horarios ORDER BY horario").fetchall()]
    finally:
        conn.close()


def atualizar_limite(horario, limite):
    conn = get_connection()
    try:
        cur = conn.execute(
            "UPDATE capacidade_horarios SET limite_maximo_clientes = ? WHERE horario = ?",
            (limite, horario))
        return cur.rowcount > 0
    finally:
        conn.close()


def vagas_por_horario(data_reserva):
    """Retorna {horario: vagas_restantes} para a data informada."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT c.horario, c.limite_maximo_clientes - COALESCE(SUM(r.qtd_pessoas), 0) AS vagas "
            "FROM capacidade_horarios c "
            "LEFT JOIN reservas r ON r.horario = c.horario AND r.data_reserva = ? "
            "GROUP BY c.horario ORDER BY c.horario", (data_reserva,)).fetchall()
        return {r["horario"]: max(r["vagas"], 0) for r in rows}
    finally:
        conn.close()


def criar_reserva(cliente_nome, telefone, data_reserva, horario, qtd_pessoas, cat_fee_total):
    """Verifica a lotação (RN02) e grava a reserva na mesma transação.

    BEGIN IMMEDIATE trava escritas concorrentes entre a checagem e o INSERT.
    """
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        try:
            cap = conn.execute(
                "SELECT limite_maximo_clientes FROM capacidade_horarios WHERE horario = ?",
                (horario,)).fetchone()
            if cap is None:
                raise ValueError("Horário inválido.")
            ocupados = conn.execute(
                "SELECT COALESCE(SUM(qtd_pessoas), 0) FROM reservas "
                "WHERE data_reserva = ? AND horario = ?", (data_reserva, horario)).fetchone()[0]
            limite = cap["limite_maximo_clientes"]
            if ocupados + qtd_pessoas > limite:
                raise LotacaoExcedida(max(limite - ocupados, 0))
            cur = conn.execute(
                "INSERT INTO reservas (cliente_nome, telefone, data_reserva, horario, "
                "qtd_pessoas, cat_fee_total) VALUES (?,?,?,?,?,?)",
                (cliente_nome, telefone, data_reserva, horario, qtd_pessoas, cat_fee_total))
            conn.execute("COMMIT")
            return cur.lastrowid
        except Exception:
            conn.execute("ROLLBACK")
            raise
    finally:
        conn.close()


def listar_reservas():
    conn = get_connection()
    try:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM reservas ORDER BY data_reserva DESC, horario DESC LIMIT 100").fetchall()]
    finally:
        conn.close()
