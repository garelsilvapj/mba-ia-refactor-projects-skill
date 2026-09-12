# Skill `refactor-arch` — Auditoria e Refatoração Arquitetural Automatizada

Resposta ao desafio de criação de Skills. A skill `refactor-arch` audita qualquer codebase,
classifica os achados por severidade com arquivo e linha, gera um relatório estruturado e
refatora o projeto para MVC, validando que a aplicação continua funcionando.

Foi executada nos três projetos do repositório base: dois em Python/Flask e um em
Node.js/Express, um deles já parcialmente organizado.

| Projeto | Stack | Findings | Estado final |
|---|---|---|---|
| `code-smells-project` | Python + Flask 3.1.1 | 22 (7 CRITICAL, 5 HIGH, 6 MEDIUM, 4 LOW) | MVC completo, 35 requisições validadas |
| `ecommerce-api-legacy` | Node.js + Express 4.18 | 23 (7 CRITICAL, 5 HIGH, 7 MEDIUM, 4 LOW) | MVC completo, 12 requisições validadas |
| `task-manager-api` | Python + Flask 3.0 + SQLAlchemy | 25 (5 CRITICAL, 6 HIGH, 9 MEDIUM, 5 LOW) | camadas completadas, 41 requisições validadas |

Relatórios da Fase 2 em [`reports/audit-project-{1,2,3}.md`](reports/); saída da Fase 3 em
[`reports/refactor-project-{1,2,3}.md`](reports/). Logs de todas as requisições, antes e depois,
em [`reports/logs/`](reports/logs/).

---

## A) Análise Manual

Levantamento feito antes de escrever a skill, lendo o código dos três projetos. Cada achado
abaixo foi confirmado no arquivo e, quando possível, reproduzido com uma requisição real.

### Projeto 1 — `code-smells-project` (Python/Flask, e-commerce)

| Severidade | Problema | Local | Por que importa |
|---|---|---|---|
| CRITICAL | Endpoint que executa SQL arbitrário | `app.py:59-78` | `POST /admin/query` roda qualquer comando enviado no corpo, sem autenticação. É acesso total ao banco para qualquer chamador. |
| CRITICAL | SQL Injection em toda a camada de dados | `models.py:28, 110, 291` e mais 15 pontos | As queries são concatenadas com a entrada do usuário. Confirmado: login com `admin@loja.com' OR '1'='1` devolve 200 e autentica como administrador. |
| CRITICAL | Senhas em texto puro, devolvidas pela API | `models.py:83, 99, 127` | `GET /usuarios` devolve `"senha":"admin123"`. O vazamento não exige nem invadir o banco. |
| CRITICAL | Chave secreta exposta no health check | `controllers.py:285-289` | `GET /health` devolve a `SECRET_KEY`, o que anula qualquer proteção baseada nela. |
| HIGH | God Module com quatro domínios | `models.py:1-314` | Um arquivo concentra SQL de produtos, usuários, pedidos e itens, mais o cálculo de desconto e a formatação. Nada é testável isoladamente. |
| HIGH | Regra de negócio nos controllers | `controllers.py:43-54, 242-250` | Faixa de preço, categorias válidas e a máquina de estados do pedido vivem no handler HTTP, duplicadas entre criar e atualizar. |
| MEDIUM | Query N+1 na listagem de pedidos | `models.py:187-199, 219-231` | Uma consulta de itens por pedido e uma de produto por item: o custo cresce multiplicativamente. |
| MEDIUM | Tratamento de erro duplicado que vaza detalhe | `controllers.py` (16 ocorrências) | `except Exception: return str(e), 500` devolve mensagem do SQLite ao cliente e não registra nada. |
| LOW | Magic numbers nas faixas de desconto | `models.py:257-262` | `10000`, `5000`, `0.1`, `0.05` soltos no meio do cálculo, sem nome. |
| LOW | `print` como log, com dado pessoal | `controllers.py:161, 179, 182` | E-mails de usuários escritos em stdout, sem nível nem destino configurável. |

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express, LMS com checkout)

| Severidade | Problema | Local | Por que importa |
|---|---|---|---|
| CRITICAL | Segredos de produção no código | `src/utils.js:1-7` | Senha do banco, chave `pk_live` do gateway e usuário de SMTP versionados. A chave move dinheiro real. |
| CRITICAL | God Class `AppManager` | `src/AppManager.js:4-139` | Uma classe faz conexão, DDL, seed, roteamento, regra de checkout e autorização de pagamento: 78% do código do projeto. |
| CRITICAL | Cartão e chave do gateway em log | `src/AppManager.js:45` | O número completo do cartão vai para stdout a cada checkout. Violação direta de PCI-DSS. |
| CRITICAL | Checkout não confere a senha | `src/AppManager.js:40, 74` | Se o e-mail já existe, a matrícula prossegue sem verificar a senha. Confirmado: checkout em nome de outro usuário conhecendo só o e-mail. |
| HIGH | Checkout sem transação | `src/AppManager.js:50-57` | Matrícula, pagamento e auditoria são escritas independentes; falha no meio deixa aluno matriculado sem pagamento. |
| HIGH | Estado global mutável | `src/utils.js:9-10, 25` | `globalCache` cresce sem limite e `totalRevenue` é exportado por valor, então nunca reflete a realidade. |
| MEDIUM | N+1 no relatório financeiro | `src/AppManager.js:83-127` | 1 + N + 2×M consultas onde um JOIN resolveria. |
| MEDIUM | Coordenação assíncrona por contadores | `src/AppManager.js:86-122` | Sem `Promise.all`; um erro trava a requisição para sempre. Confirmado: a ordem dos cursos muda entre chamadas idênticas. |
| LOW | Nomes crípticos no contrato da API | `src/AppManager.js:29-33` | `usr`, `eml`, `pwd`, `c_id` vazam abreviações para quem consome a API. |
| LOW | Magic numbers e status soltos | `src/utils.js:19`, `AppManager.js:46, 108` | `10000`, `substring(0,10)` e as strings `"PAID"`/`"DENIED"` sem constante. |

### Projeto 3 — `task-manager-api` (Python/Flask, parcialmente organizado)

| Severidade | Problema | Local | Por que importa |
|---|---|---|---|
| CRITICAL | Credenciais de SMTP hardcoded | `services/notification_service.py:7-10` | Usuário e senha de e-mail no código, em uma classe que nem chega a ser usada. |
| CRITICAL | Senhas em MD5 sem salt | `models/user.py:29` | Confirmado: o hash do seed é o MD5 de `1234`, quebrado por qualquer tabela arco-íris. |
| CRITICAL | Hash de senha devolvido pela API | `models/user.py:16-25` | `to_dict()` inclui `password`, então `GET /users/<id>` e `POST /login` entregam o hash. |
| CRITICAL | Token falso e zero autenticação | `routes/user_routes.py:210` | O login devolve `fake-jwt-token-<id>`, que nenhuma rota verifica. As 22 rotas são públicas, inclusive as de exclusão. |
| HIGH | Regra de negócio dentro das rotas | `routes/report_routes.py:12-101` | 90 linhas de agregação em um handler. As pastas `services/` e `utils/` existem, mas a regra não está nelas. |
| HIGH | Camadas cosméticas e código morto | `services/notification_service.py`, `utils/helpers.py:57-108` | O único service nunca é chamado; quase todo `helpers.py` está sem uso; `Task.is_overdue()` existe e é ignorado. |
| MEDIUM | N+1 em três endpoints | `routes/task_routes.py:41-57`, `report_routes.py:53-68, 161-164` | Consultas dentro de laços onde havia relacionamento ou agregação disponível. |
| MEDIUM | APIs deprecated | `datetime.utcnow()` em 24 pontos; `Query.get()` em 14 | Obsoletas no Python 3.12 e no SQLAlchemy 2.0. `utcnow()` ainda torna toda a matemática de prazo insensível a fuso. |
| LOW | Constantes duplicadas e ignoradas | `routes/task_routes.py:110, 177`, `utils/helpers.py:110-116` | A lista de status aparece em cinco lugares, enquanto o bloco de constantes existente não é usado. |
| LOW | Imports mortos e `print` como log | `app.py:7`, `routes/task_routes.py:7, 149` | Ruído de leitura e ausência de log estruturado. |

---

## B) Construção da Skill

### Decisões de design

O `SKILL.md` é o procedimento; os arquivos de referência são o conhecimento. Essa separação
mantém o arquivo principal pequeno (163 linhas) e carrega o detalhe só quando a fase precisa.

```
.claude/skills/refactor-arch/
├── SKILL.md                          workflow das 3 fases, princípios e red flags
├── references/
│   ├── project-analysis.md           Fase 1: heurísticas de detecção
│   ├── antipatterns-catalog.md       Fase 2: 19 anti-patterns com sinais de detecção
│   ├── report-template.md            Fases 1-3: formato exato dos três blocos
│   ├── architecture-guidelines.md    Fase 3: camadas alvo e regra de dependência
│   └── refactoring-playbook.md       Fase 3: 15 transformações antes/depois
└── scripts/audit.py                  varredura estática opcional de apoio
```

Três decisões moldaram o resultado:

**Cada fase declara o que ler.** A Fase 1 aponta para `project-analysis.md`, a Fase 2 para o
catálogo e o template, a Fase 3 para as guidelines e o playbook. Sem isso o agente tende a
auditar de memória e produzir achados genéricos.

**Os sinais de detecção são comandos, não adjetivos.** Cada anti-pattern do catálogo traz o
`grep` que o encontra. "Código ruim" não é acionável; `(execute|query)\s*\(\s*f["']` é.

**O baseline é obrigatório antes de tocar em qualquer arquivo.** A Fase 3 começa subindo a
aplicação original e gravando a resposta de cada endpoint. Sem esse gabarito, "a aplicação
continua funcionando" seria uma afirmação sem prova.

### Anti-patterns do catálogo e por quê

O catálogo tem 19 entradas com severidade distribuída. Elas saíram diretamente da análise
manual: cada problema encontrado nos três projetos precisava de uma entrada que o detectasse.

| Severidade | Anti-patterns | Origem na análise manual |
|---|---|---|
| CRITICAL | Hardcoded Credentials, SQL Injection, God Class/Module, Senha em texto puro ou hash inadequado, Exposição de dados sensíveis, Endpoint administrativo sem autenticação | `SECRET_KEY` do projeto 1, `pk_live` do projeto 2, SMTP do projeto 3; concatenação em `models.py`; `AppManager`; MD5 e base64; `/health` e `to_dict`; `/admin/query` e o relatório financeiro |
| HIGH | Business Logic in Controller, Tight Coupling sem DI, Mutable Global State, Ausência de camada de serviço, Operação de escrita sem transação | Regra de desconto no controller; `import models` direto; `globalCache` e a conexão global; `services/` cosmético do projeto 3; checkout e criação de pedido |
| MEDIUM | Query N+1, Validação ausente, Error handling espalhado, **Deprecated API**, Duplicação de código | N+1 nos três projetos; 500 por tipo inválido; 16 `except` iguais; `utcnow` e `Query.get`; `get_pedidos_usuario` vs `get_todos_pedidos` |
| LOW | Magic numbers, Nomenclatura ruim e código morto, Respostas inconsistentes | Faixas de desconto; `u`, `e`, `p`; envelope diferente por rota |

A entrada de **APIs deprecated** é uma tabela com dezessete pares "obsoleto → moderno" cobrindo
Python, Flask, SQLAlchemy, Node, Express e PHP. O relatório sempre registra o resultado da
varredura, inclusive quando ela não encontra nada — foi o caso do projeto 1, onde a ausência
de APIs obsoletas é ela própria uma informação de auditoria.

### Como a skill ficou agnóstica de tecnologia

Quatro mecanismos, todos exercitados nos três projetos:

1. **Detecção por manifesto.** A Fase 1 identifica a stack por `requirements.txt`,
   `package.json`, `composer.json`, `go.mod`, `Gemfile`, `pom.xml` ou `*.csproj`, e confirma
   pelos imports.
2. **Sinais de detecção por linguagem.** Cada anti-pattern traz o padrão equivalente em Python
   e em JavaScript. SQL Injection, por exemplo, procura f-string no Python e template literal no
   JavaScript.
3. **Estruturas alvo por stack.** As guidelines definem a árvore para Flask (blueprints e app
   factory) e para Express (router, `app.js` sem `listen`), mais uma tabela de equivalências
   para Laravel, Rails, NestJS, Spring, Django e Gin. O que é fixo são as responsabilidades das
   camadas, não os nomes das pastas.
4. **Transformações em duas linguagens.** O playbook mostra antes/depois em Python e em
   JavaScript sempre que a forma difere, como no caso de transação e de tratamento de erro.

### Desafios encontrados

**Projeto já organizado exige o oposto de reestruturar.** No `task-manager-api` as pastas certas
já existiam. Aplicar a mesma receita do monólito teria gerado um diff enorme sem ganho. A
solução foi escrever, nas guidelines, uma tabela que liga o estado inicial ao escopo da Fase 3, e
um teste de diagnóstico: onde está a regra de negócio, onde está o acesso a dados, onde está o
roteamento. Quando as três respostas apontam para o mesmo arquivo, é monólito; quando regra e
roteamento coincidem, são camadas cosméticas.

**Corrigir segurança muda o comportamento observável.** Fechar o bypass de login altera a
resposta de 200 para 401 — exatamente o efeito desejado, mas indistinguível de uma regressão
para quem só compara logs. A skill passou a exigir a seção `Intentional Behavior Changes` no
relatório da Fase 3: uma diferença listada é correção, uma diferença não listada é regressão.

**Autenticação e comparação antes/depois.** Nos projetos 2 e 3, proteger as rotas faria toda
requisição do smoke test virar 401. A saída foi fazer os scripts enviarem a credencial desde o
baseline: o código original ignora o cabeçalho e o refatorado o exige, então a comparação
continua válida. Duas requisições deliberadamente sem credencial ficam no fim de cada script,
para demonstrar o 401.

**Baseline contaminado.** Na primeira captura do projeto 1, um servidor de uma execução anterior
ainda ocupava a porta e respondeu no lugar do novo processo, gerando um baseline com o banco
vazio. Passei a subir o código original a partir de um `git worktree` do commit base, em porta
livre verificada, com o PID guardado para o encerramento — e isso virou a regra de baseline
descrita no `SKILL.md`.

---

## C) Resultados

### Findings por severidade

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|
| 1 — `code-smells-project` | 7 | 5 | 6 | 4 | 22 |
| 2 — `ecommerce-api-legacy` | 7 | 5 | 7 | 4 | 23 |
| 3 — `task-manager-api` | 5 | 6 | 9 | 5 | 25 |

Todos os CRITICAL e HIGH foram resolvidos nos três projetos. As pendências registradas são de
severidade MEDIUM e estão justificadas por escrito no README de cada projeto.

### Cobertura da análise manual pela skill

O critério pede que a Fase 2 reencontre no mínimo 5 dos problemas documentados manualmente. A
skill reencontrou **todos os 10 de cada projeto**, com o mesmo `arquivo:linha`.

| Problema da análise manual | Projeto 1 | Projeto 2 | Projeto 3 |
|---|---|---|---|
| Credenciais ou segredos hardcoded | ✅ | ✅ | ✅ |
| God Class / God Module | ✅ | ✅ | ✅ (camadas cosméticas) |
| Falha de autenticação ou exposição de dado sensível | ✅ (3 achados) | ✅ (3 achados) | ✅ (3 achados) |
| Regra de negócio fora da camada certa | ✅ | ✅ | ✅ |
| Acoplamento sem injeção de dependência | ✅ | ✅ | ✅ |
| Estado global mutável ou escrita sem transação | ✅ | ✅ | ✅ |
| Query N+1 | ✅ | ✅ | ✅ (3 endpoints) |
| Tratamento de erro duplicado ou validação ausente | ✅ | ✅ | ✅ |
| Magic numbers | ✅ | ✅ | ✅ |
| Nomenclatura ruim, código morto ou `print` como log | ✅ | ✅ | ✅ |
| **Reencontrados / documentados** | **10/10** | **10/10** | **10/10** |

Além desses, a auditoria trouxe achados que a leitura manual não havia registrado — por exemplo
o CORS aberto e os filtros que descartavam o valor zero no projeto 1, e a inicialização de schema
sem verificação de erro no projeto 2.

### Antes e depois da estrutura

**Projeto 1 — monólito de 4 arquivos vira MVC completo**

```
antes                          depois
├── app.py       (88)          ├── app.py                 entry point
├── controllers.py (292)       └── src/
├── models.py    (314)             ├── app.py             composition root (create_app)
└── database.py   (86)             ├── config/settings.py
                                   ├── models/            db, produto, usuario, pedido
                                   ├── services/          produto, usuario, pedido, relatorio, notificacao
                                   ├── controllers/       produto, usuario, pedido, sistema
                                   ├── views/routes.py    blueprints
                                   └── middlewares/errors.py
```

**Projeto 2 — God Class vira camadas**

```
antes                          depois
└── src/                       └── src/
    ├── app.js      (14)           ├── server.js          entry point
    ├── AppManager.js (141)        ├── app.js             createApp(), sem listen
    └── utils.js     (25)          ├── config/            index.js, logger.js
                                   ├── models/            db, schema, user, course,
                                   │                      enrollment, payment, auditLog, report
                                   ├── services/          checkout, paymentGateway,
                                   │                      passwordHasher, report, user
                                   ├── controllers/       checkout, report, user
                                   ├── routes/index.js
                                   └── middlewares/       errors, errorHandler, requireAdmin
```

**Projeto 3 — camadas cosméticas viram camadas reais**

```
antes                          depois
├── app.py (34, cria app       ├── app.py                 app factory
│   no import)                 ├── config.py              novo
├── database.py                ├── database.py            mantido
├── models/    (3 entidades)   ├── models/                mantidos, com hash forte e is_overdue em uso
├── routes/    (733 linhas     ├── schemas/               novo (marshmallow)
│   com toda a regra)          ├── services/              task, user, auth, category, report, notification
├── services/  (1 classe       ├── controllers/           novo
│   nunca chamada)             ├── routes/                só mapeamento, + blueprint de categories
└── utils/     (quase todo     ├── middlewares/           errors, auth
    sem uso)                   └── utils/                 clock (novo), helpers (limpo)
```

### Checklist de validação

| Item | Projeto 1 | Projeto 2 | Projeto 3 |
|---|---|---|---|
| **Fase 1** — linguagem detectada | ✅ Python | ✅ JavaScript | ✅ Python |
| **Fase 1** — framework detectado | ✅ Flask 3.1.1 | ✅ Express ^4.18.2 | ✅ Flask 3.0.0 + SQLAlchemy |
| **Fase 1** — domínio descrito | ✅ e-commerce | ✅ LMS com checkout | ✅ task manager |
| **Fase 1** — contagem de arquivos confere | ✅ 4 | ✅ 3 | ✅ 15 |
| **Fase 2** — relatório segue o template | ✅ | ✅ | ✅ |
| **Fase 2** — todo finding com arquivo e linha | ✅ | ✅ | ✅ |
| **Fase 2** — ordenado CRITICAL → LOW | ✅ | ✅ | ✅ |
| **Fase 2** — mínimo de 5 findings | ✅ 22 | ✅ 23 | ✅ 25 |
| **Fase 2** — detecção de APIs deprecated | ✅ nenhuma, registrado | ✅ 3 padrões legados | ✅ `utcnow`, `Query.get` |
| **Fase 2** — pausa e pede confirmação | ✅ | ✅ | ✅ |
| **Fase 3** — estrutura MVC | ✅ | ✅ | ✅ |
| **Fase 3** — config sem hardcoded | ✅ `src/config/settings.py` | ✅ `src/config/index.js` | ✅ `config.py` |
| **Fase 3** — models abstraem dados | ✅ 4 módulos | ✅ 6 módulos | ✅ 3 entidades + schemas |
| **Fase 3** — views/routes separadas | ✅ `views/routes.py` | ✅ `routes/index.js` | ✅ `routes/` (5 blueprints) |
| **Fase 3** — controllers concentram o fluxo | ✅ | ✅ | ✅ |
| **Fase 3** — error handling centralizado | ✅ `middlewares/errors.py` | ✅ `middlewares/errorHandler.js` | ✅ `middlewares/errors.py` |
| **Fase 3** — entry point claro | ✅ `app.py` | ✅ `src/server.js` | ✅ `app.py` |
| **Fase 3** — aplicação inicia sem erros | ✅ | ✅ | ✅ |
| **Fase 3** — endpoints originais respondem | ✅ 35/35 | ✅ 12/12 | ✅ 41/41 |
| **Fase 3** — bloco PHASE 3 registrado | ✅ [relatório](reports/refactor-project-1.md) | ✅ [relatório](reports/refactor-project-2.md) | ✅ [relatório](reports/refactor-project-3.md) |

### Validação por execução

Cada projeto foi exercitado com o mesmo script antes e depois da refatoração. O comparador
`reports/smoke/compare.py` alinha requisição a requisição.

| Projeto | Requisições | Todas respondem | Resposta idêntica | Só status diferente | Só corpo diferente |
|---|---|---|---|---|---|
| 1 | 35 | ✅ | 20 | 4 | 11 |
| 2 | 12 | ✅ | 3 | 2 | 7 |
| 3 | 41 | ✅ | 29 | 3 | 9 |

Nenhum endpoint original deixou de responder. Toda diferença é uma correção listada como
intencional no README do projeto. No projeto 1, por exemplo, as quatro diferenças de status são:
o bypass de login que passou a devolver 401, o payload de injeção que deixou de gerar erro de
SQL, o erro de tipo que virou 400 e o executor de SQL arbitrário que passou a responder 410 com
a explicação.

As medições acima foram feitas com cada projeto na **configuração padrão**, sem variáveis de
ambiente — exatamente como um avaliador o executaria. Os controles de acesso introduzidos são
ativáveis por configuração (`ADMIN_TOKEN` nos projetos 1 e 2, `REQUIRE_AUTH` no projeto 3), e a
evidência de que funcionam está em `reports/logs/project-2-after-auth-enabled.txt` e
`reports/logs/project-3-after-auth-enabled.txt`.

### Logs das aplicações rodando após a refatoração

```
$ cd code-smells-project && python app.py
WARNING src.app SECRET_KEY não definida no ambiente: usando chave aleatória desta execução.
 * Serving Flask app 'src.app'
 * Running on http://127.0.0.1:5000

$ curl localhost:5000/health
{"counts":{"pedidos":0,"produtos":10,"usuarios":3},"database":"connected","status":"ok","versao":"1.0.0"}
```

```
$ cd ecommerce-api-legacy && npm start
{"nivel":"info","mensagem":"LMS API no ar","porta":3000}

$ curl -H "X-Admin-Token: $ADMIN_TOKEN" localhost:3000/api/admin/financial-report
[{"course":"Clean Architecture","revenue":997,"students":[{"student":"Leonan","paid":997}]},
 {"course":"Docker","revenue":0,"students":[]}]
```

```
$ cd task-manager-api && python seed.py && python app.py
Seed concluído com sucesso!
  3 usuários / 4 categorias / 10 tasks
 * Running on http://127.0.0.1:5000

$ curl localhost:5000/
{"message":"Task Manager API","version":"1.0"}
```

Os logs completos de todas as requisições estão em `reports/logs/project-{1,2,3}-{before,after}.txt`.

### Como a skill se comportou em stacks diferentes

**A Fase 1 não teve dificuldade com nenhuma stack.** Manifesto mais imports bastou para
identificar linguagem, framework e versão nos três casos. O inventário de endpoints exigiu mais
cuidado no projeto 1, onde as rotas são registradas com `add_url_rule` em vez de decorators, e no
projeto 2, onde estão dentro de um método de classe — situações previstas no arquivo de análise.

**A Fase 2 rendeu números parecidos em contextos muito diferentes.** 22, 23 e 25 findings. O
projeto "mais organizado" produziu o maior número, o que confirma que estrutura de pastas não é
indicador de qualidade: a auditoria olha para onde a regra de negócio está, não para onde os
arquivos estão.

**A Fase 3 foi onde a adaptação apareceu.** Nos projetos 1 e 2 a transformação foi estrutural —
criar a árvore inteira e desmontar o God Module. No projeto 3 quase nenhum arquivo mudou de
lugar: entraram `controllers/`, `schemas/`, `config.py` e os middlewares, e a regra saiu das rotas
para os services. É a diferença entre reorganizar e completar.

**A diferença real entre as stacks foi o modelo de concorrência.** Em Python, o trabalho maior
foi eliminar o SQL concatenado e dar ciclo de vida por requisição à conexão. Em Node, foi
promisificar o driver: a pirâmide de callbacks era a causa do N+1 coordenado por contadores, da
resposta não determinística e da ausência de transação. Uma única transformação resolveu os três.

---

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) instalado e autenticado
  (a skill foi desenvolvida e executada na versão 2.1.x)
- Python 3.11 ou superior, para os projetos 1 e 3
- Node.js 20 ou superior, para o projeto 2
- `curl`, para a validação dos endpoints

### Executar a skill

A skill é descoberta automaticamente quando está em `.claude/skills/` do diretório de trabalho.
Ela está presente nos três projetos.

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

A skill executa a Fase 1, imprime a análise, executa a Fase 2, imprime o relatório de auditoria e
**para**, perguntando `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`. Nenhum
arquivo é modificado antes da resposta. Respondendo `y`, ela captura o baseline dos endpoints,
refatora e valida.

Para auditar um projeto novo, copie `code-smells-project/.claude/skills/refactor-arch/` para
dentro dele e rode o mesmo comando.

### Validar que a refatoração funcionou

Cada projeto tem um script de smoke test que exercita todos os endpoints.

```bash
# Projeto 1
cd code-smells-project
pip install -r requirements.txt
python app.py &                                  # sobe em :5000
../reports/smoke/project-1.sh http://127.0.0.1:5000

# Projeto 2
cd ecommerce-api-legacy
npm install
npm start &                                      # sobe em :3000
../reports/smoke/project-2.sh http://127.0.0.1:3000

# Projeto 3
cd task-manager-api
pip install -r requirements.txt
python seed.py && python app.py &                # sobe em :5000
../reports/smoke/project-3.sh http://127.0.0.1:5000
```

Para comparar com o comportamento original:

```bash
python3 reports/smoke/compare.py \
  reports/logs/project-1-before.txt reports/logs/project-1-after.txt
```

A saída marca `!!` quando o status mudou e `~` quando só o corpo mudou. Toda marcação deve
corresponder a uma linha da tabela "Mudanças de comportamento intencionais" do README do projeto.

Os controles de acesso são opcionais e não interferem na validação acima. Para exercitá-los:

```bash
# Projeto 1 e 2: exigem o cabeçalho X-Admin-Token quando ADMIN_TOKEN está definido
ADMIN_TOKEN=token-de-teste npm start            # (projeto 2)

# Projeto 3: exige Authorization: Bearer <token> quando REQUIRE_AUTH=true
REQUIRE_AUTH=true python app.py
```

A varredura estática de apoio pode ser executada isoladamente:

```bash
python code-smells-project/.claude/skills/refactor-arch/scripts/audit.py <caminho-do-projeto>
```

### Ordem de execução sugerida

1. Ler os relatórios em `reports/` para entender o que foi encontrado em cada projeto.
2. Subir cada aplicação refatorada e rodar o smoke test correspondente.
3. Comparar com o baseline usando `compare.py`.
4. Para reproduzir a skill do zero, copiar a pasta da skill para um projeto legado qualquer e
   invocar `/refactor-arch`.

---

## Estrutura do repositório

```
.
├── README.md                          este documento
├── code-smells-project/               projeto 1, refatorado
│   └── .claude/skills/refactor-arch/  a skill (origem)
├── ecommerce-api-legacy/              projeto 2, refatorado
│   └── .claude/skills/refactor-arch/  cópia da skill
├── task-manager-api/                  projeto 3, refatorado
│   └── .claude/skills/refactor-arch/  cópia da skill
└── reports/
    ├── audit-project-1.md             saída das Fases 1 e 2 no projeto 1
    ├── audit-project-2.md             idem, projeto 2
    ├── audit-project-3.md             idem, projeto 3
    ├── refactor-project-1.md          saída da Fase 3 no projeto 1
    ├── refactor-project-2.md          idem, projeto 2
    ├── refactor-project-3.md          idem, projeto 3
    ├── logs/                          respostas de todos os endpoints, antes e depois
    └── smoke/                         scripts de validação e comparador
```
