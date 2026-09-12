# Catálogo de anti-patterns (Fase 2)

19 anti-patterns com **sinais de detecção acionáveis**, severidade e recomendação. Rode os sinais
de cada entrada contra os arquivos-fonte; confirme cada acerto abrindo o arquivo antes de virar
finding. Sinal que não se confirma na leitura **não vira finding**.

## Escala de severidade

| Severidade | Critério | Exemplos |
|---|---|---|
| **CRITICAL** | Falha grave de arquitetura ou segurança: impede o funcionamento correto, expõe dados sensíveis ou viola completamente a separação de responsabilidades. | Credenciais hardcoded, SQL Injection, God Class com DB + regra + roteamento, senha em texto puro. |
| **HIGH** | Violação forte de MVC/SOLID que dificulta muito manutenção e testes. | Regra de negócio dentro do controller, acoplamento sem injeção de dependência, estado global mutável. |
| **MEDIUM** | Padronização, duplicação ou performance moderada. | Query N+1, middleware mal usado, validação ausente nas rotas, API deprecated. |
| **LOW** | Legibilidade. | Nomes ruins, magic numbers, imports mortos, resposta inconsistente. |

**Desempate:** qualquer problema de segurança que exponha dados é no mínimo CRITICAL. Mistura de
camadas é CRITICAL quando é a espinha do projeto e HIGH quando é pontual. Um mesmo arquivo pode
gerar vários findings de severidades diferentes.

---

## CRITICAL

### AP-01 — Hardcoded Credentials

Segredo (senha, chave de API, `SECRET_KEY`, credencial de SMTP/banco) literal no código-fonte.

**Sinais:**
```bash
grep -rniE "(secret|password|passwd|pwd|api_?key|token|private_key)[\"']?\s*[:=]\s*[\"'][^\"']{4,}" --include='*.py' --include='*.js' --include='*.ts' --include='*.php' .
grep -rniE "sk_live|pk_live|AKIA[0-9A-Z]{16}|Bearer [A-Za-z0-9._-]{20,}" .
grep -rn "smtp" --include='*.py' --include='*.js' .
```
Confirme que é um valor literal, não leitura de ambiente nem placeholder de exemplo.

**Impact:** segredo versionado no histórico do git; sessões forjáveis; acesso a serviços de
terceiros; impossível ter valores distintos por ambiente.
**Recommendation:** mover para variável de ambiente lida por um módulo de config, com
`.env.example` documentando cada chave. Rotacionar o segredo exposto.

### AP-02 — SQL Injection

Entrada do usuário concatenada ou interpolada na string da query.

**Sinais:**
```bash
grep -rnE "(execute|query|run|all|get)\s*\(\s*f[\"']" --include='*.py' .        # f-string em query
grep -rnE "(SELECT|INSERT|UPDATE|DELETE)[^\"']*[\"']\s*\+|\+\s*[\"'][^\"']*(WHERE|VALUES)" --include='*.py' --include='*.js' .
grep -rnE "\.(execute|query)\s*\(\s*[\`\"'].*\$\{" --include='*.js' --include='*.ts' .   # template literal
grep -rn "%s\" %\|\.format(" --include='*.py' . | grep -iE "select|insert|update|delete"
```
Query com placeholder (`?`, `%s` + tupla de parâmetros, `:nome`) **não** é injection.

**Impact:** leitura, alteração ou destruição de qualquer dado; bypass de login com `' OR '1'='1`.
**Recommendation:** query parametrizada com placeholders do driver; nunca construir SQL por
concatenação. Identificadores dinâmicos (nome de tabela/coluna) vêm de allowlist.

### AP-03 — God Class / God Module

Um único arquivo ou classe concentra conexão de banco, DDL, queries de vários domínios,
regra de negócio, roteamento e formatação.

**Sinais:**
```bash
wc -l <fontes> | sort -rn | head          # arquivos muito acima da mediana
grep -c "def \|function \|=>" <arquivo>   # densidade de responsabilidades
```
Confirme cruzando: o mesmo arquivo tem (a) SQL/ORM, (b) decisão de negócio e (c) `route`/`app.get`
ou DDL de 3+ tabelas.

**Impact:** impossível testar em isolamento; qualquer mudança arrisca todo o sistema; merge
conflicts constantes.
**Recommendation:** separar por domínio em models (dados), services (regra) e controllers
(fluxo HTTP).

### AP-04 — Senha em texto puro ou hash inadequado

Senha gravada como veio, ou "hasheada" com MD5/SHA1/base64/algoritmo caseiro, sem salt.

**Sinais:**
```bash
grep -rn "hashlib.md5\|hashlib.sha1\|createHash('md5')\|createHash(\"sha1\")" --include='*.py' --include='*.js' .
grep -rniE "senha|password" --include='*.py' --include='*.js' . | grep -iE "insert|values|=\s*(data|body|req)"
grep -rn "Buffer.from(.*).toString('base64')\|b64encode" --include='*.js' --include='*.py' .
```
Também é sinal: comparação de senha com `==` direto, sem função de verificação.

**Impact:** vazamento do banco expõe as senhas reais dos usuários (e de outros serviços por
reuso); MD5/SHA1 sem salt caem em rainbow table; base64 é reversível.
**Recommendation:** `bcrypt`, `argon2` ou `werkzeug.security.generate_password_hash`;
comparação por `check_password_hash` (tempo constante).

### AP-05 — Exposição de dados sensíveis na resposta

O endpoint devolve senha/hash, segredo de configuração, dados de cartão ou dados de terceiros
sem autorização. Inclui log de PAN de cartão e de chave de API.

**Sinais:**
```bash
grep -rn "password\|senha\|secret_key\|token" --include='*.py' --include='*.js' . | grep -iE "to_dict|jsonify|res\.json|serialize|dict\("
grep -rn "console.log\|print(" --include='*.js' --include='*.py' . | grep -iE "card|cc|senha|password|secret|key"
```
Cheque especialmente `to_dict()`/`toJSON()` dos modelos de usuário e rotas administrativas.

**Impact:** qualquer chamador anônimo coleta credenciais; log com PAN viola PCI-DSS.
**Recommendation:** serializar por allowlist de campos; DTO/schema de saída sem campos
sensíveis; nunca logar segredo nem dado de cartão.

### AP-06 — Endpoint administrativo perigoso e sem autenticação

Rota que executa SQL arbitrário, apaga o banco, expõe relatório financeiro ou dados de todos os
usuários, sem qualquer verificação de identidade.

**Sinais:**
```bash
grep -rniE "route\(['\"].*(admin|debug|reset|internal|raw|exec)" --include='*.py' --include='*.js' .
grep -rn "request.json\['sql'\]\|req.body.sql\|eval(\|exec(" --include='*.py' --include='*.js' .
```
Depois pergunte: existe decorator/middleware de auth em alguma rota? Se não existe em lugar
nenhum, todo endpoint sensível vira finding.

**Impact:** execução de comandos arbitrários no banco; destruição de dados; vazamento
financeiro — sem rastro nem autor.
**Recommendation:** remover o endpoint. Se for necessário, exigir autenticação + papel de
administrador e registrar auditoria.

---

## HIGH

### AP-07 — Business Logic in Controller

Cálculo, decisão de negócio, regra de preço/desconto/autorização ou máquina de estados dentro do
handler HTTP.

**Sinais:** no corpo de uma função de rota, procure aritmética sobre dados de domínio, `if` sobre
regra de negócio, listas de status válidos, e mais de ~20 linhas de corpo.
```bash
grep -rn -A25 "@app.route\|@bp.route\|router\.\(get\|post\)" --include='*.py' --include='*.js' . | grep -nE "total\s*[*+]|desconto|discount|\* 0\.|startsWith\(|status\s*=="
```

**Impact:** regra não reaproveitável fora do HTTP, não testável sem subir a aplicação, e
duplicada assim que surge um segundo ponto de entrada.
**Recommendation:** extrair para service/model; o controller fica com parse de request,
chamada e formatação da resposta.

### AP-08 — Tight Coupling / ausência de injeção de dependência

Camadas se amarram a implementações concretas por import global; a classe cria a própria conexão
de banco; não há como substituir a dependência em teste.

**Sinais:**
```bash
grep -rn "new sqlite3.Database\|sqlite3.connect\|createConnection\|new PrismaClient" --include='*.py' --include='*.js' . | grep -v config
grep -rn "^from database import\|^import models\|require('./db')" --include='*.py' --include='*.js' .
```
Sinal decisivo: o construtor/módulo instancia a dependência em vez de recebê-la.

**Impact:** impossível testar com dublê; trocar banco ou gateway exige mexer na regra de negócio;
o teste precisa de infraestrutura real.
**Recommendation:** receber a dependência por parâmetro/construtor (composition root no entry
point); depender de interface, não de implementação.

### AP-09 — Mutable Global State

Variável de módulo mutável compartilhada entre requisições: cache global, contador, conexão
única, lista em memória.

**Sinais:**
```bash
grep -rnE "^(let|var) [a-zA-Z_]+ *= *(\{\}|\[\]|0)" --include='*.js' .
grep -rnE "^[a-z_]+ *= *(\{\}|\[\]|None|0)$" --include='*.py' .
grep -rn "global \|check_same_thread=False" --include='*.py' .
```

**Impact:** estado vaza entre requisições e usuários; comportamento não determinístico sob
concorrência; cresce sem limite (vazamento de memória); impossível escalar em múltiplos
processos.
**Recommendation:** estado por requisição ou em store externo (banco/cache); conexão com ciclo
de vida por requisição; primitivo exportado por valor nunca funciona como estado compartilhado.

### AP-10 — Ausência de camada de serviço (rotas/modelos gordos)

Existe `routes/` e `models/`, mas as rotas fazem consulta ao ORM, agregação, serialização e
regra; ou o model virou depósito de relatório. As pastas existem, a separação não.

**Sinais:**
```bash
grep -rn "db.session\|\.query\.\|Model.query\|findAll\|aggregate" --include='*.py' --include='*.js' routes/ src/routes/ 2>/dev/null
wc -l routes/*.* services/*.* 2>/dev/null    # rotas enormes e services vazios/mortos
```
Sinal complementar: arquivo em `services/` que nunca é importado por ninguém.

**Impact:** a organização de pastas dá falsa sensação de arquitetura; a regra continua
inalcançável para teste e reuso.
**Recommendation:** controllers finos, services com a regra, repositórios/models com o acesso a
dados; rotas apenas mapeiam URL → controller.

### AP-11 — Operação de escrita sem transação

Vários INSERT/UPDATE que precisam ser atômicos, com commit único ao fim, `return` no meio sem
rollback, ou sem transação nenhuma.

**Sinais:**
```bash
grep -rn -B5 -A20 "INSERT INTO\|db.session.add\|\.create(" --include='*.py' --include='*.js' . | grep -nE "return|commit|rollback"
grep -rn "rollback" --include='*.py' --include='*.js' .   # ausência total é o sinal
```

**Impact:** falha no meio deixa dados inconsistentes: pedido sem itens, matrícula sem pagamento,
estoque baixado sem venda. Também há corrida entre checagem e escrita (TOCTOU).
**Recommendation:** envolver a unidade de trabalho em transação com rollback no erro; validar e
reservar recurso dentro da mesma transação.

---

## MEDIUM

### AP-12 — Query N+1

Uma consulta por item dentro de laço, quando um JOIN, `IN (...)` ou eager loading resolveria.

**Sinais:**
```bash
grep -rn -A8 "for .* in \|\.forEach(\|for (const" --include='*.py' --include='*.js' . | grep -nE "execute\(|\.query\.|query\(|findOne|\.get\("
```
Confirme que a consulta usa a variável do laço.

**Impact:** latência cresce linearmente com o volume; o endpoint degrada em produção com dados
reais.
**Recommendation:** JOIN único, `WHERE id IN (...)` em lote, ou eager loading do ORM
(`selectinload`/`include`/`with`).

### AP-13 — Validação de entrada ausente ou fraca

O handler usa o corpo da requisição sem checar presença, tipo, formato ou faixa.

**Sinais:**
```bash
grep -rn "request.get_json\|request.json\|req.body\|request.args" --include='*.py' --include='*.js' . | head -50
grep -rn "int(\|float(\|parseInt(" --include='*.py' --include='*.js' . | grep -iE "args|body|params|query"
```
Depois cheque, para cada ponto: há verificação de campo obrigatório? de tipo? de formato
(e-mail, cor, cartão)? Acesso direto `body["campo"]` sem `.get` é sinal claro.

**Impact:** dados inconsistentes no banco; `TypeError`/`ValueError` vira HTTP 500 em vez de 400;
superfície de ataque maior.
**Recommendation:** validar na borda com schema (marshmallow/pydantic/zod/joi) ou função de
validação dedicada; responder 400 com mensagem clara.

### AP-14 — Error handling espalhado / middleware mal usado

`try/except` idêntico copiado em cada handler, `except:` nu engolindo erro, mensagem crua do
erro devolvida ao cliente, ausência de handler global.

**Sinais:**
```bash
grep -rcn "try:" --include='*.py' .              # muitos try por arquivo
grep -rn "except:\|except Exception" --include='*.py' .
grep -rn "str(e)\|err.message\|error.toString()" --include='*.py' --include='*.js' . | grep -iE "jsonify|res\.(json|send)"
grep -rn "errorhandler\|app.use((err" --include='*.py' --include='*.js' .   # ausência é o sinal
```

**Impact:** detalhe interno (SQL, caminho, schema) vaza ao cliente; erro real some sem log;
resposta de erro inconsistente entre rotas; código duplicado em toda rota.
**Recommendation:** handler de erro centralizado (`@app.errorhandler` / middleware Express de 4
argumentos) + hierarquia de exceções de domínio; logar o erro, devolver mensagem genérica com
status correto.

### AP-15 — Deprecated API

Uso de API obsoleta, removida ou desencorajada pela versão em uso. **Sempre rode esta seção** e
reporte o equivalente moderno de cada acerto.

**Sinais e substitutos:**

| Ecossistema | API deprecated | Equivalente moderno | Detecção |
|---|---|---|---|
| Python | `datetime.utcnow()` / `datetime.utcfromtimestamp()` | `datetime.now(timezone.utc)` | `grep -rn "utcnow()\|utcfromtimestamp("` |
| Python | `hashlib.md5(...)` / `sha1` para senha | `werkzeug.security` / `bcrypt` / `argon2` | `grep -rn "hashlib.md5\|hashlib.sha1"` |
| Flask | `@app.before_first_request` (removido na 2.3) | app factory + `with app.app_context()` | `grep -rn "before_first_request"` |
| Flask | `flask.Markup`, `app.json_encoder` | `markupsafe.Markup`, `app.json_provider_class` | `grep -rn "flask.Markup\|json_encoder"` |
| SQLAlchemy | `Model.query.get(id)` (legado 2.0) | `db.session.get(Model, id)` | `grep -rn "\.query\.get("` |
| SQLAlchemy | `Model.query` (estilo 1.x) | `db.session.execute(select(Model))` | `grep -rn "\.query\."` |
| Python | `imp`, `distutils`, `asyncio.get_event_loop()` sem loop | `importlib`, `packaging`, `asyncio.run()` | `grep -rn "^import imp\|distutils\|get_event_loop()"` |
| Python 3.12 | adaptadores default de data do `sqlite3` | adapter/converter explícito | `grep -rn "detect_types\|PARSE_DECLTYPES"` |
| Node | `new Buffer(...)` | `Buffer.from(...)` / `Buffer.alloc(...)` | `grep -rn "new Buffer("` |
| Node | `url.parse()` | `new URL()` | `grep -rn "url.parse("` |
| Node | `crypto.createCipher` | `crypto.createCipheriv` | `grep -rn "createCipher("` |
| Node | `fs.exists`, `domain`, `require('sys')` | `fs.access`/`fs.existsSync`, `AsyncLocalStorage` | `grep -rn "fs.exists(\|require('domain')"` |
| Express | `body-parser` / `bodyParser.json()` | `express.json()` (embutido desde 4.16) | `grep -rn "body-parser\|bodyParser\."` |
| Express | `res.send(status)`, `res.json(status, obj)` | `res.sendStatus(status)`, `res.status(s).json(obj)` | `grep -rn "res.send([0-9]"` |
| Node/JS | API de callbacks para I/O, `const self = this` | `promises` + `async/await`, arrow functions | `grep -rn "function *(err\|const self = this"` |
| JS | `String.prototype.substr` | `slice` / `substring` | `grep -rn "\.substr("` |
| JS | `require` de crypto caseiro | `crypto.scrypt` / `bcrypt` | ver AP-04 |
| PHP | `mysql_*`, `each()` | `PDO` / `mysqli`, `foreach` | `grep -rn "mysql_query\|each("` |

**Impact:** quebra no próximo upgrade de runtime/framework; avisos de depreciação em produção;
frequentemente carrega também um problema de correção (datas naive, hash fraco).
**Recommendation:** substituir pelo equivalente moderno da tabela, na mesma refatoração.

### AP-16 — Duplicação de código

Bloco de lógica repetido em 3+ lugares: mesma validação, mesma serialização, mesma consulta,
mesma regra de "vencido/ativo".

**Sinais:**
```bash
grep -rn "<trecho característico>" --include='*.py' --include='*.js' . | wc -l
```
Sinal forte: existe um método no model (`is_overdue()`, `to_dict()`) que faz exatamente isso e
**nunca é chamado**, enquanto a lógica está copiada nas rotas.

**Impact:** correção precisa ser aplicada N vezes; as cópias divergem com o tempo.
**Recommendation:** extrair para função/método único e usar em todos os pontos; remover as
cópias.

---

## LOW

### AP-17 — Magic numbers e magic strings

Números e literais de negócio soltos no código: limiares, percentuais, listas de status válidos,
papéis de usuário, faixas de prioridade.

**Sinais:**
```bash
grep -rnE "[^.\w]([0-9]{3,}|0\.[0-9]+)[^.\w]" --include='*.py' --include='*.js' . | grep -v test
grep -rnE "\[[\"'](pending|done|active|admin|PAID|DENIED)" --include='*.py' --include='*.js' .
```

**Impact:** intenção ilegível; mudança de regra exige caçar o valor em vários arquivos; cópias
divergem.
**Recommendation:** constantes nomeadas ou enum em módulo de config/domínio, com fonte única.

### AP-18 — Nomenclatura ruim e código morto

Variáveis de uma letra, abreviações opacas (`usr`, `eml`, `pwd`, `c_id`), sombra de builtin
(`id`, `type`), imports nunca usados, funções nunca chamadas, `print` como log.

**Sinais:**
```bash
grep -rnE "\b(let|const|var|def) (u|e|p|c|t|x|d) *[=(]" --include='*.js' --include='*.py' .
grep -rn "print(\|console.log(" --include='*.py' --include='*.js' . | grep -v test
python -m pyflakes .   ou   npx eslint --no-eslintrc --env node --rule '{"no-unused-vars":"warn"}' .
```

**Impact:** leitura lenta, revisão difícil, código morto que confunde quem chega depois; `print`
não tem nível nem destino configurável e às vezes registra dado pessoal.
**Recommendation:** nomes que digam o papel do valor; remover import/função morta; trocar
`print`/`console.log` por logger configurado.

### AP-19 — Respostas e status codes inconsistentes

Envelope diferente por rota (`{"sucesso": ...}` em uma, objeto cru em outra, texto puro na
terceira), erro de validação com 500, recurso inexistente com 200.

**Sinais:**
```bash
grep -rn "jsonify(\|res.json(\|res.send(" --include='*.py' --include='*.js' . | head -60
grep -rn "status(200)\|, 200" --include='*.py' --include='*.js' . | grep -iE "error|erro|not found"
```

**Impact:** o cliente precisa de tratamento especial por rota; erro silencioso passa por sucesso.
**Recommendation:** contrato único de resposta e de erro; status semântico (400 validação,
401/403 auth, 404 ausente, 409 conflito, 500 só para falha inesperada).

---

## Checklist de encerramento da Fase 2

- [ ] Todos os 19 anti-patterns foram procurados (inclusive AP-15, deprecated).
- [ ] Todo finding tem `arquivo:linha` conferido no arquivo.
- [ ] Findings ordenados CRITICAL → HIGH → MEDIUM → LOW.
- [ ] Pelo menos 5 findings e pelo menos 1 CRITICAL ou HIGH.
- [ ] Relatório salvo em `reports/audit-project-N.md`.
- [ ] Pergunta de confirmação feita; nenhum arquivo modificado até aqui.
