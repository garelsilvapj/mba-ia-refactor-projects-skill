'use strict';

/**
 * Conexão e transações.
 *
 * Antes (AppManager.js:5-8) a conexão era criada dentro do construtor da God Class e usada com a
 * API de callbacks, o que produzia a pirâmide de AppManager.js:37-77. Aqui o driver é
 * promisificado uma única vez e exposto com `async/await` e suporte a transação.
 */
const sqlite3 = require('sqlite3');
const { promisify } = require('util');

function promisificar(db) {
  const api = {
    get: promisify(db.get.bind(db)),
    all: promisify(db.all.bind(db)),
    exec: promisify(db.exec.bind(db)),
    close: promisify(db.close.bind(db)),

    // `function` (e não arrow) para que `this.lastID` e `this.changes` existam.
    run(sql, params = []) {
      return new Promise((resolve, reject) => {
        db.run(sql, params, function respondido(erro) {
          if (erro) reject(erro);
          else resolve({ lastID: this.lastID, changes: this.changes });
        });
      });
    },

    /** Unidade de trabalho atômica: confirma tudo ou desfaz tudo. */
    async transacao(operacao) {
      await api.run('BEGIN');
      try {
        const resultado = await operacao();
        await api.run('COMMIT');
        return resultado;
      } catch (erro) {
        await api.run('ROLLBACK');
        throw erro;
      }
    },
  };
  return api;
}

/** Abre a conexão. Rejeita se o arquivo não puder ser aberto, em vez de falhar em silêncio. */
function conectar(arquivo) {
  return new Promise((resolve, reject) => {
    const db = new sqlite3.Database(arquivo, (erro) => {
      if (erro) reject(erro);
      else resolve(promisificar(db));
    });
  });
}

module.exports = { conectar };
