"""Regra de negócio do relatório de vendas.

Antes: as faixas de desconto (10%, 5%, 2%) e o ticket médio eram calculados dentro da camada de
dados, em models.py:256-272, junto com cinco consultas separadas de contagem.
"""


class RelatorioService:
    def __init__(self, pedido_model, config):
        self._pedidos = pedido_model
        self._config = config

    def vendas(self):
        resumo = self._pedidos.resumo_vendas()
        total_pedidos = resumo["total_pedidos"]
        faturamento = resumo["faturamento"] or 0

        percentual = self._percentual_desconto(faturamento)
        # sem faixa aplicável o desconto é zero exato, não 0.0 por multiplicação
        desconto = faturamento * percentual if percentual else 0
        ticket_medio = faturamento / total_pedidos if total_pedidos > 0 else 0

        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": resumo["pendentes"],
            "pedidos_aprovados": resumo["aprovados"],
            "pedidos_cancelados": resumo["cancelados"],
            "ticket_medio": round(ticket_medio, 2),
        }

    def _percentual_desconto(self, faturamento):
        """Faixas vindas de config, em vez de magic numbers no meio do cálculo."""
        for minimo, percentual in self._config.FAIXAS_DESCONTO:
            if faturamento > minimo:
                return percentual
        return 0.0
