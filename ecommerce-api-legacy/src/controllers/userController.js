'use strict';

/** Controller de usuário. */
class UserController {
  constructor({ userService }) {
    this.service = userService;
  }

  remover = async (req, res) => {
    res.status(200).json(await this.service.remover(req.params.id));
  };
}

module.exports = UserController;
