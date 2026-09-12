'use strict';

/**
 * Encaminha erros de handlers assíncronos para o middleware de erro.
 * O Express 4 não captura rejeições de promise sozinho; sem isto cada controller precisaria do
 * seu próprio try/catch — exatamente o que a refatoração eliminou.
 */
module.exports = (handler) => (req, res, next) =>
  Promise.resolve(handler(req, res, next)).catch(next);
