'use strict';

/**
 * Monta o relatório financeiro a partir de uma única consulta com JOIN.
 *
 * Antes a agregação acontecia no handler, somando receita em variáveis compartilhadas dentro de
 * callbacks aninhados (AppManager.js:89-127), com ordem de saída não determinística.
 */
const { PaymentStatus } = require('../config');

class ReportService {
  constructor({ reportModel }) {
    this.reports = reportModel;
  }

  async financeiro() {
    const linhas = await this.reports.linhasFinanceiras();

    const porCurso = new Map();
    for (const linha of linhas) {
      if (!porCurso.has(linha.course_id)) {
        porCurso.set(linha.course_id, { course: linha.course_title, revenue: 0, students: [] });
      }
      if (linha.enrollment_id === null) continue;

      const curso = porCurso.get(linha.course_id);
      if (linha.payment_status === PaymentStatus.PAID) {
        curso.revenue += linha.paid;
      }
      curso.students.push({
        student: linha.student_name || 'Unknown',
        paid: linha.paid ?? 0,
      });
    }
    // Ordem estável por id do curso e da matrícula (garantida pelo ORDER BY da query).
    return [...porCurso.values()];
  }
}

module.exports = ReportService;
