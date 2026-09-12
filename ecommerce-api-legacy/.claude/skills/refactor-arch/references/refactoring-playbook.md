# Playbook de refatoração (Fase 3)

15 transformações concretas, uma por anti-pattern do catálogo, com código **antes/depois**.
Aplique na ordem de severidade. Os exemplos estão em Python/Flask e Node/Express; a forma é a
mesma nas outras stacks.

| # | Transformação | Resolve |
|---|---|---|
| T-01 | Extrair configuração para o ambiente | AP-01 |
| T-02 | Parametrizar query | AP-02 |
| T-03 | Quebrar God Class em camadas | AP-03 |
| T-04 | Substituir hash caseiro por KDF | AP-04 |
| T-05 | Serializar por allowlist | AP-05 |
| T-06 | Remover ou proteger endpoint administrativo | AP-06 |
| T-07 | Extrair regra de negócio para service | AP-07 |
| T-08 | Injetar dependência | AP-08 |
| T-09 | Eliminar estado global mutável | AP-09 |
| T-10 | Envolver a unidade de trabalho em transação | AP-11 |
| T-11 | Eliminar N+1 com JOIN ou carga em lote | AP-12 |
| T-12 | Validar na borda | AP-13 |
| T-13 | Centralizar o tratamento de erros | AP-14 |
| T-14 | Substituir API deprecated | AP-15 |
| T-15 | Extrair magic numbers para constantes | AP-17 |

---

## T-01 — Extrair configuração para o ambiente

**Antes**
```python
app = Flask(__name__)
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
DB = "loja.db"
```

**Depois** — `config.py`
```python
import os


class Config:
    SECRET_KEY = os.environ["SECRET_KEY"]          # obrigatório: falha rápido se ausente
    DB_PATH = os.environ.get("DB_PATH", "loja.db")  # opcional: default seguro
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

    # constantes de domínio moram aqui, não espalhadas pelo código
    DESCONTO_MINIMO = 500.0
    DESCONTO_PERCENTUAL = 0.10
```
`.env.example`
```
SECRET_KEY=troque-por-um-valor-aleatorio
DB_PATH=loja.db
DEBUG=false
```
No entry point: `app.config.from_object(Config)`.

Em Node, o mesmo com `src/config/index.js`:
```js
module.exports = {
  port: Number(process.env.PORT || 3000),
  dbFile: process.env.DB_FILE || ':memory:',
  paymentApiKey: process.env.PAYMENT_API_KEY || '',
};
```

**Regras:** segredo sem default; valor não sensível pode ter default; o `.env` real nunca é
versionado; o segredo que estava no código é considerado comprometido e deve ser rotacionado.

---

## T-02 — Parametrizar query

**Antes**
```python
rows = conn.execute(f"SELECT * FROM produtos WHERE nome LIKE '%{nome}%'").fetchall()
user = conn.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'").fetchone()
```

**Depois**
```python
rows = conn.execute("SELECT * FROM produtos WHERE nome LIKE ?", (f"%{nome}%",)).fetchall()
user = conn.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
```
O `%` do LIKE entra **no parâmetro**, não na string da query.

**Filtro dinâmico** — construa a cláusula com placeholders, nunca com valores:
```python
clauses, params = ["1=1"], []
if categoria:
    clauses.append("categoria = ?")
    params.append(categoria)
if preco_min is not None:            # `is not None`, para não descartar 0
    clauses.append("preco >= ?")
    params.append(preco_min)
sql = f"SELECT * FROM produtos WHERE {' AND '.join(clauses)}"   # só identificadores nossos
rows = conn.execute(sql, params).fetchall()
```

Node:
```js
db.all('SELECT * FROM courses WHERE title LIKE ?', [`%${q}%`], cb);
```

**Ordenação dinâmica** (não aceita placeholder) sai de allowlist:
```python
ORDENACOES = {"preco": "preco", "nome": "nome"}
coluna = ORDENACOES.get(param, "id")
```

---

## T-03 — Quebrar God Class em camadas

**Antes** — `AppManager.js` com conexão, DDL, rotas, regra e gateway de pagamento.
```js
class AppManager {
  constructor() { this.db = new sqlite3.Database(':memory:'); }
  initDb() { this.db.run('CREATE TABLE users ...'); /* + 4 tabelas */ }
  setupRoutes(app) {
    app.post('/api/checkout', (req, res) => { /* 50 linhas de regra + SQL */ });
  }
}
```

**Depois** — uma responsabilidade por arquivo.
```js
// models/db.js — só conexão e schema
const { open } = require('./sqliteAsync');
async function createDb(file) { const db = await open(file); await migrate(db); return db; }

// models/userModel.js — só dados de usuário
class UserModel {
  constructor(db) { this.db = db; }
  findByEmail(email) { return this.db.get('SELECT * FROM users WHERE email = ?', [email]); }
  create({ name, email, passwordHash }) { /* INSERT parametrizado */ }
}

// services/checkoutService.js — só regra
class CheckoutService {
  constructor({ userModel, enrollmentModel, paymentModel, gateway }) { Object.assign(this, arguments[0]); }
  async execute({ name, email, password, courseId, card }) { /* orquestra em transação */ }
}

// controllers/checkoutController.js — só fluxo HTTP
const checkout = (service) => async (req, res, next) => {
  try { res.status(201).json(await service.execute(req.body)); } catch (err) { next(err); }
};

// routes/index.js — só mapeamento
router.post('/api/checkout', checkout(service));
```

**Ordem da extração:** config → models por domínio → services → controllers → rotas. Mova um
domínio por vez e rode o smoke test entre cada passo; a God Class encolhe até sumir.

---

## T-04 — Substituir hash caseiro por KDF

**Antes**
```js
function badCrypto(pwd) {
  let h = pwd;
  for (let i = 0; i < 10000; i++) h = Buffer.from(h).toString('base64');
  return h.substring(0, 10);            // reversível e colidível
}
```
```python
self.password = hashlib.md5(password.encode()).hexdigest()   # sem salt
def check_password(self, password):
    return self.password == hashlib.md5(password.encode()).hexdigest()
```

**Depois**
```js
const bcrypt = require('bcryptjs');
const hash = await bcrypt.hash(password, 10);
const ok = await bcrypt.compare(password, user.password_hash);
```
```python
from werkzeug.security import generate_password_hash, check_password_hash

self.password_hash = generate_password_hash(password)       # salt + scrypt
def check_password(self, password):
    return check_password_hash(self.password_hash, password)
```

Sem dependência nova, `hashlib.scrypt`/`pbkdf2_hmac` com salt aleatório por usuário resolve.
**Migração:** hashes antigos não são recuperáveis; re-hasheie no próximo login bem-sucedido ou
force redefinição. Se houver seed, gere o hash no seed.

---

## T-05 — Serializar por allowlist

**Antes**
```python
def to_dict(self):
    return self.__dict__            # leva 'password', 'secret', tudo
# ou
return jsonify({"id": u["id"], "nome": u["nome"], "senha": u["senha"]})
```

**Depois**
```python
PUBLIC_FIELDS = ("id", "nome", "email", "tipo", "criado_em")

def to_dict(self):
    return {campo: getattr(self, campo) for campo in PUBLIC_FIELDS}
```
O campo sensível só sai por um método explícito e de uso interno
(`to_dict_internal()`), nunca pelo caminho padrão da resposta.

**Log:** nunca registre PAN de cartão nem segredo.
```js
// antes
console.log('Cobrando cartão ' + card + ' key=' + config.paymentKey);
// depois
logger.info('charge attempt', { last4: card.slice(-4), courseId });
```

---

## T-06 — Remover ou proteger endpoint administrativo

**Antes**
```python
@app.route("/admin/query", methods=["POST"])
def admin_query():
    return jsonify(db.execute(request.json["sql"]).fetchall())   # SQL arbitrário, sem auth
```

**Depois** — a opção padrão é **remover**. O endpoint existe para depuração e não tem substituto
legítimo em produção.

Se houver necessidade real (ex.: relatório administrativo), mantenha a função e proteja:
```python
def require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if user is None:
            raise UnauthorizedError("autenticação necessária")
        if user["tipo"] != "admin":
            raise ForbiddenError("acesso restrito a administradores")
        return fn(*args, **kwargs)
    return wrapper


@bp.get("/relatorios/vendas")
@require_admin
def relatorio_vendas():
    return jsonify(relatorio_service.vendas())
```
Remoção de endpoint é mudança de contrato: liste em `Intentional Behavior Changes`.

---

## T-07 — Extrair regra de negócio para service

**Antes** — controller calcula total, aplica desconto e decide o status.
```python
@app.route("/pedidos", methods=["POST"])
def criar_pedido():
    body = request.get_json(force=True)
    total = 0
    for it in body["itens"]:
        prod = models.buscar_produto(it["produto_id"])
        if not prod:
            return jsonify({"erro": "produto inexistente"}), 400
        total += prod["preco"] * it["quantidade"]
    if total > 500:
        total = total * 0.9
    pid = models.inserir_pedido(body["usuario_id"], total, body["itens"])
    return jsonify({"pedido_id": pid, "total": total}), 201
```

**Depois** — `services/pedido_service.py`
```python
class PedidoService:
    def __init__(self, produto_model, pedido_model, config):
        self.produtos = produto_model
        self.pedidos = pedido_model
        self.config = config

    def criar(self, usuario_id, itens):
        if not itens:
            raise ValidationError("pedido sem itens")
        total = self._calcular_total(itens)
        total = self._aplicar_desconto(total)
        pedido_id = self.pedidos.inserir(usuario_id, total, itens)
        return {"pedido_id": pedido_id, "total": total}

    def _calcular_total(self, itens):
        total = 0.0
        for item in itens:
            produto = self.produtos.buscar(item["produto_id"])
            if produto is None:
                raise ValidationError("produto inexistente")
            total += produto["preco"] * item["quantidade"]
        return total

    def _aplicar_desconto(self, total):
        if total > self.config.DESCONTO_MINIMO:
            return total * (1 - self.config.DESCONTO_PERCENTUAL)
        return total
```
`controllers/pedido_controller.py`
```python
def criar_pedido():
    body = request.get_json(silent=True) or {}
    resultado = pedido_service.criar(body.get("usuario_id"), body.get("itens", []))
    return jsonify(resultado), 201
```
O controller ficou com três linhas: entrada, chamada, resposta. O erro vira exceção de domínio,
traduzida em 400 pelo handler central (T-13).

**Teste de que funcionou:** dá para testar a regra sem `request` e sem servidor.

---

## T-08 — Injetar dependência

**Antes**
```js
class AppManager {
  constructor() {
    this.db = new sqlite3.Database(':memory:');   // cria a própria dependência
  }
}
```
```python
import models          # acoplamento a um módulo concreto

def listar():
    return models.buscar_tudo()
```

**Depois**
```js
class CheckoutService {
  constructor({ userModel, paymentGateway }) {   // recebe pronto
    this.userModel = userModel;
    this.paymentGateway = paymentGateway;
  }
}
// server.js — composition root, o único lugar que sabe montar
const db = await createDb(config.dbFile);
const service = new CheckoutService({
  userModel: new UserModel(db),
  paymentGateway: new CardGateway(config.paymentApiKey),
});
```
```python
class ProdutoController:
    def __init__(self, produto_service):
        self.service = produto_service
# app.py (composition root)
produto_controller = ProdutoController(ProdutoService(ProdutoModel(db)))
```

Em teste, injeta-se um dublê:
```js
const service = new CheckoutService({ userModel: fakeUsers, paymentGateway: alwaysApproves });
```

---

## T-09 — Eliminar estado global mutável

**Antes**
```js
let globalCache = {};            // cresce sem limite, compartilhado entre requisições
let totalRevenue = 0;            // exportado por valor: mutação não propaga
module.exports = { globalCache, totalRevenue };
```
```python
db_connection = None             # conexão única entre threads

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(DB, check_same_thread=False)
    return db_connection
```

**Depois**
```js
// estado derivado é calculado, não acumulado
async function totalRevenue(paymentModel) {
  const { total } = await paymentModel.sumPaid();
  return total ?? 0;
}
// cache, se necessário, é explícito, com limite e TTL
const cache = new LRUCache({ max: 500, ttl: 60_000 });
```
```python
# conexão com ciclo de vida por requisição
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DB_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()
```

**Regra:** valor que pode ser derivado do banco não vira variável de módulo. Estado
compartilhado de verdade vai para banco ou cache externo.

---

## T-10 — Envolver a unidade de trabalho em transação

**Antes**
```python
def criar_pedido(usuario_id, total, itens):
    cur = conn.execute("INSERT INTO pedidos ...")
    pid = cur.lastrowid
    for item in itens:
        if estoque_insuficiente(item):
            return None                       # sai sem rollback: pedido órfão no banco
        conn.execute("INSERT INTO itens_pedido ...")
        conn.execute("UPDATE produtos SET estoque = estoque - ? ...")
    conn.commit()
```

**Depois**
```python
def criar_pedido(self, usuario_id, total, itens):
    conn = self.db
    try:
        conn.execute("BEGIN")
        cur = conn.execute("INSERT INTO pedidos (usuario_id, total) VALUES (?, ?)",
                           (usuario_id, total))
        pedido_id = cur.lastrowid
        for item in itens:
            # decremento condicional: checagem e escrita no mesmo comando (evita corrida)
            afetadas = conn.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                (item["quantidade"], item["produto_id"], item["quantidade"]),
            ).rowcount
            if afetadas == 0:
                raise ValidationError("estoque insuficiente")
            conn.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario)"
                " VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], item["preco"]),
            )
        conn.commit()
        return pedido_id
    except Exception:
        conn.rollback()
        raise
```

Em Node com callbacks, promisifique antes (T-14) e use `BEGIN`/`COMMIT`/`ROLLBACK` no mesmo
`try/catch`. Em ORM, use `db.session.begin()` / `sequelize.transaction()`.

---

## T-11 — Eliminar N+1 com JOIN ou carga em lote

**Antes**
```python
pedidos = listar_pedidos(usuario_id)
for p in pedidos:
    p["usuario"] = buscar_usuario(p["usuario_id"])["nome"]   # 1 query por pedido
    p["itens"] = listar_itens(p["id"])                        # + 1 query por pedido
```

**Depois — JOIN único**
```python
SQL = """
SELECT pe.id, pe.total, pe.status, u.nome AS usuario,
       ip.produto_id, ip.quantidade, pr.nome AS produto
FROM pedidos pe
JOIN usuarios u ON u.id = pe.usuario_id
LEFT JOIN itens_pedido ip ON ip.pedido_id = pe.id
LEFT JOIN produtos pr ON pr.id = ip.produto_id
WHERE pe.usuario_id = ?
ORDER BY pe.id
"""
rows = conn.execute(SQL, (usuario_id,)).fetchall()
pedidos = {}
for row in rows:                                   # agrupa em memória, 1 ida ao banco
    pedido = pedidos.setdefault(row["id"], {"id": row["id"], "total": row["total"],
                                            "usuario": row["usuario"], "itens": []})
    if row["produto_id"] is not None:
        pedido["itens"].append({"produto_id": row["produto_id"],
                                "quantidade": row["quantidade"], "produto": row["produto"]})
return list(pedidos.values())
```

**Alternativa — carga em lote** quando o JOIN fica pesado:
```python
ids = [p["id"] for p in pedidos]
marcadores = ",".join("?" * len(ids))
itens = conn.execute(f"SELECT * FROM itens_pedido WHERE pedido_id IN ({marcadores})", ids).fetchall()
por_pedido = defaultdict(list)
for item in itens:
    por_pedido[item["pedido_id"]].append(dict(item))
```

**Com ORM:**
```python
tasks = db.session.execute(
    select(Task).options(selectinload(Task.user), selectinload(Task.category))
).scalars().all()
```
```js
const rows = await db.all(`SELECT c.id, c.title, COUNT(e.id) AS students, SUM(p.amount) AS revenue
                           FROM courses c
                           LEFT JOIN enrollments e ON e.course_id = c.id
                           LEFT JOIN payments p ON p.enrollment_id = e.id AND p.status = 'PAID'
                           GROUP BY c.id`);
```

Agregação (`COUNT`, `SUM`) é trabalho do banco, não de laço em Python/JS.

---

## T-12 — Validar na borda

**Antes**
```python
uid = models.inserir_usuario(body["nome"], body["email"])   # KeyError → 500
if data["priority"] < 1:                                     # string → TypeError → 500
```

**Depois — função de validação dedicada**
```python
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")


def validar_usuario(data):
    erros = {}
    nome = (data.get("nome") or "").strip()
    email = (data.get("email") or "").strip()
    if not nome:
        erros["nome"] = "obrigatório"
    if not EMAIL_RE.match(email):
        erros["email"] = "formato inválido"
    if erros:
        raise ValidationError(erros)
    return {"nome": nome, "email": email}
```
```python
def criar_usuario():
    dados = validar_usuario(request.get_json(silent=True) or {})
    return jsonify(usuario_service.criar(**dados)), 201
```

**Com schema** (marshmallow/pydantic/zod/joi), quando a dependência já existe:
```python
class TaskSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    priority = fields.Int(load_default=3, validate=validate.Range(min=1, max=5))
    status = fields.Str(load_default="pending", validate=validate.OneOf(STATUSES))
```
```js
const schema = z.object({ email: z.string().email(), courseId: z.number().int().positive() });
const data = schema.parse(req.body);     // lança → errorHandler devolve 400
```

**Regras:** `request.get_json(silent=True) or {}` em vez de `force=True`; conversão de query
string dentro de `try` devolvendo 400; comparar com `is not None` para não descartar `0`;
validação de entrada devolve **400**, nunca 500.

---

## T-13 — Centralizar o tratamento de erros

**Antes** — o mesmo bloco em 16 rotas:
```python
try:
    ...
except Exception as e:
    return jsonify({"erro": str(e)}), 500      # vaza SQL e caminho ao cliente
```

**Depois** — exceções de domínio + handler único.
```python
# middlewares/errors.py
class AppError(Exception):
    status = 500
    def __init__(self, message, details=None):
        super().__init__(message)
        self.message, self.details = message, details

class ValidationError(AppError):   status = 400
class UnauthorizedError(AppError): status = 401
class ForbiddenError(AppError):    status = 403
class NotFoundError(AppError):     status = 404
class ConflictError(AppError):     status = 409


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"erro": err.message, "detalhes": err.details}), err.status

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        app.logger.exception("erro não tratado")      # detalhe vai para o log
        return jsonify({"erro": "erro interno"}), 500  # cliente recebe mensagem genérica
```
As camadas passam a lançar: `raise NotFoundError("produto não encontrado")`. Os `try/except` das
rotas desaparecem.

**Express** — handler com quatro argumentos, registrado por último:
```js
// middlewares/errorHandler.js
module.exports = (err, req, res, _next) => {
  const status = err.status || 500;
  if (status >= 500) logger.error(err);
  res.status(status).json({ error: status >= 500 ? 'internal error' : err.message });
};
// app.js
app.use(routes);
app.use(errorHandler);            // sempre depois das rotas
```
Controllers assíncronos usam `next(err)` (ou um wrapper `asyncHandler`), nunca `try/catch`
duplicado com `res.status(500).send(String(err))`.

**Nunca** use `except:` nu nem `except Exception: pass`: o erro some sem log.

---

## T-14 — Substituir API deprecated

| Antes | Depois |
|---|---|
| `datetime.utcnow()` | `datetime.now(timezone.utc)` |
| `hashlib.md5(pwd)` | `generate_password_hash(pwd)` (ver T-04) |
| `Model.query.get(id)` | `db.session.get(Model, id)` |
| `Model.query.filter_by(...)` | `db.session.execute(select(Model).where(...)).scalars()` |
| `@app.before_first_request` | app factory + `with app.app_context():` |
| `new Buffer(x)` | `Buffer.from(x)` |
| `url.parse(u)` | `new URL(u)` |
| `bodyParser.json()` | `express.json()` |
| `res.send(404)` | `res.sendStatus(404)` |
| `str.substr(a, b)` | `str.slice(a, b)` |

**Datas com fuso** — a troca de `utcnow()` muda o comparador:
```python
# antes: naive, comparação errada contra datetime aware
if task.due_date < datetime.utcnow():
# depois
from datetime import datetime, timezone
def now_utc():
    return datetime.now(timezone.utc)

def _aware(value):                      # datas antigas gravadas naive
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

if _aware(task.due_date) < now_utc():
```

**Callback → async/await** (API de callbacks é o "deprecated" mais caro de manter):
```js
// antes: pirâmide de 5 níveis, erro tratado em cada nível
db.get('SELECT ...', [id], function (err, user) {
  if (err) return res.status(500).send('erro');
  db.run('INSERT ...', [user.id], function (err2) {
    if (err2) return res.status(500).send('erro');
    /* ... mais 3 níveis ... */
  });
});

// depois: promisificar uma vez
const { promisify } = require('util');
function promisifyDb(db) {
  return {
    get: promisify(db.get.bind(db)),
    all: promisify(db.all.bind(db)),
    run: (sql, params = []) =>
      new Promise((resolve, reject) =>
        db.run(sql, params, function (err) {           // `function` para ter `this.lastID`
          err ? reject(err) : resolve({ lastID: this.lastID, changes: this.changes });
        })),
  };
}
// uso: linear, com um único ponto de erro
const user = await db.get('SELECT * FROM users WHERE email = ?', [email]);
const { lastID } = await db.run('INSERT INTO enrollments (user_id) VALUES (?)', [user.id]);
```
Com `async/await`, `const self = this` também desaparece.

**Concorrência:** substitua contador manual por `Promise.all`.
```js
// antes: pending--; if (pending === 0) res.json(out);   → trava ou responde duas vezes
// depois
const results = await Promise.all(courses.map((c) => buildCourseReport(c)));
res.json(results);
```

---

## T-15 — Extrair magic numbers para constantes

**Antes**
```python
if total > 10000:   desconto = 0.10
elif total > 5000:  desconto = 0.05
if data["priority"] < 1 or data["priority"] > 5: ...
if status not in ["pending", "in_progress", "done", "cancelled"]: ...
```

**Depois** — fonte única, em config ou no módulo do domínio.
```python
# config.py
FAIXAS_DESCONTO = ((10_000, 0.10), (5_000, 0.05), (1_000, 0.02))
PRIORIDADE_MIN, PRIORIDADE_MAX = 1, 5


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"
```
```python
def desconto_para(total):
    for minimo, percentual in FAIXAS_DESCONTO:
        if total > minimo:
            return percentual
    return 0.0
```
```js
const PaymentStatus = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });
```

**Sinal de que funcionou:** a mesma lista de status não aparece em dois arquivos.

---

## Ordem recomendada de aplicação

1. **T-01, T-02, T-04, T-05, T-06** — segurança primeiro; são pequenas e de alto impacto.
2. **T-03** — quebrar a God Class, um domínio por vez.
3. **T-07, T-08, T-09** — mover regra para services e inverter as dependências.
4. **T-13** — centralizar erros (permite remover os `try/except` das rotas).
5. **T-10, T-11, T-12** — transação, N+1 e validação.
6. **T-14, T-15** — APIs deprecated e constantes.

Rode o smoke test dos endpoints **entre os grupos**, não só no fim. Quando algo quebrar, o
conjunto de mudanças suspeito é pequeno.
