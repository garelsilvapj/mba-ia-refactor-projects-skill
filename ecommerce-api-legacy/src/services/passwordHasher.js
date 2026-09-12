'use strict';

/**
 * Hash de senha com scrypt (módulo `crypto` da própria plataforma, sem dependência nova).
 *
 * Substitui `badCrypto` (utils.js:17-23), que concatenava base64 truncado — reversível e
 * colidível. Aqui cada senha tem salt próprio e a comparação é em tempo constante.
 */
const crypto = require('crypto');
const { promisify } = require('util');

const scrypt = promisify(crypto.scrypt);
const TAMANHO_SALT = 16;
const TAMANHO_CHAVE = 64;

async function gerarHash(senha) {
  const salt = crypto.randomBytes(TAMANHO_SALT).toString('hex');
  const derivada = await scrypt(senha, salt, TAMANHO_CHAVE);
  return `scrypt$${salt}$${derivada.toString('hex')}`;
}

async function verificar(senha, armazenado) {
  if (typeof armazenado !== 'string') return false;
  const [algoritmo, salt, esperado] = armazenado.split('$');
  if (algoritmo !== 'scrypt' || !salt || !esperado) return false;

  const derivada = await scrypt(senha, salt, TAMANHO_CHAVE);
  const esperadoBuffer = Buffer.from(esperado, 'hex');
  if (esperadoBuffer.length !== derivada.length) return false;
  return crypto.timingSafeEqual(derivada, esperadoBuffer);
}

module.exports = { gerarHash, verificar };
