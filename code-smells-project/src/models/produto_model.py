"""Acesso a dados de produto. Sem HTTP, sem regra de negócio.

Todas as queries são parametrizadas — antes eram montadas por concatenação
(models.py:28, 47-50, 57-61, 68, 289-297).
"""

CAMPOS_PUBLICOS = (
    "id",
    "nome",
    "descricao",
    "preco",
    "estoque",
    "categoria",
    "ativo",
    "criado_em",
)


def _serializar(linha):
    """Mapeamento único linha → dicionário (antes duplicado em 3 pontos de models.py)."""
    return {campo: linha[campo] for campo in CAMPOS_PUBLICOS}


class ProdutoModel:
    def __init__(self, conexao_provider):
        # Dependência injetada: o model não sabe de onde vem a conexão.
        self._conexao = conexao_provider

    def listar(self):
        linhas = self._conexao().execute("SELECT * FROM produtos ORDER BY id").fetchall()
        return [_serializar(linha) for linha in linhas]

    def buscar_por_id(self, produto_id):
        linha = self._conexao().execute(
            "SELECT * FROM produtos WHERE id = ?", (produto_id,)
        ).fetchone()
        return _serializar(linha) if linha else None

    def criar(self, nome, descricao, preco, estoque, categoria):
        conexao = self._conexao()
        cursor = conexao.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria)"
            " VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
        conexao.commit()
        return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        conexao = self._conexao()
        conexao.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?,"
            " categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )
        conexao.commit()
        return True

    def deletar(self, produto_id):
        conexao = self._conexao()
        conexao.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        conexao.commit()
        return True

    def buscar(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        """Filtro dinâmico: só a cláusula é construída; os valores vão como parâmetros."""
        clausulas = ["1=1"]
        parametros = []
        if termo:
            clausulas.append("(nome LIKE ? OR descricao LIKE ?)")
            parametros.extend([f"%{termo}%", f"%{termo}%"])
        if categoria:
            clausulas.append("categoria = ?")
            parametros.append(categoria)
        # `is not None` em vez de veracidade: o valor 0 é um filtro legítimo.
        if preco_min is not None:
            clausulas.append("preco >= ?")
            parametros.append(preco_min)
        if preco_max is not None:
            clausulas.append("preco <= ?")
            parametros.append(preco_max)

        sql = f"SELECT * FROM produtos WHERE {' AND '.join(clausulas)} ORDER BY id"
        linhas = self._conexao().execute(sql, parametros).fetchall()
        return [_serializar(linha) for linha in linhas]

    def contar(self):
        return self._conexao().execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
