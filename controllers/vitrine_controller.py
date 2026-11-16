"""Orquestra dados da home e filtros (US01)."""
from models import produto_model
from models.database import CATEGORIAS, ONGS

ICONES_CATEGORIA = {"Cafés": "☕", "Doces": "🍰", "Salgados": "🥐", "Temáticos": "🐾"}


def dados_home(categoria=None):
    if categoria not in CATEGORIAS:
        categoria = None
    return {
        "produtos": produto_model.listar_produtos(categoria),
        "categorias": CATEGORIAS,
        "categoria_ativa": categoria,
        "icones": ICONES_CATEGORIA,
        "gatos": produto_model.listar_gatos(),
        "ongs": ONGS,
    }
