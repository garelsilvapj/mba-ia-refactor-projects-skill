"""Acesso a dados de pedido e itens.

Duas correções estruturais em relação a models.py:
  - a listagem usa um JOIN único (antes models.py:187-199 e 219-231 faziam 1 + N + N×M queries);
  - a criação é transacional, com decremento condicional de estoque (antes models.py:133-169
    fazia commit único ao final e saía por `return` sem rollback).
"""


class EstoqueInsuficiente(Exception):
    def __init__(self, produto_nome):
        super().__init__(produto_nome)
        self.produto_nome = produto_nome


SQL_LISTAGEM = """
SELECT pe.id            AS pedido_id,
       pe.usuario_id    AS usuario_id,
       pe.status        AS status,
       pe.total         AS total,
       pe.criado_em     AS criado_em,
       ip.produto_id    AS produto_id,
       ip.quantidade    AS quantidade,
       ip.preco_unitario AS preco_unitario,
       pr.nome          AS produto_nome
FROM pedidos pe
LEFT JOIN itens_pedido ip ON ip.pedido_id = pe.id
LEFT JOIN produtos pr ON pr.id = ip.produto_id
{filtro}
ORDER BY pe.id, ip.id
"""


class PedidoModel:
    def __init__(self, conexao_provider):
        self._conexao = conexao_provider

    # --- leitura ---

    def listar(self, usuario_id=None):
        if usuario_id is None:
            sql = SQL_LISTAGEM.format(filtro="")
            parametros = ()
        else:
            sql = SQL_LISTAGEM.format(filtro="WHERE pe.usuario_id = ?")
            parametros = (usuario_id,)

        pedidos = {}
        ordem = []
        for linha in self._conexao().execute(sql, parametros):
            pedido_id = linha["pedido_id"]
            if pedido_id not in pedidos:
                pedidos[pedido_id] = {
                    "id": pedido_id,
                    "usuario_id": linha["usuario_id"],
                    "status": linha["status"],
                    "total": linha["total"],
                    "criado_em": linha["criado_em"],
                    "itens": [],
                }
                ordem.append(pedido_id)
            if linha["produto_id"] is not None:
                pedidos[pedido_id]["itens"].append(
                    {
                        "produto_id": linha["produto_id"],
                        "produto_nome": linha["produto_nome"] or "Desconhecido",
                        "quantidade": linha["quantidade"],
                        "preco_unitario": linha["preco_unitario"],
                    }
                )
        return [pedidos[pedido_id] for pedido_id in ordem]

    def existe(self, pedido_id):
        return (
            self._conexao().execute(
                "SELECT 1 FROM pedidos WHERE id = ?", (pedido_id,)
            ).fetchone()
            is not None
        )

    def contar(self):
        return self._conexao().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]

    def resumo_vendas(self):
        """Agregação em uma query só (antes models.py:239-254 fazia cinco consultas)."""
        linha = self._conexao().execute(
            """
            SELECT COUNT(*) AS total_pedidos,
                   COALESCE(SUM(total), 0) AS faturamento,
                   COALESCE(SUM(status = 'pendente'), 0)  AS pendentes,
                   COALESCE(SUM(status = 'aprovado'), 0)  AS aprovados,
                   COALESCE(SUM(status = 'cancelado'), 0) AS cancelados
            FROM pedidos
            """
        ).fetchone()
        return dict(linha)

    # --- escrita ---

    def criar(self, usuario_id, itens_com_preco, total, status):
        """Cria pedido, itens e baixa de estoque em uma única transação."""
        conexao = self._conexao()
        try:
            conexao.execute("BEGIN")
            cursor = conexao.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, status, total),
            )
            pedido_id = cursor.lastrowid
            for item in itens_com_preco:
                # Decremento condicional: checagem e escrita no mesmo comando, sem corrida.
                afetadas = conexao.execute(
                    "UPDATE produtos SET estoque = estoque - ?"
                    " WHERE id = ? AND estoque >= ?",
                    (item["quantidade"], item["produto_id"], item["quantidade"]),
                ).rowcount
                if afetadas == 0:
                    raise EstoqueInsuficiente(item["produto_nome"])
                conexao.execute(
                    "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade,"
                    " preco_unitario) VALUES (?, ?, ?, ?)",
                    (
                        pedido_id,
                        item["produto_id"],
                        item["quantidade"],
                        item["preco_unitario"],
                    ),
                )
            conexao.commit()
            return pedido_id
        except Exception:
            conexao.rollback()
            raise

    def atualizar_status(self, pedido_id, novo_status):
        conexao = self._conexao()
        conexao.execute(
            "UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id)
        )
        conexao.commit()
        return True
