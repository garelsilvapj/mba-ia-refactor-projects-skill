# Análise de projeto (Fase 1)

Heurísticas para descobrir **o que é** o projeto antes de auditá-lo. Tudo aqui é somente leitura.

## 1. Delimitar o que é código-fonte

Sempre exclua da contagem e das buscas:

```
node_modules/  .venv/  venv/  env/  __pycache__/  .git/  dist/  build/  target/
vendor/  coverage/  .next/  .pytest_cache/  *.lock  *-lock.json  *.min.js  migrations/versions/
```

Comando de referência:

```bash
find . -type f \( -name '*.py' -o -name '*.js' -o -name '*.ts' -o -name '*.php' -o -name '*.rb' -o -name '*.go' -o -name '*.java' \) \
  -not -path '*/node_modules/*' -not -path '*/.venv/*' -not -path '*/__pycache__/*' -not -path '*/.git/*' \
  | sort
wc -l <arquivos>   # linhas por arquivo e total
```

"Source files: N analyzed" é essa contagem. Não conte lockfiles, testes gerados, nem o próprio
diretório `.claude/`.

## 2. Linguagem e framework pelo manifesto

| Manifesto encontrado | Linguagem | Onde ler a versão do framework |
|---|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` | Python | linha `flask==`, `django==`, `fastapi==` |
| `package.json` | JavaScript / TypeScript | `dependencies.express`, `.nestjs/core`, `.next`, `.fastify` |
| `composer.json` | PHP | `require.laravel/framework`, `symfony/*` |
| `go.mod` | Go | `github.com/gin-gonic/gin`, `github.com/labstack/echo` |
| `Gemfile` | Ruby | `gem 'rails'`, `gem 'sinatra'` |
| `pom.xml`, `build.gradle` | Java / Kotlin | `spring-boot-starter-web` |
| `*.csproj` | C# | `Microsoft.AspNetCore.*` |

Se o manifesto não existir ou estiver incompleto, confirme pelos imports:

```bash
grep -rn "^from flask\|^import flask\|require('express')\|from fastapi\|use Illuminate" --include='*.py' --include='*.js' .
```

**Regra:** a versão relatada é a do manifesto. Se o manifesto usar faixa (`^4.18.2`), relate a
faixa e, se o lockfile existir, a versão resolvida.

### Dependências que mudam a auditoria

| Dependência | O que implica |
|---|---|
| `flask-sqlalchemy`, `sequelize`, `prisma`, `mongoose`, `eloquent`, `activerecord` | Há ORM: SQL injection é improvável, mas N+1 é provável |
| `sqlite3`, `psycopg2`, `mysql2`, `pg` (driver puro) | SQL escrito à mão: procure concatenação em queries |
| `flask-cors`, `cors` | Verifique se a origem é `*` |
| `marshmallow`, `pydantic`, `joi`, `zod`, `class-validator` | Há biblioteca de validação — se estiver declarada e não usada, é finding |
| `python-dotenv`, `dotenv` | Config por ambiente é esperada — se nada lê `env`, é finding |
| `bcrypt`, `argon2`, `werkzeug.security` | Hash de senha adequado. A ausência com `hashlib.md5`/base64 é CRITICAL |

**Dependência declarada e nunca importada** é um achado de qualidade (LOW/MEDIUM). Verifique:

```bash
grep -rn "import marshmallow\|from marshmallow" --include='*.py' .   # nada? dependência morta
```

## 3. Banco de dados

| Sinal | Conclusão |
|---|---|
| `CREATE TABLE`, `executescript`, `db.run("CREATE ...")` | Schema no código; extraia os nomes das tabelas |
| Classes com `db.Model`, `sequelize.define`, `mongoose.Schema` | Tabelas/coleções são os modelos do ORM |
| `sqlite:///arquivo.db`, `:memory:` | SQLite; `:memory:` significa dados voláteis a cada boot |
| `DATABASE_URL`, `postgres://`, `mysql://` | Banco externo; a app pode não subir sem ele |
| Pasta `migrations/` | Schema versionado; leia a última migration |

```bash
grep -rniE "create table( if not exists)? +([a-z_]+)" --include='*.py' --include='*.js' --include='*.sql' .
grep -rn "__tablename__\|db.Model\|sequelize.define\|mongoose.model" --include='*.py' --include='*.js' .
```

Registre onde o banco é inicializado e **se há seed** — a validação da Fase 3 depende de dados.

## 4. Domínio

O domínio sai do cruzamento de três fontes:

1. **Tabelas/modelos** — `produtos, usuarios, pedidos, itens_pedido` → e-commerce.
   `users, courses, enrollments, payments` → plataforma de cursos (LMS) com pagamento.
   `users, tasks, categories` → gerenciador de tarefas.
2. **Rotas** — `/checkout`, `/reports/vendas`, `/tasks/stats` dizem o que o sistema faz.
3. **README do projeto**, se houver.

Escreva o domínio em uma linha, citando as entidades: `"E-commerce API (produtos, pedidos,
usuários, relatório de vendas)"`.

## 5. Inventário de endpoints (obrigatório)

Esta lista é o **contrato** que a Fase 3 deve preservar. Extraia método + rota + `arquivo:linha`.

| Framework | Como listar |
|---|---|
| Flask | `grep -rn "@app.route\|@bp.route\|@[a-z_]*_bp.route\|add_url_rule" --include='*.py' .` |
| FastAPI | `grep -rn "@app.get\|@app.post\|@router\." --include='*.py' .` |
| Django | ler `urls.py` (`path(`, `re_path(`) |
| Express | `grep -rn "app\.\(get\|post\|put\|patch\|delete\)\|router\.\(get\|post\|put\|patch\|delete\)" --include='*.js' .` |
| NestJS | `grep -rn "@Get(\|@Post(\|@Controller(" --include='*.ts' .` |
| Laravel | ler `routes/web.php` e `routes/api.php` |
| Rails | ler `config/routes.rb` |

Atenção a rotas registradas fora do arquivo de rotas (registro dinâmico via `add_url_rule`,
métodos de classe que recebem `app`, handlers inline no entry point). Se existir um arquivo
`api.http`, `*.rest`, collection do Postman ou `curl` no README, use-o como fonte adicional de
requisições de exemplo com corpo válido.

## 6. Classificar a arquitetura atual

| Observação | Classificação a relatar |
|---|---|
| Tudo em 1-5 arquivos na raiz, roteamento + SQL + regra juntos | `Monolítica — sem separação de camadas` |
| Uma classe/módulo central que faz tudo | `Monolítica — God Class <Nome> concentra DB, rotas e regra` |
| Existem pastas `models/`, `routes/`, mas a regra está nas rotas | `Camadas parciais — pastas existem, mas a separação é cosmética` |
| Controllers finos, services, repositórios, config, error handler | `MVC/em camadas — avaliar só melhorias pontuais` |

Para decidir, responda por escrito:

- **Onde está a regra de negócio?** (cálculo, decisão, validação de domínio)
- **Onde está o acesso a dados?** (SQL, ORM)
- **Onde está o roteamento?**
- Se as três respostas apontam para o mesmo arquivo → monólito/God Class.
- Se a regra está no mesmo arquivo do roteamento → camadas parciais.

## 7. Como a aplicação sobe

Antes de fechar a Fase 1, registre:

- **Entry point** e comando (`python app.py`, `npm start`, `flask run`, `uvicorn main:app`).
- **Porta** e se está hardcoded.
- **Variáveis de ambiente** necessárias (`grep -rn "os.environ\|process.env"`). Nenhuma?
  Isso já é sinal de configuração hardcoded.
- **Seed/migrations** necessários antes do primeiro request.
- **Serviços externos** (SMTP, gateway de pagamento, fila) que podem impedir o boot.

Sem essa informação a Fase 3 não consegue capturar o baseline.

## Saída da Fase 1

Preencha o bloco `PHASE 1: PROJECT ANALYSIS` de `report-template.md` com os itens acima.
Guarde o inventário de endpoints e o comando de boot para as fases seguintes.
