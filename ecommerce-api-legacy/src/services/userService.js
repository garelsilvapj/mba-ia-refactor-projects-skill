'use strict';

/** Regra de negócio de usuário. */
const { NotFoundError, ValidationError } = require('../middlewares/errors');

class UserService {
  constructor({ userModel }) {
    this.users = userModel;
  }

  /**
   * Antes (AppManager.js:131-137) o erro era ignorado, a resposta era sempre 200 e as matrículas
   * e pagamentos ficavam apontando para um usuário inexistente.
   */
  async remover(id) {
    const usuarioId = Number(id);
    if (!Number.isInteger(usuarioId) || usuarioId <= 0) {
      throw new ValidationError('Id de usuário inválido');
    }

    const removidos = await this.users.remover(usuarioId);
    if (removidos === 0) {
      throw new NotFoundError('Usuário não encontrado');
    }
    return { removido: true, id: usuarioId };
  }
}

module.exports = UserService;
