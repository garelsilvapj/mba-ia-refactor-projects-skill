'use strict';

/** Entry point: cria a aplicação e abre a porta. */
const { createApp } = require('./app');
const { config } = require('./config');
const logger = require('./config/logger');

createApp()
  .then((app) => {
    app.listen(config.port, () => {
      logger.info('LMS API no ar', { porta: config.port });
    });
  })
  .catch((erro) => {
    logger.error('falha ao iniciar a aplicação', { erro: erro.message });
    process.exit(1);
  });
