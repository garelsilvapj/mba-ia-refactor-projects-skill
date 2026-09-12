# task-manager-api

API de Task Manager em Python/Flask, **refatorada** pela skill `/refactor-arch`. Este projeto já
tinha pastas `models/`, `routes/`, `services/` e `utils/`, então a Fase 3 não recriou a estrutura:
introduziu as camadas que faltavam (config, controllers, services reais, schemas, middlewares) e
corrigiu os problemas de segurança e de qualidade. O relatório está em
`reports/audit-project-3.md`.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env        # defina SECRET_KEY para manter os tokens válidos entre reinícios
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite com 3 usuários,
4 categorias e 10 tarefas — rode-o antes do primeiro boot.

Usuários do seed: `joao@email.com` / `1234` (admin), `maria@email.com` / `abcd`,
`pedro@email.com` / `pass`. As senhas ficam no banco com hash forte.

## Autenticação

O login devolve um token assinado, com validade. A **exigência** do token é opcional: por
padrão (`REQUIRE_AUTH=false`) a API responde exatamente como antes da refatoração, e todos os
22 endpoints continuam acessíveis. Definindo `REQUIRE_AUTH=true` no `.env`, as rotas protegidas
passam a exigir o cabeçalho `Authorization: Bearer <token>`.

```bash
TOKEN=$(curl -s -X POST localhost:5000/login -H 'Content-Type: application/json' \
  -d '{"email":"joao@email.com","password":"1234"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')

curl -H "Authorization: Bearer $TOKEN" localhost:5000/tasks
```

Com `REQUIRE_AUTH=true`:

| Acesso | Rotas |
|---|---|
| Público | `GET /`, `GET /health`, `POST /login`, `POST /users` |
| Autenticado | leitura e escrita de tasks, users e categories, `GET /reports/user/<id>` |
| Administrador | `DELETE` de tasks, users e categories, `GET /reports/summary` |

## Estrutura

```
app.py                   app factory create_app() + entry point
config.py                configuração via ambiente + constantes de domínio
database.py              instância do SQLAlchemy
models/                  entidades; Task.is_overdue() é a única definição de "atrasada"
schemas/                 validação de entrada com marshmallow
services/                regra de negócio: task, user, auth, category, report, notification
controllers/             entrada → service → resposta
routes/                  apenas mapeamento URL → controller (+ blueprint próprio de categories)
middlewares/
├── errors.py            exceções de domínio + handler central
└── auth.py              tokens assinados, require_auth / require_admin
utils/
├── clock.py             fonte única de "agora" (sem datetime.utcnow)
└── helpers.py           auxiliares realmente usados
```

## Mudanças de comportamento intencionais

Comparação completa em `reports/logs/project-3-before.txt` e `-after.txt`: das 41 requisições do
smoke test, **41 respondem** e 29 são idênticas ao comportamento anterior.

| Antes | Agora |
|---|---|
| não havia autenticação possível | com `REQUIRE_AUTH=true`, as rotas protegidas exigem token |
| login devolvia `fake-jwt-token-<id>` | token assinado com a SECRET_KEY, com validade |
| respostas de usuário e de login traziam o hash da senha | campo removido da serialização |
| senhas em MD5 sem salt | hash forte do werkzeug (scrypt) |
| `priority` não numérico causava 500 | 400 com a mensagem de validação |
| `GET /tasks/search?priority=abc` causava 500 | 400 |
| categoria aceitava qualquer cor | 400 para cor fora do formato `#RRGGBB` |
| erro de validação trazia só `error` | mesmo `error`, mais um campo `details` por campo |
| cadastro público podia escolher o próprio papel | com `REQUIRE_AUTH=true`, o papel só é aceito de um admin |

## Melhorias sem mudança de contrato

- `GET /tasks` deixou de fazer duas consultas por tarefa (carregamento antecipado).
- `GET /reports/summary` deixou de fazer uma consulta por usuário e nove contagens separadas.
- `GET /categories` e `GET /users` agregam a contagem no banco, em uma consulta.
- `GET /tasks/search` aceita `limit` e `offset` e escapa `%`/`_` no termo de busca.
- `datetime.utcnow()` (deprecated) e `Query.get()` (legado do SQLAlchemy 1.x) foram substituídos.
- As tarefas de um usuário excluído são removidas na mesma transação.
