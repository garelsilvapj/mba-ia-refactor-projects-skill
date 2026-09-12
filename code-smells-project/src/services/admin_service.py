"""Operações administrativas sobre a base."""

TABELAS = ("itens_pedido", "pedidos", "produtos", "usuarios")


class AdminService:
    def __init__(self, conexao_provider):
        self._conexao = conexao_provider

    def resetar_banco(self):
        """Esvazia as tabelas em uma única transação (antes eram 4 DELETE soltos com commit)."""
        conexao = self._conexao()
        try:
            conexao.execute("BEGIN")
            for tabela in TABELAS:
                conexao.execute(f"DELETE FROM {tabela}")  # identificadores fixos, não entrada
            conexao.commit()
        except Exception:
            conexao.rollback()
            raise
        return True
