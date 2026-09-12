# Fase 3 — Projeto 1 (`code-smells-project`)

Saída da Fase 3 da skill `/refactor-arch`, executada após a confirmação `y` no relatório
[`audit-project-1.md`](audit-project-1.md).

```
================================
PHASE 3: REFACTORING COMPLETE
================================
Project: code-smells-project

## New Project Structure
app.py                      entry point (sobe a app criada pelo factory)
src/
├── app.py                  composition root: create_app() liga as camadas
├── config/settings.py      configuração do ambiente + constantes de domínio
├── models/                 acesso a dados, um módulo por domínio
│   ├── db.py               conexão por requisição, schema e seed
│   ├── produto_model.py
│   ├── usuario_model.py
│   └── pedido_model.py
├── services/               regra de negócio
│   ├── produto_service.py
│   ├── usuario_service.py
│   ├── pedido_service.py
│   ├── relatorio_service.py
│   ├── notificacao_service.py
│   └── admin_service.py
├── controllers/            fluxo HTTP: entrada → service → resposta
│   ├── produto_controller.py
│   ├── usuario_controller.py
│   ├── pedido_controller.py
│   ├── sistema_controller.py
│   └── admin_controller.py
├── views/routes.py         Blueprints: URL → controller
└── middlewares/
    ├── errors.py           exceções de domínio + handler central
    └── admin.py            credencial opcional das rotas administrativas

## Findings Resolved
  [CRITICAL] Endpoint de SQL arbitrário     → rota responde 410 com explicação (controllers/admin_controller.py)
  [CRITICAL] Reset de base sem autenticação → credencial opcional via ADMIN_TOKEN (middlewares/admin.py)
  [CRITICAL] SQL Injection (19 pontos)      → queries parametrizadas (models/*.py)
  [CRITICAL] Credenciais hardcoded          → variáveis de ambiente (config/settings.py, .env.example)
  [CRITICAL] Senhas em texto puro           → hash na escrita e allowlist na saída (models/usuario_model.py)
  [CRITICAL] Chave secreta no /health       → resposta só com estado do serviço (controllers/sistema_controller.py)
  [CRITICAL] God Module de 4 domínios       → models por domínio + services (models/, services/)
  [HIGH]     Regra de negócio no controller → produto_service.py e pedido_service.py
  [HIGH]     Cálculo de relatório no model  → relatorio_service.py
  [HIGH]     Acoplamento sem DI             → dependências injetadas no composition root (src/app.py)
  [HIGH]     Conexão global entre threads   → conexão por requisição (models/db.py)
  [HIGH]     Pedido sem transação           → BEGIN/COMMIT com decremento condicional (models/pedido_model.py)
  [MEDIUM]   N+1 na listagem de pedidos     → JOIN único (models/pedido_model.py)
  [MEDIUM]   Validação ausente ou frágil    → validação na borda, 400 no lugar de 500 (services/produto_service.py)
  [MEDIUM]   17 try/except duplicados       → handler central (middlewares/errors.py)
  [MEDIUM]   Duplicação de queries          → listagem parametrizada e serialização única
  [MEDIUM]   CORS liberado                  → origens por configuração (config/settings.py)
  [MEDIUM]   Filtros descartando zero       → comparação com `is not None` (models/produto_model.py)
  [LOW]      Magic numbers                  → constantes nomeadas (config/settings.py)
  [LOW]      print como log                 → logging configurado + notificacao_service.py
  [LOW]      Sombreamento de builtin        → parâmetros renomeados
  [LOW]      Imports mortos e envelope      → imports removidos, envelope de erro único

## Validation
  ✓ Application boots without errors  (python app.py)
  ✓ 35/35 endpoints respond           (reports/logs/project-1-after.txt)
  ✓ 20/35 responses byte-identical to the baseline
  ✓ Zero CRITICAL/HIGH findings remaining

## Intentional Behavior Changes
  - POST /admin/query responde 410 em vez de executar SQL arbitrário. A rota segue registrada,
    com mensagem explícita; não há forma segura de mantê-la funcional.
  - POST /login com payload de injeção devolve 401 em vez de autenticar como administrador.
  - GET /produtos/busca com payload de injeção devolve 200 tratando o texto como literal, em
    vez de 500 com a mensagem do parser SQL.
  - POST /produtos com preço não numérico devolve 400 em vez de 500.
  - GET /usuarios e GET /usuarios/<id> não trazem mais o campo `senha`.
  - GET /health não traz mais secret_key, db_path, debug e ambiente.
  - As respostas de erro passaram a incluir `"sucesso": false` de forma consistente.
  - Com ADMIN_TOKEN definido, POST /admin/reset-db passa a exigir o cabeçalho X-Admin-Token.
    Sem a variável, responde como antes.

Remaining: CRITICAL: 0 | HIGH: 0 | MEDIUM: 0 | LOW: 0
================================
```

## Verificação

```bash
cd code-smells-project && pip install -r requirements.txt && python app.py
../reports/smoke/project-1.sh http://127.0.0.1:5000
python3 ../reports/smoke/compare.py \
  ../reports/logs/project-1-before.txt ../reports/logs/project-1-after.txt
```
