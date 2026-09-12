"""Controller de produto: lê a requisição, chama o service, formata a resposta.

Sem SQL, sem regra de negócio e sem `try/except` — o erro sobe para o handler central.
"""
from flask import jsonify, request

from src.middlewares.errors import ValidationError


def _float_opcional(valor, campo):
    if valor is None:
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        raise ValidationError(f"{campo} deve ser numérico") from None


class ProdutoController:
    def __init__(self, produto_service):
        self._service = produto_service

    def listar(self):
        return jsonify({"dados": self._service.listar(), "sucesso": True}), 200

    def buscar(self, id):
        return jsonify({"dados": self._service.buscar(id), "sucesso": True}), 200

    def pesquisar(self):
        resultados = self._service.pesquisar(
            termo=request.args.get("q", ""),
            categoria=request.args.get("categoria"),
            preco_min=_float_opcional(request.args.get("preco_min"), "preco_min"),
            preco_max=_float_opcional(request.args.get("preco_max"), "preco_max"),
        )
        return (
            jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}),
            200,
        )

    def criar(self):
        produto_id = self._service.criar(request.get_json(silent=True))
        return (
            jsonify(
                {
                    "dados": {"id": produto_id},
                    "sucesso": True,
                    "mensagem": "Produto criado",
                }
            ),
            201,
        )

    def atualizar(self, id):
        self._service.atualizar(id, request.get_json(silent=True))
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    def deletar(self, id):
        self._service.deletar(id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
