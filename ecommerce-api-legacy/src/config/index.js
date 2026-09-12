'use strict';

/**
 * Configuração da aplicação: tudo vem do ambiente.
 *
 * Antes (src/utils.js:1-7) este objeto trazia a senha do banco, a chave `pk_live` do gateway e
 * o usuário de SMTP como literais no código. Nada aqui tem segredo embutido.
 */

const PaymentStatus = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });

const config = {
  port: Number(process.env.PORT || 3000),
  // ':memory:' mantém o comportamento original de banco volátil por execução.
  dbFile: process.env.DB_FILE || ':memory:',

  // Segredos: sem valor padrão. Ausentes, os recursos que dependem deles ficam desativados.
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
  adminToken: process.env.ADMIN_TOKEN || '',

  smtpUser: process.env.SMTP_USER || '',

  // Regras de negócio que antes eram magic numbers/strings espalhados.
  bcryptRounds: Number(process.env.BCRYPT_ROUNDS || 10),
  logLevel: process.env.LOG_LEVEL || 'info',
};

module.exports = { config, PaymentStatus };
