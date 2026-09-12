'use strict';

/**
 * Consulta do relatório financeiro.
 *
 * Antes (AppManager.js:83-127) eram 1 + N + 2×M consultas coordenadas por contadores manuais,
 * com ordem não determinística. Agora é uma consulta só, com JOIN e ordenação explícita.
 */
const SQL = `
  SELECT c.id            AS course_id,
         c.title         AS course_title,
         e.id            AS enrollment_id,
         u.name          AS student_name,
         p.amount        AS paid,
         p.status        AS payment_status
  FROM courses c
  LEFT JOIN enrollments e ON e.course_id = c.id
  LEFT JOIN users u       ON u.id = e.user_id
  LEFT JOIN payments p    ON p.enrollment_id = e.id
  ORDER BY c.id, e.id
`;

class ReportModel {
  constructor(db) {
    this.db = db;
  }

  linhasFinanceiras() {
    return this.db.all(SQL);
  }
}

module.exports = ReportModel;
