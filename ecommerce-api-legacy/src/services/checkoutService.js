'use strict';

/**
 * Regra de negócio do checkout.
 *
 * Antes: 50 linhas dentro do handler HTTP (AppManager.js:28-78), com cinco níveis de callback,
 * sem transação (falha na linha 55 deixava matrícula órfã) e sem verificar a senha de usuário
 * já existente (linha 74).
 */
const {
  NotFoundError,
  PaymentDeclinedError,
  UnauthorizedError,
  ValidationError,
} = require('../middlewares/errors');

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$/;

class CheckoutService {
  constructor({ db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, gateway, hasher }) {
    this.db = db;
    this.users = userModel;
    this.courses = courseModel;
    this.enrollments = enrollmentModel;
    this.payments = paymentModel;
    this.auditLogs = auditLogModel;
    this.gateway = gateway;
    this.hasher = hasher;
  }

  async executar(dados) {
    const entrada = this._validar(dados);

    const curso = await this.courses.buscarAtivoPorId(entrada.cursoId);
    if (!curso) throw new NotFoundError('Curso não encontrado');

    const usuarioId = await this._resolverUsuario(entrada);

    const { aprovado, status } = this.gateway.autorizar({
      numeroCartao: entrada.cartao,
      valor: curso.price,
    });
    if (!aprovado) throw new PaymentDeclinedError();

    // Matrícula, pagamento e auditoria numa transação: ou tudo, ou nada.
    const matriculaId = await this.db.transacao(async () => {
      const id = await this.enrollments.criar({ usuarioId, cursoId: curso.id });
      await this.payments.criar({ matriculaId: id, valor: curso.price, status });
      await this.auditLogs.registrar(`Checkout curso ${curso.id} por ${usuarioId}`);
      return id;
    });

    return { msg: 'Sucesso', enrollment_id: matriculaId };
  }

  // --- regras ---

  _validar(dados) {
    const corpo = dados || {};
    const nome = corpo.usr;
    const email = corpo.eml;
    const senha = corpo.pwd;
    const cursoId = corpo.c_id;
    const cartao = corpo.card;

    if (!nome || !email || !cursoId || !cartao) {
      throw new ValidationError('Bad Request');
    }
    if (!EMAIL_RE.test(String(email))) {
      throw new ValidationError('E-mail em formato inválido');
    }
    if (!senha) {
      // Antes a senha ausente virava silenciosamente "123456" (AppManager.js:68).
      throw new ValidationError('Senha é obrigatória');
    }
    if (!/^[0-9]{13,19}$/.test(String(cartao))) {
      throw new ValidationError('Número de cartão inválido');
    }
    return { nome, email: String(email), senha: String(senha), cursoId, cartao: String(cartao) };
  }

  async _resolverUsuario({ nome, email, senha }) {
    const existente = await this.users.buscarPorEmail(email);
    if (!existente) {
      return this.users.criar({ nome, email, senhaHash: await this.hasher.gerarHash(senha) });
    }

    // [corrige CRITICAL] antes o fluxo seguia sem conferir a senha de quem já tinha conta.
    const senhaConfere = await this.hasher.verificar(senha, existente.pass);
    if (!senhaConfere) {
      throw new UnauthorizedError('Credenciais inválidas para o e-mail informado');
    }
    return existente.id;
  }
}

module.exports = CheckoutService;
