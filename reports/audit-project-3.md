# Relatório de auditoria — Projeto 3 (`task-manager-api`)

Saída das Fases 1 e 2 da skill `/refactor-arch`. Este projeto já tinha pastas `models/`,
`routes/`, `services/` e `utils/`, então a auditoria cobre tanto problemas de código quanto a
separação de camadas que as pastas prometem e não entregam.

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.0.0 + Flask-SQLAlchemy 3.1.1
Dependencies:  flask-cors 4.0.0; marshmallow 3.20.1, requests 2.31.0 e python-dotenv 1.0.0
               estão declaradas e nunca são importadas
Domain:        Task Manager (usuários, categorias, tarefas com prazo e prioridade,
               relatórios de produtividade, login)
Architecture:  Camadas parciais — as pastas existem, mas a separação é cosmética: as rotas
               concentram regra de negócio, consultas ao ORM e serialização; services/ tem uma
               única classe que ninguém chama; utils/ está quase todo sem uso
Source files:  15 files analyzed
DB tables:     users, categories, tasks
Endpoints:     22 routes
Entry point:   python seed.py && python app.py (porta 5000, debug=True, host 0.0.0.0)
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask + SQLAlchemy
Files:   15 analyzed | ~1158 lines of code

## Summary
CRITICAL: 5 | HIGH: 6 | MEDIUM: 9 | LOW: 5

## Findings

### [CRITICAL] Credenciais de SMTP hardcoded
File: services/notification_service.py:7-10
Description: o construtor de `NotificationService` fixa host, porta, usuário
(`taskmanager@gmail.com`) e senha (`senha123`) do servidor de e-mail. A senha é usada em
`server.login` na linha 17.
Impact: credencial de e-mail versionada no repositório; quem tiver acesso ao código envia
e-mail em nome da aplicação.
Recommendation: mover para variáveis de ambiente lidas por um módulo de config — o projeto já
declara `python-dotenv` na dependência e não a usa — e rotacionar a senha exposta.

### [CRITICAL] SECRET_KEY hardcoded
File: app.py:13
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'`, igual em qualquer ambiente. A
URI do banco (linha 11) e o modo debug (linha 34) também são literais.
Impact: chave de assinatura pública no histórico do git; nenhuma configuração por ambiente.
Recommendation: `config.py` com perfis lendo do ambiente e `.env.example` documentando as
chaves.

### [CRITICAL] Senhas com MD5 sem salt
File: models/user.py:29
Description: `set_password` grava `hashlib.md5(pwd.encode()).hexdigest()` e `check_password`
(linha 32) compara o hash com `==`. Confirmado na execução: o usuário do seed tem
`81dc9bdb52d04dc20036dbd8313ed055`, que é o MD5 de `1234` e é revertido por qualquer tabela
arco-íris.
Impact: o vazamento do banco entrega as senhas reais; a comparação direta ainda permite ataque
de tempo.
Recommendation: `werkzeug.security.generate_password_hash` / `check_password_hash` (ou bcrypt),
com re-hash no próximo login bem-sucedido. Ver também o finding de APIs deprecated.

### [CRITICAL] Hash de senha exposto nas respostas da API
File: models/user.py:16-25
Description: `User.to_dict()` inclui o campo `password`, e esse dicionário é devolvido por
`GET /users/<id>` (routes/user_routes.py:33), `POST /users` (:85-86), `PUT /users/<id>` (:129) e
`POST /login` (:209). Confirmado na execução: o hash aparece no corpo das quatro respostas.
Impact: qualquer chamador anônimo coleta os hashes de todos os usuários e os quebra offline.
Recommendation: serializar por allowlist de campos, sem `password`; usar marshmallow, que já é
dependência do projeto, para o schema de saída.

### [CRITICAL] Ausência completa de autenticação e autorização
File: routes/user_routes.py:210
Description: o login devolve `'fake-jwt-token-' + str(user.id)`, um token previsível que nenhum
endpoint verifica. Não há decorator de autenticação em nenhuma das 22 rotas; `User.is_admin()`
(models/user.py:34-38) existe e nunca é chamado. Assim, `DELETE /users/<id>`,
`DELETE /tasks/<id>` e `/reports/summary` são públicos.
Impact: qualquer pessoa apaga usuários e tarefas e lê o relatório de produtividade de toda a
equipe.
Recommendation: emitir token real (JWT assinado com a chave de config), validar em um
middleware `before_request` e exigir papel de administrador nas rotas destrutivas e de
relatório.

### [HIGH] Regra de negócio e acesso a dados dentro das rotas
File: routes/report_routes.py:12-101
Description: `summary_report` tem 90 linhas que consultam o ORM, agregam contagens, calculam
atraso, produtividade por usuário e montam o JSON. O mesmo padrão está em
routes/task_routes.py:11-63 (listagem), :85-154 (criação), :273-299 (estatísticas) e
routes/user_routes.py:42-90. As camadas `services/` e `utils/` existem, mas a regra não está
nelas.
Impact: nada é testável sem subir a aplicação; a mesma regra é reescrita em cada rota que dela
precisa; o arquivo de rotas cresce sem limite.
Recommendation: criar services por domínio (task, user, category, report, auth) e reduzir as
rotas a mapeamento URL → controller.

### [HIGH] Camada de serviço inexistente na prática e código morto
File: services/notification_service.py:1-48
Description: `NotificationService` é a única classe de `services/` e nunca é importada por
nenhuma rota; nenhuma task atribuída dispara notificação. Em `utils/helpers.py`,
`process_task_data` (:57-108), `validate_email` (:19-23), `is_valid_color` (:52-55),
`sanitize_string`, `generate_id`, `log_action` e o bloco de constantes (:110-116) também não
são usados; `format_date` e `calculate_percentage` são importados em
routes/report_routes.py:7 e nunca chamados. No model, `Task.is_overdue()`
(models/task.py:50-60), `validate_status` e `validate_priority` (:38-48) nunca são chamados.
Impact: a organização de pastas dá falsa sensação de arquitetura; quem chega ao projeto não
sabe o que está em uso; a lógica correta existe mas é ignorada em favor de cópias.
Recommendation: mover a regra para os services, passar a usar os helpers e os métodos do model,
e remover o que sobrar.

### [HIGH] Acoplamento direto, sem injeção de dependência
File: routes/task_routes.py:2-5
Description: cada módulo de rotas importa o `db` global e as classes concretas de model
(`from database import db`, `from models.task import Task`); o mesmo em
routes/user_routes.py:2-4 e routes/report_routes.py:2-5. Nada recebe dependências.
Impact: impossível testar uma rota sem banco real; impossível trocar a persistência sem tocar em
todas as rotas.
Recommendation: repositórios/serviços recebendo a sessão por parâmetro, montados em um
composition root.

### [HIGH] Estado global e efeito colateral em tempo de import
File: app.py:30-31
Description: `with app.app_context(): db.create_all()` roda quando o módulo é importado — o que
inclui `from app import app, db` em seed.py:2 e qualquer import em teste. A aplicação é criada
no escopo do módulo (app.py:9), o `db` é global (database.py:3) e
`NotificationService.notifications` (services/notification_service.py:6) é uma lista em memória.
Impact: importar o módulo cria o banco; não há como instanciar a app com outra configuração em
teste; sem migrations, alterações de schema nunca chegam a um banco existente.
Recommendation: app factory `create_app(config)`, inicialização explícita do banco e
Flask-Migrate para evolução de schema.

### [HIGH] Exceções engolidas por `except` nu
File: routes/task_routes.py:62-63
Description: `except: return jsonify({'error': 'Erro interno'}), 500` captura qualquer coisa sem
registrar nada. O padrão se repete em routes/task_routes.py:137, 151, 204, 236,
routes/user_routes.py:130, 149, routes/report_routes.py:186, 207, 221,
services/notification_service.py:23 e utils/helpers.py:44-50 e 88.
Impact: falhas reais somem sem log e sem stack trace; a depuração passa a depender de reproduzir
o erro localmente.
Recommendation: capturar exceções específicas, registrar com `logging` e tratar a resposta em um
handler central.

### [HIGH] Exclusão de usuário sem transação explícita
File: routes/user_routes.py:140-146
Description: as tarefas do usuário são marcadas para exclusão em um laço (140-142) **fora** do
bloco `try`, e o `delete` do usuário mais o `commit` ficam dentro dele (144-146). A chave
estrangeira `tasks.user_id` (models/task.py:13) não declara `ondelete`.
Impact: falha no commit deixa a sessão com exclusões parciais pendentes; exclusão por outro
caminho deixa tarefas órfãs apontando para um usuário inexistente.
Recommendation: uma única transação cobrindo as duas exclusões, com `cascade` declarado no
relacionamento.

### [MEDIUM] Query N+1 na listagem de tarefas
File: routes/task_routes.py:41-57
Description: para cada tarefa, uma consulta de usuário (linha 42) e outra de categoria (linha 51),
embora os relacionamentos `Task.user` e `Task.category` já existam (models/task.py:20-21).
Impact: `GET /tasks` custa 1 + 2N consultas e degrada com o volume.
Recommendation: `selectinload(Task.user)` e `selectinload(Task.category)` em uma consulta só.

### [MEDIUM] Query N+1 no relatório de resumo
File: routes/report_routes.py:53-68
Description: o laço sobre usuários dispara `Task.query.filter_by(user_id=...)` por usuário. Somam-se
nove contagens independentes nas linhas 19-28, que caberiam em um `GROUP BY`, e
`Task.query.all()` na linha 30 traz todas as tarefas para contar atrasos em Python.
Impact: o endpoint mais pesado da API faz dezenas de idas ao banco por requisição.
Recommendation: uma consulta agregada por status e prioridade, uma por produtividade de usuário,
e o filtro de atraso resolvido no `WHERE`.

### [MEDIUM] Query N+1 na listagem de categorias
File: routes/report_routes.py:161-164
Description: uma consulta de contagem de tarefas por categoria, dentro do laço de categorias.
Impact: custo linear desnecessário em um endpoint de listagem simples.
Recommendation: `LEFT JOIN` com `COUNT` e `GROUP BY`.

### [MEDIUM] Deprecated API: `datetime.utcnow()`
File: models/task.py:15
Description: `datetime.utcnow()` está deprecated desde o Python 3.12 e devolve datetime *naive*.
Ocorre em models/task.py:15, 16 e 52, models/user.py:14, models/category.py:11,
routes/task_routes.py:31, 72, 215 e 285, routes/user_routes.py:172, routes/report_routes.py:35,
42, 45, 71 e 133, services/notification_service.py:35, utils/helpers.py:38 e seed.py:66-75.
Impact: emite DeprecationWarning e quebra em versões futuras; como os valores são naive, toda a
matemática de atraso ignora fuso e fica incorreta fora do UTC.
Recommendation: `datetime.now(timezone.utc)`, com uma função única de "agora" e normalização das
datas lidas do banco.

### [MEDIUM] Deprecated API: `Model.query` e `Query.get()` do SQLAlchemy 1.x
File: routes/task_routes.py:67
Description: `Task.query.get(task_id)` usa a API legada do SQLAlchemy: `Query.get()` está
obsoleto na versão 2.0 em favor de `Session.get()`. Ocorre em routes/task_routes.py:67, 117,
122, 158, 188, 195 e 227, routes/user_routes.py:29, 94, 135 e 155 e
routes/report_routes.py:105, 192 e 212. O estilo `Model.query` aparece em praticamente todas as
consultas do projeto.
Impact: avisos de depreciação e quebra na próxima major do SQLAlchemy.
Recommendation: `db.session.get(Model, id)` para busca por chave e
`db.session.execute(select(...))` para as demais consultas.

### [MEDIUM] Validação ausente ou frágil que transforma erro do cliente em 500
File: routes/task_routes.py:113
Description: `if priority < 1 or priority > 5` compara sem checar tipo: confirmado na execução,
`POST /tasks` com `"priority": "alta"` devolve 500. O mesmo em :182. Em :261 e :264,
`int(priority)` e `int(user_id)` convertem parâmetros de query sem proteção — confirmado:
`GET /tasks/search?priority=abc` devolve 500. Em routes/report_routes.py:197 o corpo pode ser
`None`; em :180 a cor não é validada embora `is_valid_color` exista; em
routes/task_routes.py:167 `len()` é chamado sobre valor possivelmente não textual.
Impact: erro de entrada é reportado como falha do servidor, com página HTML em vez de JSON.
Recommendation: validar na borda com marshmallow (já é dependência) e devolver 400 com os
campos inválidos.

### [MEDIUM] Lógica de "tarefa atrasada" duplicada em cinco lugares
File: routes/task_routes.py:30-39
Description: o mesmo bloco aninhado de verificação de atraso aparece em
routes/task_routes.py:30-39, :71-80 e :284-287, routes/user_routes.py:171-180 e
routes/report_routes.py:34-37 e :132-135 — enquanto `Task.is_overdue()` (models/task.py:50-60)
implementa exatamente isso e nunca é chamado.
Impact: mudar a regra de atraso exige seis edições coerentes; as cópias divergem em silêncio.
Recommendation: usar `Task.is_overdue()` em todos os pontos e apagar as cópias.

### [MEDIUM] Serialização duplicada, ignorando `to_dict`
File: routes/task_routes.py:17-28
Description: a listagem monta o dicionário da tarefa campo a campo, embora `Task.to_dict()`
(models/task.py:23-36) faça o mesmo; routes/user_routes.py:162-169 repete uma terceira variação.
Cada `to_dict` também é escrito do zero em cada model, sem base comum.
Impact: os endpoints divergem no formato da mesma entidade e a correção de um campo não alcança
os outros.
Recommendation: uma camada de serialização única por entidade (schemas marshmallow), usada por
todos os endpoints.

### [MEDIUM] Ausência de paginação e busca com `LIKE` sem escape
File: routes/task_routes.py:250-255
Description: `GET /tasks`, `GET /users` e `GET /tasks/search` devolvem todos os registros sem
limite. Na busca, o termo entra em `f'%{query}%'` sem escapar `%` e `_`; não é injeção de SQL
(os parâmetros são vinculados pelo ORM), mas altera a semântica do filtro.
Impact: resposta cresce sem limite com a base; buscas com `%` retornam resultado inesperado.
Recommendation: paginação por `limit`/`offset` com teto e escape dos curingas no termo de busca.

### [LOW] Magic numbers e listas de valores válidos repetidos
File: routes/task_routes.py:110
Description: a lista de status aparece em routes/task_routes.py:110 e 177, models/task.py:39 e
utils/helpers.py:75 e 110; os papéis em routes/user_routes.py:71 e 120 e utils/helpers.py:111;
os limites de prioridade em routes/task_routes.py:113 e 182 e models/task.py:46; o tamanho
mínimo de senha em routes/user_routes.py:64 e 115. O bloco de constantes de
utils/helpers.py:110-116 existe para isso e não é usado.
Impact: uma mudança de regra exige caçar o valor em vários arquivos.
Recommendation: usar as constantes existentes, movidas para config ou para um módulo de domínio.

### [LOW] Imports mortos
File: app.py:7
Description: `import os, sys, json, datetime` em app.py:7 usa apenas `datetime`;
routes/task_routes.py:7 importa `json, os, sys, time` sem usar; routes/user_routes.py:6 importa
`hashlib` e `json` sem usar (e usa `re` sem importá-lo diretamente neste arquivo);
routes/report_routes.py:8, models/task.py:3 e utils/helpers.py:3-7 têm imports não utilizados;
em utils/helpers.py:33 o `import uuid` está dentro da função.
Impact: ruído de leitura e falsa impressão de dependências.
Recommendation: remover os imports não usados e mover o `import uuid` para o topo.

### [LOW] `print` no lugar de log
File: routes/task_routes.py:149
Description: há `print` em routes/task_routes.py:149, 153, 219 e 234, routes/user_routes.py:83,
89 e 147, services/notification_service.py:21 e 24, utils/helpers.py:39-41 e seed.py:93-96.
Impact: sem nível, sem destino configurável e sem correlação; o log de erro em :153 é a única
pista de falhas e vai para stdout sem contexto.
Recommendation: `logging` configurado no app factory.

### [LOW] Nomes de uma letra e construções não idiomáticas
File: routes/report_routes.py:33
Description: variáveis de laço `t`, `u`, `c`, `p`, `td` em routes/task_routes.py:16, 268 e 283 e
routes/report_routes.py:33, 55, 59 e 161; `overdue_count = overdue_count + 1` em vez de `+=`
(routes/task_routes.py:287, routes/report_routes.py:37 e 63); `type(tags) == list` em vez de
`isinstance` (routes/task_routes.py:141 e 210, utils/helpers.py:103);
`if cond: return True else: return False` em models/user.py:34-38, models/task.py:38-60 e
utils/helpers.py:21-23 e 52-55.
Impact: leitura mais lenta e revisão mais difícil.
Recommendation: nomes descritivos e formas idiomáticas de Python.

### [LOW] Recursos mal alocados e dependências declaradas sem uso
File: routes/report_routes.py:157
Description: os quatro endpoints de `/categories` (linhas 157, 167, 190 e 211) vivem no blueprint
de relatórios; nenhum blueprint tem `url_prefix` (app.py:18-20), então tudo fica na raiz sem
versionamento. As dependências `marshmallow`, `requests` e `python-dotenv` estão em
requirements.txt e nunca são importadas.
Impact: quem procura categorias não as encontra; a API não tem caminho de evolução por versão; o
ambiente instala pacotes que não são usados.
Recommendation: blueprint próprio para categorias, prefixo `/api/v1` quando houver janela para
mudança de contrato, e usar (ou remover) as dependências declaradas.

================================
Total: 25 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Confirmação

Resposta do usuário: **y** — a Fase 3 foi autorizada e executada. O resultado está em
`reports/logs/project-3-after.txt` e no README, seção Resultados.
