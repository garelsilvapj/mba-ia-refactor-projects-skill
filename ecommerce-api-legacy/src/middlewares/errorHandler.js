'use strict';

/**
 * Tratamento de erro centralizado. Registrado por último, com quatro argumentos.
 * Detalhe técnico vai para o log; o cliente recebe JSON com a mensagem adequada ao status.
 */
const logger = require('../config/logger');
const { AppError } = require('./errors');

function notFoundHandler(req, res) {
  res.status(404).json({ error: 'Rota não encontrada' });
}

// eslint-disable-next-line no-unused-vars
function errorHandler(erro, req, res, _next) {
  const status = erro instanceof AppError ? erro.status : 500;

  if (status >= 500) {
    logger.error('erro não tratado', { rota: `${req.method} ${req.originalUrl}`, erro: erro.message });
    return res.status(status).json({ error: 'Erro interno' });
  }

  logger.info('requisição rejeitada', {
    rota: `${req.method} ${req.originalUrl}`,
    status,
    motivo: erro.message,
  });
  return res.status(status).json({ error: erro.message });
}

module.exports = { errorHandler, notFoundHandler };
