'use strict';

/** Trilha de auditoria. */
class AuditLogModel {
  constructor(db) {
    this.db = db;
  }

  registrar(acao) {
    return this.db.run(
      "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
      [acao],
    );
  }
}

module.exports = AuditLogModel;
