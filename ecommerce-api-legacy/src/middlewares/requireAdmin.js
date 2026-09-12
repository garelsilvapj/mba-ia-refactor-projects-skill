'use strict';

/**
 * Autorização das rotas administrativas.
 *
 * Antes o relatório financeiro (AppManager.js:80-129) e a exclusão de usuário (131-137) eram
 * públicos e não havia como protegê-los.
 *
 * A proteção é **opcional por configuração**, para não alterar o contrato da API já publicada:
 *   - sem `ADMIN_TOKEN` no ambiente, as rotas respondem como antes (e o boot avisa no log);
 *   - com `ADMIN_TOKEN` definido, passam a exigir o cabeçalho `X-Admin-Token`.
 *
 * Assim o `api.http` do projeto continua funcionando sem configuração alguma, e quem for para
 * produção ativa a proteção definindo uma variável de ambiente.
 */
const { config } = require('../config');
const logger = require('../config/logger');
const { UnauthorizedError } = require('./errors');

let avisoEmitido = false;

function requireAdmin(req, _res, next) {
  if (!config.adminToken) {
    if (!avisoEmitido) {
      logger.warn(
        'ADMIN_TOKEN não configurado: rotas administrativas seguem abertas, como no comportamento original',
        { rota: `${req.method} ${req.originalUrl}` },
      );
      avisoEmitido = true;
    }
    return next();
  }

  const enviado = req.get('X-Admin-Token');
  if (!enviado || enviado !== config.adminToken) {
    return next(new UnauthorizedError('Credencial de administrador inválida'));
  }
  return next();
}

module.exports = requireAdmin;
