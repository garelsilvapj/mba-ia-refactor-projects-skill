'use strict';

/** Acesso a dados de pagamento. */
class PaymentModel {
  constructor(db) {
    this.db = db;
  }

  async criar({ matriculaId, valor, status }) {
    const { lastID } = await this.db.run(
      'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
      [matriculaId, valor, status],
    );
    return lastID;
  }
}

module.exports = PaymentModel;
