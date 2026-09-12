"""Controller de relatórios."""
from flask import jsonify


class ReportController:
    def __init__(self, report_service):
        self.service = report_service

    def resumo(self):
        return jsonify(self.service.resumo()), 200

    def por_usuario(self, user_id):
        return jsonify(self.service.por_usuario(user_id)), 200
