'use strict';

/**
 * Gateway de pagamento.
 *
 * Antes a autorização era a expressão `cc.startsWith("4") ? "PAID" : "DENIED"` escrita dentro do
 * handler HTTP (AppManager.js:46), e o número do cartão era impresso em log junto com a chave de
 * produção (AppManager.js:45).
 *
 * Aqui vira uma dependência com interface própria: o service depende desta abstração e um dublê
 * a substitui em teste. A regra "cartão iniciado em 4 é aprovado" segue sendo a do ambiente de
 * simulação, agora isolada em um único lugar.
 */
const logger = require('../config/logger');
const { PaymentStatus } = require('../config');

class PaymentGateway {
  constructor({ apiKey }) {
    this.apiKey = apiKey;
  }

  /** Nunca registra o número completo do cartão nem a chave: só os quatro últimos dígitos. */
  autorizar({ numeroCartao, valor }) {
    const aprovado = String(numeroCartao).startsWith('4');
    const status = aprovado ? PaymentStatus.PAID : PaymentStatus.DENIED;

    logger.info('autorização de pagamento', {
      final: String(numeroCartao).slice(-4),
      valor,
      status,
    });
    return { status, aprovado };
  }
}

module.exports = PaymentGateway;
