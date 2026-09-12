"""Regra de negócio de produto.

Antes: as regras (faixa de preço, tamanho do nome, categorias válidas) estavam dentro dos
controllers, duplicadas entre criação e atualização (controllers.py:28-54 e 72-90).
"""
from src.middlewares.errors import NotFoundError, ValidationError


def _numero(valor, campo):
    """Converte para número recusando bool e texto — antes um preço textual virava 500."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValidationError(f"{campo} deve ser numérico")
    return valor


class ProdutoService:
    def __init__(self, produto_model, config):
        self._produtos = produto_model
        self._config = config

    def listar(self):
        return self._produtos.listar()

    def buscar(self, produto_id):
        produto = self._produtos.buscar_por_id(produto_id)
        if produto is None:
            raise NotFoundError("Produto não encontrado")
        return produto

    def pesquisar(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        return self._produtos.buscar(termo, categoria, preco_min, preco_max)

    def criar(self, dados):
        campos = self._validar(dados, exigir_categoria_valida=True)
        return self._produtos.criar(**campos)

    def atualizar(self, produto_id, dados):
        self.buscar(produto_id)  # 404 se não existir, antes de validar o corpo
        campos = self._validar(dados, exigir_categoria_valida=True)
        self._produtos.atualizar(produto_id, **campos)
        return True

    def deletar(self, produto_id):
        self.buscar(produto_id)
        self._produtos.deletar(produto_id)
        return True

    # --- regras ---

    def _validar(self, dados, exigir_categoria_valida):
        if not dados:
            raise ValidationError("Dados inválidos")
        if "nome" not in dados:
            raise ValidationError("Nome é obrigatório")
        if "preco" not in dados:
            raise ValidationError("Preço é obrigatório")
        if "estoque" not in dados:
            raise ValidationError("Estoque é obrigatório")

        nome = dados["nome"]
        if not isinstance(nome, str):
            raise ValidationError("Nome deve ser texto")
        preco = _numero(dados["preco"], "Preço")
        estoque = _numero(dados["estoque"], "Estoque")
        categoria = dados.get("categoria", "geral")

        if preco < 0:
            raise ValidationError("Preço não pode ser negativo")
        if estoque < 0:
            raise ValidationError("Estoque não pode ser negativo")
        if len(nome) < self._config.NOME_PRODUTO_MIN:
            raise ValidationError("Nome muito curto")
        if len(nome) > self._config.NOME_PRODUTO_MAX:
            raise ValidationError("Nome muito longo")
        if exigir_categoria_valida and categoria not in self._config.CATEGORIAS_VALIDAS:
            validas = list(self._config.CATEGORIAS_VALIDAS)
            raise ValidationError(f"Categoria inválida. Válidas: {validas}")

        return {
            "nome": nome,
            "descricao": dados.get("descricao", ""),
            "preco": preco,
            "estoque": estoque,
            "categoria": categoria,
        }
