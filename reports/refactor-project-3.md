# Fase 3 — Projeto 3 (`task-manager-api`)

Saída da Fase 3 da skill `/refactor-arch`, executada após a confirmação `y` no relatório
[`audit-project-3.md`](audit-project-3.md).

Este projeto já tinha `models/`, `routes/`, `services/` e `utils/`. Seguindo
`references/architecture-guidelines.md`, a Fase 3 **não recriou a estrutura**: introduziu as
camadas ausentes e corrigiu o código, movendo o mínimo de arquivos.

```
================================
PHASE 3: REFACTORING COMPLETE
================================
Project: task-manager-api

## New Project Structure
app.py                      app factory create_app() + entry point
config.py                   NOVO: configuração do ambiente + constantes de domínio
database.py                 mantido: instância do SQLAlchemy
models/                     mantidos: hash forte, to_dict sem senha, is_overdue em uso
├── user.py  task.py  category.py
schemas/                    NOVO: validação de entrada com marshmallow
├── base.py  task_schema.py  user_schema.py  category_schema.py
services/                   regra de negócio (antes: uma classe nunca chamada)
├── task_service.py  user_service.py  auth_service.py
├── category_service.py  report_service.py  notification_service.py
controllers/                NOVO: entrada → service → resposta
├── task_controller.py  user_controller.py  category_controller.py
├── report_controller.py  system_controller.py
routes/                     reduzidas a mapeamento URL → controller
├── task_routes.py  user_routes.py  report_routes.py
├── category_routes.py      NOVO: categories saiu do blueprint de relatórios
└── system_routes.py        NOVO
middlewares/                NOVO
├── errors.py               exceções de domínio + handler central
└── auth.py                 tokens assinados, exigência opcional
utils/
├── clock.py                NOVO: fonte única de "agora", sem datetime.utcnow
└── helpers.py              limpo: só o que é realmente usado

## Findings Resolved
  [CRITICAL] Credenciais de SMTP hardcoded  → config.py + .env.example (services/notification_service.py)
  [CRITICAL] SECRET_KEY hardcoded           → config.py lendo o ambiente
  [CRITICAL] Senhas em MD5 sem salt         → werkzeug/scrypt (models/user.py)
  [CRITICAL] Hash exposto nas respostas     → allowlist de campos em to_dict (models/user.py)
  [CRITICAL] Token falso e zero autenticação→ token assinado + require_auth/require_admin (middlewares/auth.py)
  [HIGH]     Regra de negócio nas rotas     → services/ por domínio
  [HIGH]     Camadas cosméticas e código morto → services e helpers passaram a ser usados; o resto removido
  [HIGH]     Acoplamento sem DI             → sessão injetada nos services (app.py)
  [HIGH]     create_all() em tempo de import→ app factory com inicialização explícita
  [HIGH]     except nus engolindo erros     → exceções de domínio + handler central (middlewares/errors.py)
  [HIGH]     Exclusão de usuário sem transação → tarefas e usuário na mesma transação (services/user_service.py)
  [MEDIUM]   N+1 na listagem de tarefas     → selectinload (services/task_service.py)
  [MEDIUM]   N+1 no relatório de resumo     → agregações com GROUP BY (services/report_service.py)
  [MEDIUM]   N+1 na listagem de categorias  → contagem agregada (services/category_service.py)
  [MEDIUM]   datetime.utcnow() (24 usos)    → utils/clock.py com datetime.now(timezone.utc)
  [MEDIUM]   Query.get() legado (14 usos)   → db.session.get() e select()
  [MEDIUM]   Validação frágil gerando 500   → schemas marshmallow, 400 com detalhes
  [MEDIUM]   Lógica de atraso duplicada 5x  → Task.is_overdue() como única definição
  [MEDIUM]   Serialização duplicada         → to_dict único por entidade
  [MEDIUM]   Sem paginação e LIKE sem escape→ limit/offset e escape de curingas
  [LOW]      Constantes repetidas           → config.py como fonte única
  [LOW]      Imports mortos                 → removidos
  [LOW]      print como log                 → logging configurado no factory
  [LOW]      Nomes de uma letra             → nomes descritivos
  [LOW]      Categories no blueprint errado → routes/category_routes.py

## Validation
  ✓ Application boots without errors  (python seed.py && python app.py)
  ✓ 41/41 endpoints respond           (reports/logs/project-3-after.txt)
  ✓ 29/41 responses byte-identical to the baseline
  ✓ Zero erros 500 remaining          (o baseline tinha 2)
  ✓ Zero CRITICAL/HIGH findings remaining

## Intentional Behavior Changes
  - Respostas de usuário e de login não trazem mais o hash da senha.
  - O token do login passou a ser assinado e com validade, no lugar de `fake-jwt-token-<id>`.
  - POST /tasks com priority não numérico devolve 400 em vez de 500.
  - GET /tasks/search?priority=abc devolve 400 em vez de 500.
  - POST /categories com cor fora do formato #RRGGBB devolve 400 em vez de aceitar.
  - Erros de validação trazem o mesmo campo `error` e passaram a incluir `details` por campo.
  - Com REQUIRE_AUTH=true, as rotas protegidas passam a exigir `Authorization: Bearer <token>`
    e as destrutivas exigem papel de administrador. Sem a variável, respondem como antes.

Remaining: CRITICAL: 0 | HIGH: 0 | MEDIUM: 0 | LOW: 0
================================
```

## Verificação

```bash
cd task-manager-api && pip install -r requirements.txt && python seed.py && python app.py
../reports/smoke/project-3.sh http://127.0.0.1:5000
python3 ../reports/smoke/compare.py \
  ../reports/logs/project-3-before.txt ../reports/logs/project-3-after.txt
```

Evidência do modo protegido em [`logs/project-3-after-auth-enabled.txt`](logs/project-3-after-auth-enabled.txt),
capturada com `REQUIRE_AUTH=true`.
