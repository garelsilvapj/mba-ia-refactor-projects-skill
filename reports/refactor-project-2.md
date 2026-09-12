# Fase 3 — Projeto 2 (`ecommerce-api-legacy`)

Saída da Fase 3 da skill `/refactor-arch`, executada após a confirmação `y` no relatório
[`audit-project-2.md`](audit-project-2.md).

```
================================
PHASE 3: REFACTORING COMPLETE
================================
Project: ecommerce-api-legacy

## New Project Structure
src/
├── server.js               entry point: cria a app e abre a porta
├── app.js                  composition root: monta dependências, middlewares e rotas
├── config/
│   ├── index.js            process.env + enum de status de pagamento
│   └── logger.js           logger com níveis, sem PAN nem segredo
├── models/                 acesso a dados, um arquivo por domínio
│   ├── db.js               driver promisificado + helper de transação
│   ├── schema.js           DDL e seed
│   ├── userModel.js  courseModel.js  enrollmentModel.js
│   ├── paymentModel.js  auditLogModel.js
│   └── reportModel.js      consulta do relatório com JOIN único
├── services/               regra de negócio
│   ├── checkoutService.js  fluxo de checkout, transacional
│   ├── paymentGateway.js   abstração do gateway, injetável
│   ├── passwordHasher.js   scrypt com salt
│   ├── reportService.js
│   └── userService.js
├── controllers/            entrada → service → resposta
│   ├── checkoutController.js  reportController.js  userController.js
│   └── asyncHandler.js     encaminha erro assíncrono ao middleware
├── routes/index.js         URL → controller
└── middlewares/
    ├── errors.js           exceções de domínio
    ├── errorHandler.js     handler central (4 argumentos, registrado por último)
    └── requireAdmin.js     credencial opcional das rotas administrativas

## Findings Resolved
  [CRITICAL] Segredos de produção no código → process.env + .env.example (config/index.js)
  [CRITICAL] God Class AppManager           → config, models, services, controllers, routes
  [CRITICAL] Cartão e chave no log          → logger registra só os 4 últimos dígitos (services/paymentGateway.js)
  [CRITICAL] Hash caseiro badCrypto         → scrypt com salt (services/passwordHasher.js)
  [CRITICAL] Senha do seed em texto puro    → hash gerado no seed (models/schema.js)
  [CRITICAL] Relatório financeiro público   → credencial opcional via ADMIN_TOKEN (middlewares/requireAdmin.js)
  [CRITICAL] Checkout sem conferir a senha  → verificação antes de matricular (services/checkoutService.js)
  [HIGH]     Regra de checkout no handler   → checkoutService.js, transacional
  [HIGH]     Autorização de pagamento inline→ PaymentGateway injetável (services/paymentGateway.js)
  [HIGH]     Acoplamento sem DI             → dependências montadas em src/app.js
  [HIGH]     Estado global mutável          → receita derivada do banco; cache de módulo removido
  [HIGH]     initDb sem checagem de erro    → inicialização aguardada e com erro propagado
  [MEDIUM]   N+1 no relatório               → JOIN único (models/reportModel.js)
  [MEDIUM]   Coordenação por contadores     → async/await; ordem determinística
  [MEDIUM]   DELETE mentindo no status      → 404 quando nada foi removido (services/userService.js)
  [MEDIUM]   Validação mínima               → validação na borda (services/checkoutService.js)
  [MEDIUM]   Erros ad-hoc em 6 pontos       → errorHandler central
  [MEDIUM]   APIs e padrões deprecated      → driver promisificado, `self` removido, crypto nativo
  [MEDIUM]   Configuração fixa              → config/index.js
  [LOW]      Nomes crípticos                → nomes completos internamente
  [LOW]      Magic numbers e status soltos  → PaymentStatus congelado (config/index.js)
  [LOW]      DDL e seed embutidos           → models/schema.js
  [LOW]      Sem scripts de apoio           → npm scripts + smoke test documentado

## Validation
  ✓ Application boots without errors  (npm start)
  ✓ 12/12 endpoints respond           (reports/logs/project-2-after.txt)
  ✓ api.http funciona sem configuração alguma
  ✓ Zero CRITICAL/HIGH findings remaining

## Intentional Behavior Changes
  - Checkout com e-mail já cadastrado e senha incorreta devolve 401 em vez de matricular.
  - DELETE /api/users/<id> inexistente devolve 404 em vez de 200 com texto de sucesso.
  - Respostas de erro passaram de texto puro para JSON `{"error": "..."}`, com a mesma mensagem.
  - A ordem dos cursos no relatório passou a ser estável; antes variava entre chamadas.
  - Com ADMIN_TOKEN definido, o relatório financeiro e a exclusão de usuário exigem o cabeçalho
    X-Admin-Token. Sem a variável, respondem como antes.

Remaining: CRITICAL: 0 | HIGH: 0 | MEDIUM: 1 | LOW: 0
  [MEDIUM] Matrículas e pagamentos órfãos após excluir um usuário. As chaves estrangeiras estão
  declaradas em models/schema.js, mas a checagem do SQLite não foi ativada: ativá-la mudaria os
  números históricos do relatório financeiro. A escolha entre exclusão em cascata e exclusão
  lógica é decisão de produto, não de refatoração.
================================
```

## Verificação

```bash
cd ecommerce-api-legacy && npm install && npm start
../reports/smoke/project-2.sh http://127.0.0.1:3000
python3 ../reports/smoke/compare.py \
  ../reports/logs/project-2-before.txt ../reports/logs/project-2-after.txt
```

Evidência do modo protegido em [`logs/project-2-after-auth-enabled.txt`](logs/project-2-after-auth-enabled.txt),
capturada com `ADMIN_TOKEN` definido.
