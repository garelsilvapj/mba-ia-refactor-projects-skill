'use strict';

/**
 * Exceções de domínio.
 *
 * Antes cada handler devolvia `res.status(5xx).send("texto")` por conta própria
 * (AppManager.js:38, 41, 51, 55, 70, 84). Agora as camadas lançam e um único middleware traduz.
 */
class AppError extends Error {
  constructor(mensagem, status = 500) {
    super(mensagem);
    this.name = this.constructor.name;
    this.status = status;
  }
}

class ValidationError extends AppError {
  constructor(mensagem) {
    super(mensagem, 400);
  }
}

class UnauthorizedError extends AppError {
  constructor(mensagem) {
    super(mensagem, 401);
  }
}

class ForbiddenError extends AppError {
  constructor(mensagem) {
    super(mensagem, 403);
  }
}

class NotFoundError extends AppError {
  constructor(mensagem) {
    super(mensagem, 404);
  }
}

class PaymentDeclinedError extends AppError {
  constructor(mensagem = 'Pagamento recusado') {
    super(mensagem, 400);
  }
}

module.exports = {
  AppError,
  ValidationError,
  UnauthorizedError,
  ForbiddenError,
  NotFoundError,
  PaymentDeclinedError,
};
