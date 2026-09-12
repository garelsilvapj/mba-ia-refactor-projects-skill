'use strict';

/**
 * Camada de rotas: mapeia URL → controller. Nenhuma lógica aqui.
 * Antes as três rotas eram registradas dentro de `AppManager.setupRoutes` (AppManager.js:25-137),
 * junto com toda a regra de negócio.
 */
const express = require('express');

const asyncHandler = require('../controllers/asyncHandler');
const requireAdmin = require('../middlewares/requireAdmin');

function criarRotas({ checkoutController, reportController, userController }) {
  const router = express.Router();

  router.post('/api/checkout', asyncHandler(checkoutController.criar));

  // Rotas administrativas agora exigem credencial.
  router.get(
    '/api/admin/financial-report',
    requireAdmin,
    asyncHandler(reportController.financeiro),
  );
  router.delete('/api/users/:id', requireAdmin, asyncHandler(userController.remover));

  return router;
}

module.exports = criarRotas;
