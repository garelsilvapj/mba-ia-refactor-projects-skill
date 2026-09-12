'use strict';

/** Controller de checkout: entrada → service → resposta. Sem regra, sem SQL. */
class CheckoutController {
  constructor({ checkoutService }) {
    this.service = checkoutService;
  }

  criar = async (req, res) => {
    const resultado = await this.service.executar(req.body);
    res.status(200).json(resultado);
  };
}

module.exports = CheckoutController;
