'use strict';

/**
 * Autorização das rotas administrativas.
 *
 * Antes o relatório financeiro (AppManager.js:80-129) e a exclusão de usuário (131-137) eram
 * públicos. Agora exigem o token de administrador configurado por ambiente.
 */
const { config } = require('../config');
const { ForbiddenError, UnauthorizedError } = require('./errors');

function requireAdmin(req, _res, next) {
  if (!config.adminToken) {
    return next(
      new ForbiddenError(
        'ADMIN_TOKEN não configurado: rotas administrativas indisponíveis',
      ),
    );
  }
  const enviado = req.get('X-Admin-Token');
  if (!enviado || enviado !== config.adminToken) {
    return next(new UnauthorizedError('Credencial de administrador inválida'));
  }
  return next();
}

module.exports = requireAdmin;
