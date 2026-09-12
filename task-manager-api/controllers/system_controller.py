"""Controller das rotas de sistema (índice e health check)."""
from flask import current_app, jsonify

from utils.clock import now_utc_naive


class SystemController:
    def index(self):
        return jsonify({"message": "Task Manager API", "version": "1.0"}), 200

    def health(self):
        return jsonify({"status": "ok", "timestamp": str(now_utc_naive())}), 200
