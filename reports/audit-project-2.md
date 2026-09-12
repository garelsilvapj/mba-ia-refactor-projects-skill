# Relatório de auditoria — Projeto 2 (`ecommerce-api-legacy`)

Saída das Fases 1 e 2 da skill `/refactor-arch`.

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js, CommonJS)
Framework:     Express ^4.18.2
Dependencies:  sqlite3 ^5.1.6 (driver com API de callbacks)
Domain:        LMS / plataforma de cursos com checkout (users, courses, enrollments,
               payments, audit_logs) — matrícula com autorização de pagamento
Architecture:  Monolítica — God Class AppManager concentra conexão de banco, DDL, seed,
               roteamento, regra de checkout e "gateway" de pagamento; 78% do código em um
               único arquivo
Source files:  3 files analyzed
DB tables:     users, courses, enrollments, payments, audit_logs (SQLite em memória)
Endpoints:     3 routes
Entry point:   npm start → node src/app.js (porta 3000, fixa em utils.js:6)
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript + Express
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 7 | HIGH: 5 | MEDIUM: 7 | LOW: 4

## Findings

### [CRITICAL] Credenciais de produção hardcoded no código-fonte
File: src/utils.js:1-7
Description: o objeto `config` traz a senha do banco (`senha_super_secreta_prod_123`), a chave
do gateway de pagamento em modo produção (`pk_live_1234567890abcdef`), o usuário de SMTP e a
porta, todos como literais. Nada no projeto lê `process.env`.
Impact: a chave `pk_live` permite movimentar cobranças reais e está versionada no git; não há
como ter valores diferentes por ambiente.
Recommendation: mover tudo para variáveis de ambiente com `.env.example`, e rotacionar
imediatamente a chave do gateway e a senha do banco, que devem ser consideradas comprometidas.

### [CRITICAL] God Class concentra banco, rotas, regra de negócio e pagamento
File: src/AppManager.js:4-139
Description: a classe `AppManager` abre a conexão SQLite no construtor (linha 7), cria o schema
e o seed (10-23), registra as três rotas (25-137), implementa a regra de checkout (28-78), a
autorização do pagamento (46) e a agregação do relatório financeiro (80-129).
Impact: nada é testável isoladamente; qualquer alteração em uma rota arrisca as demais; o
arquivo concentra 78% do código do projeto.
Recommendation: separar em config, models por domínio, services (checkout, relatório, gateway),
controllers e rotas.

### [CRITICAL] Número do cartão e chave do gateway gravados em log
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)`
escreve o número completo do cartão e a chave de produção na saída padrão a cada checkout.
Impact: violação direta de PCI-DSS; qualquer pessoa com acesso ao log obtém cartões de clientes
e a chave do gateway.
Recommendation: nunca logar o PAN nem segredos; registrar no máximo os quatro últimos dígitos,
por um logger com níveis.

### [CRITICAL] Hash de senha caseiro e reversível
File: src/utils.js:17-23
Description: `badCrypto()` concatena 10.000 vezes os dois primeiros caracteres do base64 da
senha e devolve os 10 primeiros caracteres do resultado. É usado em AppManager.js:68 para
gravar a senha do usuário criado no checkout.
Impact: base64 é reversível e o truncamento gera colisões, então o valor gravado não protege a
senha — na prática as senhas estão em claro e qualquer usuário pode colidir com outro.
Recommendation: `bcrypt` ou `crypto.scrypt` com salt por usuário e comparação em tempo
constante.

### [CRITICAL] Senha em texto puro no seed e formatos inconsistentes na mesma coluna
File: src/AppManager.js:18
Description: o seed insere o usuário `leonan@fullcycle.com.br` com a senha literal `'123'`,
enquanto o cadastro do checkout grava o resultado de `badCrypto` (AppManager.js:68). A coluna
`pass` guarda dois formatos diferentes.
Impact: senha real versionada no repositório; qualquer verificação futura de senha falha ou
precisa aceitar os dois formatos.
Recommendation: gerar hash também no seed e padronizar a coluna.

### [CRITICAL] Relatório financeiro exposto sem autenticação
File: src/AppManager.js:80-129
Description: `GET /api/admin/financial-report` devolve receita por curso e a lista de alunos com
os valores pagos, sem qualquer verificação de identidade ou papel. Não existe autenticação em
nenhuma rota do projeto.
Impact: qualquer chamador anônimo obtém o faturamento da empresa e dados pessoais dos alunos.
Recommendation: exigir autenticação e papel de administrador; o dado financeiro não pode
trafegar em rota pública.

### [CRITICAL] Checkout não verifica a senha de usuário existente
File: src/AppManager.js:40
Description: quando o e-mail já existe, o fluxo desvia para `processPaymentAndEnroll(user.id)`
(linha 74) sem nunca comparar a senha recebida em `req.body.pwd`. Confirmado na execução: um
checkout com o e-mail do usuário do seed e senha arbitrária é aceito e gera a matrícula 3.
Impact: qualquer pessoa matricula terceiros e associa cobranças à conta de outro usuário,
apenas conhecendo o e-mail.
Recommendation: autenticar antes do checkout (verificação de senha ou token) e associar a
matrícula ao usuário autenticado, nunca ao e-mail enviado no corpo.

### [HIGH] Regra de checkout inteira dentro do handler HTTP e sem transação
File: src/AppManager.js:28-78
Description: o handler faz validação, busca do curso, criação de usuário, autorização de
pagamento, matrícula, registro do pagamento, log de auditoria e cache, tudo aninhado. As
escritas das linhas 50, 54 e 57 são independentes: se a inserção do pagamento falhar (55), a
matrícula já gravada (50) permanece órfã.
Impact: regra de negócio impossível de testar sem HTTP e sem banco; falha parcial deixa aluno
matriculado sem pagamento correspondente.
Recommendation: extrair um `CheckoutService` que execute matrícula, pagamento e auditoria em
uma transação única, com rollback no erro.

### [HIGH] Regra de autorização de pagamento embutida no controller
File: src/AppManager.js:46
Description: a decisão de aprovar a cobrança é `cc.startsWith("4") ? "PAID" : "DENIED"`, escrita
dentro do handler, sem abstração de gateway.
Impact: a regra mais crítica do negócio não é testável nem substituível; integrar um gateway
real exige reescrever o handler.
Recommendation: criar uma interface de gateway de pagamento injetada no service, com
implementação real e dublê para teste.

### [HIGH] Acoplamento a implementações concretas, sem injeção de dependência
File: src/AppManager.js:5-8
Description: o construtor instancia a própria conexão (`new sqlite3.Database(':memory:')`); o
módulo importa `config`, `logAndCache` e `badCrypto` diretamente (linha 2); `app.js:8-10` cria o
manager e lhe entrega a instância do Express.
Impact: impossível trocar o banco, o gateway ou o cache; impossível testar sem subir a
aplicação inteira.
Recommendation: receber as dependências por parâmetro e montá-las em um composition root no
entry point.

### [HIGH] Estado global mutável exportado pelo módulo de utilidades
File: src/utils.js:9-10
Description: `globalCache` é um objeto de módulo que cresce sem limite a cada checkout
(`logAndCache`, linhas 12-15) e `totalRevenue` é um número exportado por valor (linha 25), de
modo que qualquer mutação é invisível para quem importa — é estado morto que aparenta funcionar.
Impact: vazamento de memória no processo; estado compartilhado entre requisições e usuários;
valor de receita que nunca reflete a realidade.
Recommendation: derivar a receita do banco por consulta e, se o cache for necessário, usar uma
estrutura com limite e expiração, fora do escopo de módulo.

### [HIGH] Inicialização do schema sem verificação de erro e sem sincronização com o boot
File: src/AppManager.js:10-23
Description: `initDb()` dispara cinco `CREATE TABLE` e quatro `INSERT` sem callback de erro
(linhas 12-21); `app.js:9-12` chama `initDb()` e imediatamente abre a porta, sem esperar a
conclusão.
Impact: falha de DDL passa despercebida e a aplicação sobe com o banco incompleto; requisições
que chegam antes do schema falham de forma intermitente.
Recommendation: tornar a inicialização assíncrona e aguardada, com erro propagado, antes do
`listen`.

### [MEDIUM] Query N+1 no relatório financeiro
File: src/AppManager.js:83-127
Description: uma consulta lista os cursos (83), uma consulta de matrículas por curso (92), e
para cada matrícula duas consultas — usuário (104) e pagamento (106). O custo é
1 + N + 2×M idas ao banco.
Impact: o endpoint degrada de forma multiplicativa com o número de cursos e alunos.
Recommendation: uma única query com `LEFT JOIN` entre cursos, matrículas, usuários e pagamentos,
com `SUM` agregando a receita no banco.

### [MEDIUM] Coordenação assíncrona manual por contadores
File: src/AppManager.js:86-122
Description: o relatório controla o término com os contadores `coursesPending` (86, 97, 120) e
`enrPending` (93, 117), decrementados dentro de callbacks aninhados. Se um callback falhar, o
contador nunca zera e a requisição fica pendurada; decrementos concorrentes podem chamar
`res.json` duas vezes (`ERR_HTTP_HEADERS_SENT`). Confirmado na execução: a ordem dos cursos no
JSON muda entre chamadas idênticas.
Impact: resposta não determinística, risco de travar a requisição e de responder duas vezes.
Recommendation: substituir por `Promise.all` sobre consultas promisificadas, ou por uma única
query agregada, com ordenação explícita.

### [MEDIUM] Exclusão de usuário ignora erro, mente no status e deixa órfãos
File: src/AppManager.js:131-137
Description: o callback de `DELETE FROM users` recebe `err` e não o utiliza (133-135); a resposta
é sempre 200 com um texto que admite o problema. Confirmado na execução: `DELETE /api/users/999`
devolve 200 mesmo sem usuário. Matrículas e pagamentos permanecem apontando para o id removido,
e não há chave estrangeira declarada.
Impact: o cliente não distingue sucesso de falha; o relatório passa a exibir `Unknown` no lugar
do aluno, com o pagamento ainda contabilizado.
Recommendation: verificar o erro e `changes`, devolver 404 quando nada foi removido, declarar
chaves estrangeiras e decidir entre cascata ou exclusão lógica.

### [MEDIUM] Validação de entrada mínima
File: src/AppManager.js:35
Description: a única checagem é `if (!u || !e || !cid || !cc)`. A senha não é validada e recebe
o valor padrão `"123456"` quando ausente (linha 68); não há verificação de formato de e-mail,
de tipo de `c_id` nem de formato do cartão.
Impact: usuários criados com senha padrão conhecida; dados inconsistentes no banco; o `c_id`
chega ao SQL sem conversão de tipo.
Recommendation: validar o corpo na borda com um schema, devolvendo 400 com os campos inválidos.

### [MEDIUM] Tratamento de erro duplicado, sem middleware central
File: src/AppManager.js:38
Description: o padrão `res.status(5xx).send("<texto>")` se repete nas linhas 38, 41, 51, 55, 70 e
84, sempre em texto puro, enquanto o caminho de sucesso devolve JSON (linha 60). Não há
`app.use((err, req, res, next) => ...)` em lugar nenhum e nenhum handler chama `next(err)`.
Impact: o cliente recebe formatos diferentes conforme o resultado; nenhum erro é registrado com
contexto; a mesma correção precisa ser replicada em seis pontos.
Recommendation: middleware de erro de quatro argumentos registrado por último, com hierarquia de
exceções de domínio e envelope JSON único.

### [MEDIUM] APIs e padrões deprecated
File: src/AppManager.js:37-77
Description: a varredura de APIs obsoletas encontrou três itens. (1) Uso da API de callbacks do
`sqlite3` formando uma pirâmide de cinco níveis (37-77), em vez de promises com `async/await`.
(2) `const self = this` na linha 26, idioma pré-ES6 usado apenas para alcançar `this.lastID`
dentro de callbacks com `function`. (3) Criptografia caseira em utils.js:17-23, no lugar do
módulo `crypto` moderno. Registrado também o que **não** foi encontrado: o projeto já usa
`express.json()` (app.js:6) em vez de `bodyParser.json()`, e `Buffer.from()` (utils.js:20) em
vez de `new Buffer()`.
Impact: código difícil de ler e de tratar erro; `this` ambíguo; o padrão de callbacks é a raiz
da coordenação manual e do risco de resposta dupla.
Recommendation: promisificar o driver com `util.promisify` e migrar para `async/await`, o que
elimina `self` e os callbacks aninhados; usar `crypto.scrypt`/`bcrypt` para senha.

### [MEDIUM] Configuração fixa, sem separação por ambiente
File: src/utils.js:1-7
Description: `config` é um literal; a porta 3000 vem da linha 6 e é usada em `app.js:12`. Não há
`process.env`, `dotenv`, nem `.env.example`.
Impact: mudar porta, banco ou chave exige editar o código; se a porta estiver ocupada o processo
aborta com `EADDRINUSE` sem alternativa.
Recommendation: módulo de config lendo `process.env` com defaults não sensíveis.

### [LOW] Nomes crípticos, inclusive no contrato da API
File: src/AppManager.js:29-33
Description: as variáveis do handler são `u`, `e`, `p`, `cid`, `cc`; os campos do corpo aceitos
pela API são `usr`, `eml`, `pwd`, `c_id`. O nome abreviado vaza para o contrato público.
Impact: leitura difícil e API pouco clara para quem a consome.
Recommendation: nomes completos internamente e campos descritivos no contrato, mantendo os
antigos apenas se houver clientes em produção.

### [LOW] Magic numbers e strings de status sem constantes
File: src/utils.js:19
Description: o laço de 10.000 iterações (19), os cortes `substring(0, 2)` (20) e
`substring(0, 10)` (22) não têm nome nem explicação; as strings `"PAID"` e `"DENIED"` aparecem
soltas em AppManager.js:46, 48 e 108.
Impact: intenção ilegível; comparar status por literal em pontos distintos convida a divergência.
Recommendation: constantes nomeadas e um enum congelado para o status de pagamento.

### [LOW] Schema e seed embutidos como strings no código da aplicação
File: src/AppManager.js:10-23
Description: o DDL das cinco tabelas e os dados iniciais estão em literais dentro de `initDb`.
Não há migrations, nem separação entre schema e seed, e `active INTEGER` é usado como booleano.
Impact: evoluir o schema exige editar o código da aplicação; não há histórico de alterações.
Recommendation: separar schema e seed em módulos próprios, com migrations quando o banco deixar
de ser em memória.

### [LOW] Projeto sem rede de proteção
File: package.json:6-8
Description: o único script é `start`; não há `test`, `dev` nem `lint`, nenhuma dependência de
desenvolvimento, nenhum teste e nenhum linter.
Impact: nada protege uma refatoração; regressões só aparecem em execução manual.
Recommendation: adicionar scripts de teste e lint e, no mínimo, um teste de fumaça dos três
endpoints.

================================
Total: 23 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Confirmação

Resposta do usuário: **y** — a Fase 3 foi autorizada e executada. O resultado está em
`reports/logs/project-2-after.txt` e no README, seção Resultados.
