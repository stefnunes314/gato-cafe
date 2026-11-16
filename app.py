"""Front Controller: rotas Flask que delegam aos controllers."""
import os
from functools import wraps

from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   session, url_for)

from controllers import (admin_controller, carrinho_controller, pedido_controller,
                         reserva_controller, vitrine_controller)
from models.database import init_db

app = Flask(__name__, template_folder="views", static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-troque-em-producao")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

init_db()


def voltar(aba, **params):
    """Redireciona para a home, reabrindo a aba indicada."""
    return redirect(url_for("index", **params) + f"#{aba}")


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapper


# ---------- Cliente ----------
@app.get("/")
def index():
    contexto = vitrine_controller.dados_home(request.args.get("categoria"))
    contexto["carrinho"] = carrinho_controller.resumo(session)
    contexto["reserva"] = reserva_controller.dados_formulario()
    contexto["modalidades"] = carrinho_controller.MODALIDADES
    contexto["pagamentos"] = pedido_controller.FORMAS_PAGAMENTO
    return render_template("index.html", **contexto)


@app.post("/carrinho/<acao>")
@app.post("/carrinho/<acao>/<int:produto_id>")
def carrinho(acao, produto_id=None):
    try:
        if acao == "add":
            carrinho_controller.adicionar(session, produto_id)
            flash("Item adicionado ao carrinho.", "success")
            return voltar("cardapio", categoria=request.form.get("categoria") or None)
        if acao == "dec":
            carrinho_controller.decrementar(session, produto_id)
        elif acao == "remove":
            carrinho_controller.remover(session, produto_id)
            flash("Item removido.", "info")
        elif acao == "limpar":
            carrinho_controller.limpar(session)
            flash("Carrinho esvaziado.", "info")
        elif acao == "modalidade":
            carrinho_controller.definir_modalidade(session, request.form.get("modalidade"))
        elif acao == "inc":
            carrinho_controller.adicionar(session, produto_id)
        else:
            return ("Ação desconhecida", 404)
    except ValueError as e:
        flash(str(e), "danger")
    return voltar("carrinho")


@app.post("/checkout")
def checkout():
    try:
        pedido_id, total = pedido_controller.finalizar(
            session, request.form.get("nome"), request.form.get("telefone"),
            request.form.get("pagamento"), request.form.get("endereco"))
    except ValueError as e:
        flash(str(e), "danger")
        return voltar("carrinho")
    flash(f"Pedido #{pedido_id} confirmado! Total: R$ {total:.2f}".replace(".", ","), "success")
    return voltar("carrinho")


@app.post("/reservas")
def reservas():
    f = request.form
    try:
        reserva_id, total = reserva_controller.criar(
            f.get("nome"), f.get("telefone"), f.get("data"), f.get("horario"), f.get("qtd"))
    except ValueError as e:
        flash(str(e), "danger")
        return voltar("gatoterapia")
    flash(f"Reserva #{reserva_id} confirmada! Cat Fee: R$ {total:.2f}".replace(".", ","), "success")
    return voltar("gatoterapia")


@app.get("/api/vagas")
def api_vagas():
    try:
        return jsonify(reserva_controller.vagas(request.args.get("data")))
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400


@app.template_filter("brl")
def brl(valor):
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------- Administração ----------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if admin_controller.autenticar(request.form.get("senha")):
            session["admin"] = True
            return redirect(url_for("admin"))
        flash("Senha incorreta.", "danger")
    return render_template("admin_login.html")


@app.post("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("index"))


@app.get("/admin")
@admin_required
def admin():
    return render_template("admin.html", **admin_controller.dados_painel())


@app.post("/admin/capacidade")
@admin_required
def admin_capacidade():
    try:
        admin_controller.alterar_limite(request.form.get("horario"), request.form.get("limite"))
        flash("Limite de vagas atualizado.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin") + "#lotacao")


@app.post("/admin/gato/<int:gato_id>/status")
@admin_required
def admin_gato_status(gato_id):
    try:
        admin_controller.alterar_status_gato(gato_id, request.form.get("status"))
        flash("Status de adoção atualizado.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin") + "#adocao")


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=int(os.environ.get("PORT", 5000)))
