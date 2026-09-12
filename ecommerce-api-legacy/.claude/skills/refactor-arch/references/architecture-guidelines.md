# Guidelines de arquitetura — o MVC alvo (Fase 3)

Define **para onde** o projeto vai. O playbook define **como** chegar lá.

## As camadas e suas responsabilidades

| Camada | Responsabilidade única | Pode fazer | Nunca faz |
|---|---|---|---|
| **Config** | Fornecer configuração vinda do ambiente | Ler `env`, expor constantes de domínio, definir perfis (dev/test/prod) | Conter segredo literal, importar model/controller |
| **Model** | Representar e persistir dados de **um** domínio | Definir a entidade, executar queries parametrizadas do próprio domínio, mapear linha → objeto | Conhecer HTTP (`request`, `response`, status code), decidir regra de negócio de outro domínio |
| **Service** | Regra de negócio e orquestração | Calcular, decidir, validar invariantes, coordenar vários models em transação | Conhecer HTTP, montar JSON de resposta, ler `request` |
| **Controller** | Fluxo de uma requisição | Ler e validar entrada, chamar service, escolher status code, formatar resposta | Conter cálculo de negócio, montar SQL, acessar o banco direto |
| **View / Route** | Mapear URL → controller | Declarar método, caminho, middlewares da rota | Conter lógica; em API a "View" é a serialização da resposta |
| **Middleware** | Preocupações transversais | Error handler, auth, CORS, log, parse de corpo | Regra de negócio de um domínio específico |
| **Entry point** | Composition root | Criar app, ler config, instanciar e ligar as camadas, registrar rotas e handlers | Conter rota, regra ou query |

**Service é opcional em domínio trivial.** Quando o controller só faz CRUD direto, ele pode
chamar o model. Assim que aparece cálculo, decisão ou coordenação de dois models, o service
passa a ser obrigatório.

## Regra de dependência

```
route → controller → service → model → banco
                  ↘ config ↙
```

- As setas apontam em um sentido só. Model nunca importa controller; service nunca importa route.
- Config é folha: qualquer camada lê, config não importa ninguém.
- Middleware é registrado pelo entry point, não importado pelas rotas.
- Se precisar de uma dependência "para trás", o desenho está errado: inverta passando a
  dependência como parâmetro.

**Teste rápido de violação:**
```bash
grep -rn "import\|require" models/ | grep -iE "controller|route|request|flask import request|express"
grep -rn "import\|require" services/ | grep -iE "controller|route|req|res"
```
Qualquer acerto é uma violação a corrigir.

## Estruturas alvo por stack

### Python / Flask

```
src/  (ou raiz do projeto)
├── config.py                 # Config a partir de env + constantes de domínio
├── app.py                    # create_app(): app factory + composition root
├── models/
│   ├── db.py                 # conexão/sessão, init_db, ciclo de vida por requisição
│   ├── produto_model.py      # entidade + queries parametrizadas de produto
│   └── pedido_model.py
├── services/
│   └── pedido_service.py     # cálculo de total, desconto, regra de estoque
├── controllers/
│   └── pedido_controller.py  # funções que recebem request e devolvem response
├── views/  (ou routes/)
│   └── routes.py             # Blueprints: URL → controller
├── middlewares/
│   └── error_handler.py      # @app.errorhandler centralizado
└── .env.example
```

Pontos obrigatórios:

- **App factory** `create_app(config)` em vez de `app = Flask(__name__)` no topo do módulo: sem
  efeito colateral em import, com instância isolada por teste.
- **Blueprints** com `url_prefix`, em vez de `@app.route` espalhado ou `add_url_rule` manual.
- Nada de `db.create_all()` em tempo de import.
- Entry point separado (`wsgi.py` ou bloco `if __name__ == "__main__"` mínimo).

### Node.js / Express

```
src/
├── config/index.js           # process.env + defaults, sem segredo literal
├── server.js                 # entry point: cria app, liga tudo, escuta a porta
├── app.js                    # createApp(deps): middlewares + rotas, sem listen
├── models/
│   ├── db.js                 # conexão + helpers promisificados
│   ├── userModel.js
│   └── paymentModel.js
├── services/
│   ├── checkoutService.js    # regra de checkout, transacional
│   └── paymentGateway.js     # abstração do gateway (injetável/mockável)
├── controllers/
│   └── checkoutController.js
├── routes/
│   └── index.js              # router: URL → controller
├── middlewares/
│   ├── errorHandler.js       # (err, req, res, next) — 4 argumentos
│   └── validate.js
└── .env.example
```

Pontos obrigatórios:

- `app.js` exporta a app sem `listen`; `server.js` faz o `listen`. Isso torna a app testável.
- Error handler registrado **por último**, com quatro argumentos; controllers usam `next(err)`.
- Acesso a dados com `async/await` (promisificar driver de callback), nunca pirâmide de callbacks.

### Outras stacks

Mesmo mapa de responsabilidades, com os nomes idiomáticos do framework:

| Stack | Model | Controller | View/Route | Config |
|---|---|---|---|---|
| Laravel | `app/Models` | `app/Http/Controllers` | `routes/api.php` | `config/` + `.env` |
| Rails | `app/models` | `app/controllers` | `config/routes.rb` | `config/` |
| NestJS | `*.entity.ts` + repository | `*.controller.ts` | decorators de rota | `ConfigModule` |
| Spring | `@Entity` + `@Repository` | `@RestController` | anotações de mapping | `application.yml` |
| Django | `models.py` | `views.py` | `urls.py` | `settings.py` |
| Go/Gin | `internal/model` | `internal/handler` | `router.go` | `internal/config` |

**Não force pastas onde o framework já resolve.** Em projeto já organizado, adapte: o objetivo é a
separação de responsabilidades, não uma árvore de diretórios específica.

## Adaptação ao ponto de partida

| Estado inicial | O que a Fase 3 faz |
|---|---|
| Monólito de poucos arquivos | Criar a árvore inteira; quebrar o God Module por domínio; extrair config e error handler |
| God Class única | Extrair, na ordem: config → models por domínio → services → controllers → rotas; a classe desaparece |
| Camadas parciais (pastas existem, regra nas rotas) | **Não recriar o que já existe.** Introduzir controllers e services, esvaziar as rotas, adicionar config/app factory/error handler, corrigir os problemas de código |
| Já em MVC | Somente correções pontuais dos findings; não mover arquivo sem motivo |

Em projeto parcialmente organizado, mover arquivo sem necessidade só gera diff e risco. Prefira:
primeiro corrigir segurança e corretude, depois introduzir a camada que falta.

## Critérios de pronto (checklist da Fase 3)

- [ ] **Config**: nenhum segredo literal no código; tudo por `env` com `.env.example`.
- [ ] **Models**: um por domínio; sem HTTP; queries parametrizadas.
- [ ] **Views/Routes**: só mapeiam URL → controller.
- [ ] **Controllers**: finos; sem cálculo de negócio; sem SQL.
- [ ] **Services**: concentram a regra; testáveis sem subir servidor.
- [ ] **Error handling**: centralizado; sem `try/except` copiado por rota; sem erro cru no corpo.
- [ ] **Entry point**: claro e mínimo; sem efeito colateral em import.
- [ ] **Dependências**: injetadas, não instanciadas dentro da regra.
- [ ] **Boot**: a aplicação inicia sem erro.
- [ ] **Endpoints**: todos os originais respondem como antes (salvo mudanças intencionais
      listadas).
