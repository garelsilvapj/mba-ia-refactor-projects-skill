"""Acesso a dados de usuário.

Duas correções de segurança em relação a models.py:
  - a senha nunca sai pela serialização pública (antes models.py:83 e 99 devolviam `senha`);
  - as queries são parametrizadas, o que elimina o bypass de login por SQL Injection
    (antes models.py:110).
"""
import sqlite3

# [corrige CRITICAL] allowlist de campos: 'senha' não está aqui e não sai em nenhuma resposta.
CAMPOS_PUBLICOS = ("id", "nome", "email", "tipo", "criado_em")
CAMPOS_LOGIN = ("id", "nome", "email", "tipo")


def _serializar(linha, campos=CAMPOS_PUBLICOS):
    return {campo: linha[campo] for campo in campos}


class EmailJaCadastrado(Exception):
    """Sinaliza violação da restrição UNIQUE de e-mail para a camada de serviço."""


class UsuarioModel:
    def __init__(self, conexao_provider):
        self._conexao = conexao_provider

    def listar(self):
        linhas = self._conexao().execute("SELECT * FROM usuarios ORDER BY id").fetchall()
        return [_serializar(linha) for linha in linhas]

    def buscar_por_id(self, usuario_id):
        linha = self._conexao().execute(
            "SELECT * FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        return _serializar(linha) if linha else None

    def buscar_por_email(self, email):
        """Uso interno da autenticação: devolve a linha completa, com o hash da senha."""
        return self._conexao().execute(
            "SELECT * FROM usuarios WHERE email = ?", (email,)
        ).fetchone()

    def criar(self, nome, email, senha_hash, tipo):
        conexao = self._conexao()
        try:
            cursor = conexao.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, senha_hash, tipo),
            )
        except sqlite3.IntegrityError as erro:
            raise EmailJaCadastrado(email) from erro
        conexao.commit()
        return cursor.lastrowid

    def contar(self):
        return self._conexao().execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]

    @staticmethod
    def serializar_login(linha):
        return _serializar(linha, CAMPOS_LOGIN)
