'use strict';

/** Acesso a dados de matrícula. */
class EnrollmentModel {
  constructor(db) {
    this.db = db;
  }

  async criar({ usuarioId, cursoId }) {
    const { lastID } = await this.db.run(
      'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
      [usuarioId, cursoId],
    );
    return lastID;
  }
}

module.exports = EnrollmentModel;
