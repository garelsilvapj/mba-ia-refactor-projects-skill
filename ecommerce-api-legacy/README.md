# ecommerce-api-legacy

LMS API com fluxo de checkout, em Node.js/Express, **refatorada para MVC** pela skill
`/refactor-arch`. O relatório de auditoria está em `reports/audit-project-2.md`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite continua em memória e é populado no
boot. Exemplos de requisições em `api.http`.

Sem configuração alguma, os três endpoints respondem como antes e o `api.http` funciona. Para
proteger as rotas administrativas, copie `.env.example` para `.env` e defina `ADMIN_TOKEN`:
a partir daí elas exigem o cabeçalho `X-Admin-Token`.

## Estrutura

```
src/
├── server.js               entry point: cria a app e abre a porta
├── app.js                  composition root: monta dependências, middlewares e rotas
├── config/
│   ├── index.js            configuração via process.env + enum de status de pagamento
│   └── logger.js           logger com níveis (substitui console.log)
├── models/                 acesso a dados, um arquivo por domínio
│   ├── db.js               driver promisificado + helper de transação
│   ├── schema.js           DDL e seed
│   ├── userModel.js  courseModel.js  enrollmentModel.js
│   ├── paymentModel.js  auditLogModel.js
│   └── reportModel.js      consulta do relatório com JOIN único
├── services/               regra de negócio
│   ├── checkoutService.js  fluxo de checkout, transacional
│   ├── paymentGateway.js   abstração do gateway (injetável)
│   ├── passwordHasher.js   scrypt com salt
│   └── reportService.js    userService.js
├── controllers/            entrada → service → resposta
├── routes/index.js         URL → controller
└── middlewares/
    ├── errors.js           exceções de domínio
    ├── errorHandler.js     handler central (4 argumentos, registrado por último)
    └── requireAdmin.js     autorização das rotas administrativas
```

`src/app.js` exporta a app sem `listen`, o que permite criá-la em teste com um banco e um
gateway falsos.

## Endpoints

| Método | Rota | Autenticação | Descrição |
|---|---|---|---|
| POST | `/api/checkout` | senha do usuário, se o e-mail já existir | matrícula + pagamento |
| GET | `/api/admin/financial-report` | `X-Admin-Token`, se `ADMIN_TOKEN` estiver definido | receita e alunos por curso |
| DELETE | `/api/users/:id` | `X-Admin-Token`, se `ADMIN_TOKEN` estiver definido | remove usuário |

## Mudanças de comportamento intencionais

Correções aplicadas na Fase 3 (comparação completa em `reports/logs/project-2-before.txt` e
`-after.txt`).

| Antes | Agora |
|---|---|
| não havia como proteger o relatório financeiro nem a exclusão de usuário | proteção disponível: com `ADMIN_TOKEN` definido, exigem `X-Admin-Token` |
| checkout com e-mail existente ignorava a senha | 401 quando a senha não confere |
| `DELETE /api/users/999` devolvia 200 | 404, com verificação de linhas afetadas |
| erros respondiam texto puro | JSON `{"error": "..."}` com a mesma mensagem |
| ordem dos cursos no relatório variava entre chamadas | ordem estável por id |
| número do cartão e chave `pk_live` iam para o log | log registra só os quatro últimos dígitos |
| senha do seed em texto puro e hash caseiro | scrypt com salt por usuário |

## Ponto deliberadamente não alterado

A exclusão de usuário continua deixando matrículas e pagamentos existentes apontando para o id
removido, e o relatório segue exibindo `Unknown` no lugar do aluno. As chaves estrangeiras estão
declaradas no schema, mas a checagem do SQLite não foi ativada: ativá-la mudaria os números
históricos do relatório financeiro, o que vai além de uma refatoração. A decisão entre exclusão
em cascata e exclusão lógica é de produto e está registrada como pendência MEDIUM no relatório.
