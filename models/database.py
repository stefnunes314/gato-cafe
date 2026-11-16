"""Conexão SQLite, PRAGMA de chaves estrangeiras, schema e seed inicial."""
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get("GATOCAFE_DB", os.path.join(BASE_DIR, "instance", "gatocafe.db"))

CATEGORIAS = ("Cafés", "Doces", "Salgados", "Temáticos")
STATUS_ADOCAO = ("Disponível", "Em processo", "Adotado")
HORARIOS = ("10:00", "12:00", "14:00", "16:00", "18:00")
LIMITE_PADRAO = 8

SCHEMA = """
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    descricao TEXT NOT NULL,
    preco REAL NOT NULL CHECK (preco >= 0),
    categoria TEXT NOT NULL CHECK (categoria IN ('Cafés','Doces','Salgados','Temáticos'))
);
CREATE TABLE IF NOT EXISTS gatos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    idade TEXT NOT NULL,
    temperamento TEXT NOT NULL,
    ong_parceira TEXT NOT NULL,
    status_adocao TEXT NOT NULL DEFAULT 'Disponível'
        CHECK (status_adocao IN ('Disponível','Em processo','Adotado')),
    foto TEXT
);
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_nome TEXT NOT NULL,
    telefone TEXT NOT NULL,
    modalidade TEXT NOT NULL CHECK (modalidade IN ('Consumo Local','Delivery')),
    endereco TEXT,
    forma_pagamento TEXT NOT NULL CHECK (forma_pagamento IN ('Pix','Cartão de Crédito')),
    total REAL NOT NULL CHECK (total >= 0),
    criado_em TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS itens_pedido (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    produto_id INTEGER NOT NULL REFERENCES produtos(id),
    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
    preco_unitario REAL NOT NULL CHECK (preco_unitario >= 0)
);
CREATE TABLE IF NOT EXISTS capacidade_horarios (
    horario TEXT PRIMARY KEY,
    limite_maximo_clientes INTEGER NOT NULL CHECK (limite_maximo_clientes > 0)
);
CREATE TABLE IF NOT EXISTS reservas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_nome TEXT NOT NULL,
    telefone TEXT NOT NULL,
    data_reserva TEXT NOT NULL,
    horario TEXT NOT NULL REFERENCES capacidade_horarios(horario),
    qtd_pessoas INTEGER NOT NULL CHECK (qtd_pessoas > 0),
    cat_fee_total REAL NOT NULL CHECK (cat_fee_total >= 0),
    criado_em TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
"""

PRODUTOS_SEED = [
    ("Espresso", "Café intenso de grãos especiais, torra média.", 7.00, "Cafés"),
    ("Cappuccino Cremoso", "Espresso, leite vaporizado e espuma aveludada.", 12.50, "Cafés"),
    ("Café Coado V60", "Método filtrado, notas frutadas e acidez suave.", 11.00, "Cafés"),
    ("Brownie de Chocolate", "Brownie úmido com chocolate 70%.", 11.90, "Doces"),
    ("Cheesecake de Frutas Vermelhas", "Fatia cremosa com calda artesanal.", 16.00, "Doces"),
    ("Pão de Queijo Recheado", "Porção com 4 unidades recheadas com requeijão.", 14.00, "Salgados"),
    ("Croissant de Presunto e Queijo", "Folhado amanteigado, servido quente.", 15.50, "Salgados"),
    ("Latte Patinha", "Latte com arte de patinha de gato em cacau.", 14.50, "Temáticos"),
    ("Cookie Focinho", "Cookie de baunilha decorado com focinho de gato.", 9.50, "Temáticos"),
]

GATOS_SEED = [
    ("Mingau", "2 anos", "Calmo e carinhoso", "ONG Patas Amigas", "Disponível"),
    ("Pipoca", "8 meses", "Brincalhona e curiosa", "Abrigo Miau Feliz", "Disponível"),
    ("Thor", "5 anos", "Independente e tranquilo", "ONG Patas Amigas", "Em processo"),
    ("Luna", "3 anos", "Sociável e dorminhoca", "Abrigo Miau Feliz", "Disponível"),
]


# Fotos em static/img/gatos (Unsplash, licença livre)
FOTOS_SEED = {"Mingau": "mingau.jpg", "Pipoca": "pipoca.jpg", "Thor": "thor.jpg", "Luna": "luna.jpg"}

# Contatos fictícios das ONGs parceiras (dados de exemplo)
ONGS = {
    "ONG Patas Amigas": {"telefone": "(11) 4002-1001", "email": "adocao@patasamigas.example",
                         "instagram": "@patasamigas"},
    "Abrigo Miau Feliz": {"telefone": "(11) 4002-2002", "email": "contato@miaufeliz.example",
                          "instagram": "@abrigomiaufeliz"},
}


def get_connection():
    """Abre conexão com FK ativadas. Autocommit; transações são explícitas (BEGIN)."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, isolation_level=None, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        if conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO produtos (nome, descricao, preco, categoria) VALUES (?,?,?,?)",
                PRODUTOS_SEED,
            )
        if conn.execute("SELECT COUNT(*) FROM gatos").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO gatos (nome, idade, temperamento, ong_parceira, status_adocao) "
                "VALUES (?,?,?,?,?)",
                GATOS_SEED,
            )
        # Migração: coluna de foto dos gatos (bancos criados antes desta versão)
        colunas = {r["name"] for r in conn.execute("PRAGMA table_info(gatos)")}
        if "foto" not in colunas:
            conn.execute("ALTER TABLE gatos ADD COLUMN foto TEXT")
        for nome, foto in FOTOS_SEED.items():
            conn.execute("UPDATE gatos SET foto = ? WHERE nome = ? AND foto IS NULL", (foto, nome))
        if conn.execute("SELECT COUNT(*) FROM capacidade_horarios").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO capacidade_horarios (horario, limite_maximo_clientes) VALUES (?,?)",
                [(h, LIMITE_PADRAO) for h in HORARIOS],
            )
    finally:
        conn.close()
