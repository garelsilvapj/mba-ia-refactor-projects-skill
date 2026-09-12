"""Notificações.

Antes esta classe tinha as credenciais de SMTP no construtor (host, usuário e senha literais),
guardava as notificações em uma lista de instância e nunca era chamada por rota nenhuma.

Agora as credenciais vêm da configuração, o envio é opcional (sem SMTP configurado a notificação
só é registrada em log) e o serviço é injetado no TaskService pelo composition root.
"""
import logging
import smtplib

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, config):
        self.config = config

    @property
    def habilitado(self):
        return bool(self.config.SMTP_HOST and self.config.SMTP_USER)

    def notificar_task_atribuida(self, usuario, tarefa):
        assunto = f"Nova task atribuída: {tarefa.title}"
        corpo = (
            f"Olá {usuario.name},\n\n"
            f"A task '{tarefa.title}' foi atribuída a você.\n\n"
            f"Prioridade: {tarefa.priority}\nStatus: {tarefa.status}"
        )
        self._enviar(usuario.email, assunto, corpo, evento="task_assigned", task_id=tarefa.id)

    def notificar_task_atrasada(self, usuario, tarefa):
        assunto = f"Task atrasada: {tarefa.title}"
        corpo = (
            f"Olá {usuario.name},\n\n"
            f"A task '{tarefa.title}' está atrasada!\n\nData limite: {tarefa.due_date}"
        )
        self._enviar(usuario.email, assunto, corpo, evento="task_overdue", task_id=tarefa.id)

    def _enviar(self, destinatario, assunto, corpo, evento, task_id):
        if not self.habilitado:
            logger.info("notificação registrada (SMTP desativado)", extra={"evento": evento, "task_id": task_id})
            return False
        try:
            with smtplib.SMTP(self.config.SMTP_HOST, self.config.SMTP_PORT) as servidor:
                servidor.starttls()
                servidor.login(self.config.SMTP_USER, self.config.SMTP_PASSWORD)
                servidor.sendmail(
                    self.config.SMTP_USER, destinatario, f"Subject: {assunto}\n\n{corpo}"
                )
            logger.info("notificação enviada", extra={"evento": evento, "task_id": task_id})
            return True
        except (smtplib.SMTPException, OSError) as erro:
            # Exceção específica e log com contexto — antes era `except Exception` com print.
            logger.warning("falha ao enviar notificação: %s", erro, extra={"evento": evento})
            return False
