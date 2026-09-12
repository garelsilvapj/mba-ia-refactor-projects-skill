'use strict';

/** Controller do relatório financeiro. */
class ReportController {
  constructor({ reportService }) {
    this.service = reportService;
  }

  financeiro = async (_req, res) => {
    res.status(200).json(await this.service.financeiro());
  };
}

module.exports = ReportController;
