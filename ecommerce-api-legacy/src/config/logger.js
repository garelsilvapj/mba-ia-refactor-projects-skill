'use strict';

/**
 * Logger mínimo com níveis.
 *
 * Substitui os `console.log` diretos — em especial o de AppManager.js:45, que imprimia o número
 * completo do cartão e a chave do gateway. Nada de segredo ou PAN passa por aqui.
 */
const { config } = require('./index');

const NIVEIS = { error: 0, warn: 1, info: 2, debug: 3 };

function registrar(nivel, mensagem, contexto) {
  if (NIVEIS[nivel] > (NIVEIS[config.logLevel] ?? NIVEIS.info)) return;
  const linha = { nivel, mensagem, ...(contexto || {}) };
  process.stdout.write(`${JSON.stringify(linha)}\n`);
}

module.exports = {
  error: (m, c) => registrar('error', m, c),
  warn: (m, c) => registrar('warn', m, c),
  info: (m, c) => registrar('info', m, c),
  debug: (m, c) => registrar('debug', m, c),
};
