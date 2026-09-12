"""Regra de negócio de pedido.

Antes: o cálculo do total, a checagem de estoque e a montagem do pedido estavam dentro de
models.py:133-169 (camada de dados), a lista de status válidos e os efeitos colaterais de
notificação estavam dentro do controller (controllers.py:242-250).
"""
from src.middlewares.errors import NotFoundError, ValidationError
from src.models.pedido_model import EstoqueInsuficiente


class PedidoService:
    def __init__(self, pedido_model, produto_model, config, notificador):
        self._pedidos = pedido_model
        self._produtos = produto_model
        self._config = config
        self._notificador = notificador

    def listar(self, usuario_id=None):
        return self._pedidos.listar(usuario_id)

    def criar(self, dados):
        if not dados:
            raise ValidationError("Dados inválidos")

        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens") or []

        if usuario_id is None:
            raise ValidationError("Usuario ID é obrigatório")
        if not itens:
            raise ValidationError("Pedido deve ter pelo menos 1 item")

        itens_com_preco, total = self._preparar_itens(itens)

        try:
            pedido_id = self._pedidos.criar(
                usuario_id, itens_com_preco, total, self._config.STATUS_PEDIDO_PADRAO
            )
        except EstoqueInsuficiente as erro:
            raise ValidationError(f"Estoque insuficiente para {erro.produto_nome}") from None

        self._notificador.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    def atualizar_status(self, pedido_id, novo_status):
        if novo_status not in self._config.STATUS_PEDIDO_VALIDOS:
            raise ValidationError("Status inválido")
        if not self._pedidos.existe(pedido_id):
            raise NotFoundError("Pedido não encontrado")

        self._pedidos.atualizar_status(pedido_id, novo_status)
        self._notificador.status_alterado(pedido_id, novo_status)
        return True

    # --- regras ---

    def _preparar_itens(self, itens):
        """Resolve preço e valida existência; o estoque é conferido na transação da escrita."""
        preparados = []
        total = 0.0
        for item in itens:
            produto_id = item.get("produto_id")
            quantidade = item.get("quantidade")
            if produto_id is None or quantidade is None:
                raise ValidationError("Item precisa de produto_id e quantidade")
            if not isinstance(quantidade, int) or isinstance(quantidade, bool) or quantidade <= 0:
                raise ValidationError("Quantidade deve ser um inteiro positivo")

            produto = self._produtos.buscar_por_id(produto_id)
            if produto is None:
                raise ValidationError(f"Produto {produto_id} não encontrado")
            if produto["estoque"] < quantidade:
                raise ValidationError(f"Estoque insuficiente para {produto['nome']}")

            total += produto["preco"] * quantidade
            preparados.append(
                {
                    "produto_id": produto_id,
                    "produto_nome": produto["nome"],
                    "quantidade": quantidade,
                    "preco_unitario": produto["preco"],
                }
            )
        return preparados, total
