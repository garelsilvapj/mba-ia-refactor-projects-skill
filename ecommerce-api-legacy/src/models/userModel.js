'use strict';

/** Acesso a dados de usuário. Recebe a conexão por injeção; não conhece HTTP. */
class UserModel {
  constructor(db) {
    this.db = db;
  }

  buscarPorEmail(email) {
    return this.db.get('SELECT * FROM users WHERE email = ?', [email]);
  }

  buscarPorId(id) {
    return this.db.get('SELECT id, name, email FROM users WHERE id = ?', [id]);
  }

  async criar({ nome, email, senhaHash }) {
    const { lastID } = await this.db.run(
      'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
      [nome, email, senhaHash],
    );
    return lastID;
  }

  /** Devolve quantas linhas foram removidas, para o service distinguir 200 de 404. */
  async remover(id) {
    const { changes } = await this.db.run('DELETE FROM users WHERE id = ?', [id]);
    return changes;
  }
}

module.exports = UserModel;
