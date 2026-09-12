"""Entry point da API da Loja.

Toda a aplicação vive em `src/` (config, models, services, controllers, views, middlewares).
Este arquivo apenas cria a app e a sobe — é o ponto de entrada, não o lugar das rotas.

Antes da refatoração, este arquivo declarava 19 rotas, implementava três handlers inline
(incluindo dois endpoints administrativos sem autenticação) e fixava a SECRET_KEY no código.
"""
from src.app import create_app
from src.config.settings import Config

app = create_app()

if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
