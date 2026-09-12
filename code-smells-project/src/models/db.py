"""Ciclo de vida da conexão, schema e seed.

Antes (database.py:4-11): uma conexão global de módulo, aberta com `check_same_thread=False`,
compartilhada por todas as requisições e nunca fechada, na mesma função que criava o schema e
populava o banco.

Agora: uma conexão por requisição, fechada no teardown; schema e seed em funções separadas,
executadas explicitamente na inicialização.
"""
import sqlite3

from flask import current_app, g
from werkzeug.security import generate_password_hash

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        descricao TEXT,
        preco REAL NOT NULL,
        estoque INTEGER NOT NULL DEFAULT 0,
        categoria TEXT,
        ativo INTEGER DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL,
        tipo TEXT NOT NULL DEFAULT 'cliente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
        status TEXT NOT NULL DEFAULT 'pendente',
        total REAL NOT NULL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER NOT NULL REFERENCES pedidos(id),
        produto_id INTEGER NOT NULL REFERENCES produtos(id),
        quantidade INTEGER NOT NULL,
        preco_unitario REAL NOT NULL
    )
    """,
)

PRODUTOS_SEED = [
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
]

# [corrige CRITICAL] as senhas do seed eram gravadas em texto puro (database.py:76-78).
# Agora são geradas com hash antes de entrar no banco.
USUARIOS_SEED = [
    ("Admin", "admin@loja.com", "admin123", "admin"),
    ("João Silva", "joao@email.com", "123456", "cliente"),
    ("Maria Santos", "maria@email.com", "senha123", "cliente"),
]


def conectar(db_path):
    """Abre uma conexão isolada (usada na inicialização, fora de uma requisição)."""
    conexao = sqlite3.connect(db_path)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def get_db():
    """Conexão da requisição atual, criada sob demanda e fechada no teardown."""
    if "db" not in g:
        g.db = conectar(current_app.config["DB_PATH"])
    return g.db


def close_db(_excecao=None):
    conexao = g.pop("db", None)
    if conexao is not None:
        conexao.close()


def criar_schema(db_path):
    conexao = conectar(db_path)
    try:
        for ddl in SCHEMA:
            conexao.execute(ddl)
        conexao.commit()
    finally:
        conexao.close()


def popular_dados_iniciais(db_path):
    """Popula o banco apenas quando está vazio. Idempotente e independente da conexão."""
    conexao = conectar(db_path)
    try:
        if conexao.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] == 0:
            conexao.executemany(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria)"
                " VALUES (?, ?, ?, ?, ?)",
                PRODUTOS_SEED,
            )
        if conexao.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
            conexao.executemany(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                [
                    (nome, email, generate_password_hash(senha), tipo)
                    for nome, email, senha, tipo in USUARIOS_SEED
                ],
            )
        conexao.commit()
    finally:
        conexao.close()


def init_db(db_path):
    criar_schema(db_path)
    popular_dados_iniciais(db_path)
