'use strict';

/**
 * Composition root: monta o grafo de dependências e devolve a app do Express.
 *
 * Não chama `listen` — isso é responsabilidade de `server.js`. Assim a app pode ser criada em
 * teste, com um banco em memória e dublês de gateway, sem abrir porta.
 *
 * Antes (app.js:8-10) o entry point instanciava a God Class `AppManager`, que criava a própria
 * conexão e recebia a instância do Express para registrar rotas.
 */
const express = require('express');

const { config } = require('./config');
const logger = require('./config/logger');

const { conectar } = require('./models/db');
const { criarSchema, popularDadosIniciais } = require('./models/schema');
const UserModel = require('./models/userModel');
const CourseModel = require('./models/courseModel');
const EnrollmentModel = require('./models/enrollmentModel');
const PaymentModel = require('./models/paymentModel');
const AuditLogModel = require('./models/auditLogModel');
const ReportModel = require('./models/reportModel');

const hasher = require('./services/passwordHasher');
const PaymentGateway = require('./services/paymentGateway');
const CheckoutService = require('./services/checkoutService');
const ReportService = require('./services/reportService');
const UserService = require('./services/userService');

const CheckoutController = require('./controllers/checkoutController');
const ReportController = require('./controllers/reportController');
const UserController = require('./controllers/userController');

const criarRotas = require('./routes');
const { errorHandler, notFoundHandler } = require('./middlewares/errorHandler');

function montarDependencias({ db, gateway }) {
  const userModel = new UserModel(db);
  const courseModel = new CourseModel(db);
  const enrollmentModel = new EnrollmentModel(db);
  const paymentModel = new PaymentModel(db);
  const auditLogModel = new AuditLogModel(db);
  const reportModel = new ReportModel(db);

  const checkoutService = new CheckoutService({
    db,
    userModel,
    courseModel,
    enrollmentModel,
    paymentModel,
    auditLogModel,
    gateway,
    hasher,
  });

  return {
    checkoutController: new CheckoutController({ checkoutService }),
    reportController: new ReportController({ reportService: new ReportService({ reportModel }) }),
    userController: new UserController({ userService: new UserService({ userModel }) }),
  };
}

/**
 * Cria a aplicação. As dependências podem ser injetadas (teste); sem elas, monta as reais.
 */
async function createApp({ db, gateway } = {}) {
  const conexao = db || (await conectar(config.dbFile));

  // A inicialização é aguardada: o servidor só sobe com o schema pronto.
  await criarSchema(conexao);
  await popularDadosIniciais(conexao, hasher.gerarHash);

  if (!config.adminToken) {
    logger.warn('ADMIN_TOKEN não configurado: rotas administrativas ficarão indisponíveis');
  }

  const app = express();
  app.use(express.json());
  app.use(criarRotas(montarDependencias({
    db: conexao,
    gateway: gateway || new PaymentGateway({ apiKey: config.paymentGatewayKey }),
  })));
  app.use(notFoundHandler);
  app.use(errorHandler); // sempre por último

  return app;
}

module.exports = { createApp };
