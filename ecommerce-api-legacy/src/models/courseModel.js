'use strict';

/** Acesso a dados de curso. */
class CourseModel {
  constructor(db) {
    this.db = db;
  }

  buscarAtivoPorId(id) {
    return this.db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]);
  }

  listar() {
    return this.db.all('SELECT * FROM courses ORDER BY id');
  }
}

module.exports = CourseModel;
