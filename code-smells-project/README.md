# code-smells-project

API de E-commerce em Python/Flask, **refatorada para MVC** pela skill `/refactor-arch`.
O relatório de auditoria que originou a refatoração está em `reports/audit-project-1.md`.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env        # opcional: sem .env a app sobe com defaults de desenvolvimento
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado no primeiro
boot com produtos e usuários de exemplo. Usuários do seed: `admin@loja.com` / `admin123`,
`joao@email.com` / `123456`, `maria@email.com` / `senha123` (as senhas ficam no banco em hash).

## Estrutura

```
app.py                      entry point (sobe a app criada pelo factory)
src/
├── app.py                  composition root: create_app() liga as camadas
├── config/settings.py      configuração vinda do ambiente + constantes de domínio
├── models/                 acesso a dados, uma classe por domínio
│   ├── db.py               conexão por requisição, schema e seed
│   ├── produto_model.py
│   ├── usuario_model.py
│   └── pedido_model.py
├── services/               regra de negócio
│   ├── produto_service.py
│   ├── usuario_service.py  inclui autenticação com hash de senha
│   ├── pedido_service.py
│   ├── relatorio_service.py
│   └── notificacao_service.py
├── controllers/            fluxo HTTP: entrada → service → resposta
├── views/routes.py         Blueprints: URL → controller
└── middlewares/errors.py   exceções de domínio + handler de erro centralizado
```

Regra de dependência: `views → controllers → services → models → banco`. Nenhum model ou
service conhece `request`/`jsonify`.

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | índice da API |
| GET | `/health` | estado do serviço e contagens |
| GET | `/produtos` | lista produtos |
| GET | `/produtos/busca?q=&categoria=&preco_min=&preco_max=` | busca com filtros |
| GET | `/produtos/<id>` | detalhe |
| POST | `/produtos` | cria |
| PUT | `/produtos/<id>` | atualiza |
| DELETE | `/produtos/<id>` | remove |
| GET | `/usuarios` | lista usuários (sem senha) |
| GET | `/usuarios/<id>` | detalhe |
| POST | `/usuarios` | cria usuário |
| POST | `/login` | autentica |
| POST | `/pedidos` | cria pedido |
| GET | `/pedidos` | lista todos |
| GET | `/pedidos/usuario/<id>` | pedidos de um usuário |
| PUT | `/pedidos/<id>/status` | atualiza status |
| GET | `/relatorios/vendas` | relatório de vendas |
| POST | `/admin/reset-db` | esvazia as tabelas (credencial opcional) |
| POST | `/admin/query` | retirada por segurança, responde 410 |

## Mudanças de comportamento intencionais

Correções de segurança e de corretude aplicadas na Fase 3. **Todas as 19 rotas originais
continuam registradas e respondendo**; o resto responde exatamente como antes (ver
`reports/logs/project-1-before.txt` e `-after.txt`).

| Antes | Agora |
|---|---|
| `POST /admin/query` executava SQL arbitrário sem auth | rota responde 410 com a explicação |
| `POST /admin/reset-db` apagava o banco sem auth | segue funcionando; com `ADMIN_TOKEN` exige credencial |
| login com `' OR '1'='1` autenticava como admin (200) | 401 |
| busca com payload de injeção devolvia 500 com erro do SQLite | 200, texto tratado como literal |
| `GET /usuarios` devolvia o campo `senha` em texto puro | campo não existe mais na resposta |
| `GET /health` devolvia `secret_key`, `db_path`, `debug` | só estado e contagens |
| preço não numérico causava 500 | 400 com mensagem de validação |
| respostas de erro variavam de formato | envelope único `{"erro": ..., "sucesso": false}` |
