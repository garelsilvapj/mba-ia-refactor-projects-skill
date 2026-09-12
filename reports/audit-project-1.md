# Relatório de auditoria — Projeto 1 (`code-smells-project`)

Saída das Fases 1 e 2 da skill `/refactor-arch`.

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1, sqlite3 (stdlib)
Domain:        E-commerce API (produtos, usuários, pedidos, itens de pedido, relatório de vendas)
Architecture:  Monolítica — 4 arquivos sem camadas: models.py mistura SQL de 4 domínios com
               regra de negócio, controllers.py mistura HTTP com acesso direto ao banco e
               app.py declara rotas e ainda implementa 3 handlers inline
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
Endpoints:     19 routes
Entry point:   python app.py (porta 5000, debug=True, host 0.0.0.0)
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 7 | HIGH: 5 | MEDIUM: 6 | LOW: 4

## Findings

### [CRITICAL] Endpoint de execução de SQL arbitrário
File: app.py:59-78
Description: `POST /admin/query` recebe o campo `sql` do corpo da requisição e o executa
diretamente (`cursor.execute(query)` na linha 69), sem autenticação, sem allowlist e com
commit automático para comandos que não são SELECT (linha 75).
Impact: qualquer chamador anônimo lê, altera ou destrói qualquer tabela do banco. É uma porta
dos fundos completa, sem autenticação nem registro de auditoria.
Recommendation: remover o endpoint. Necessidades legítimas de consulta devem virar endpoints
específicos com query parametrizada e autorização de administrador.

### [CRITICAL] Endpoint destrutivo sem autenticação
File: app.py:47-57
Description: `POST /admin/reset-db` executa `DELETE` nas quatro tabelas e faz commit, sem
autenticação, confirmação ou trilha de auditoria. Confirmado na execução: devolve 200 e
esvazia a base.
Impact: perda total dos dados de produção por uma única requisição anônima.
Recommendation: remover o endpoint. Reset de base é tarefa de administração operacional, não
de rota HTTP pública.

### [CRITICAL] SQL Injection em toda a camada de dados
File: models.py:28
Description: todas as queries são montadas por concatenação de string com a entrada do
usuário. O caso mais grave é o login em `models.py:110`
(`"... WHERE email = '" + email + "' AND senha = '" + senha + "'"`), que permite autenticar-se
como administrador sem senha. Confirmado na execução: `POST /login` com
`email = admin@loja.com' OR '1'='1` devolve 200 e os dados do usuário Admin. Também em
models.py:48-49, 58-60, 68, 92, 127-128, 140, 149-150, 155, 158-160, 164-165, 174, 188, 192,
220, 224, 280 e 291-297 (busca com LIKE).
Impact: bypass de autenticação, leitura de qualquer tabela, alteração e destruição de dados.
Confirmado também que payload malformado devolve 500 com a mensagem do parser SQL ao cliente.
Recommendation: substituir toda concatenação por queries parametrizadas com placeholders `?` e
tupla de parâmetros; no filtro dinâmico da busca, montar apenas a cláusula com placeholders e
passar os valores como parâmetros.

### [CRITICAL] Credenciais hardcoded no código-fonte
File: app.py:7
Description: `SECRET_KEY` fixa no código com o valor `'minha-chave-super-secreta-123'`. Somam-se
as senhas do seed em texto puro em database.py:76-78 (`admin123`, `123456`, `senha123`) e o
caminho do banco fixo em database.py:5.
Impact: o segredo está no histórico do git; é o mesmo em todos os ambientes; sessões e tokens
assinados com ele são forjáveis por qualquer pessoa com acesso ao repositório.
Recommendation: mover para variável de ambiente lida por um módulo de config, com
`.env.example` documentando cada chave, e rotacionar o segredo exposto.

### [CRITICAL] Senhas armazenadas e devolvidas em texto puro
File: models.py:127-128
Description: a senha é gravada exatamente como chegou (`INSERT INTO usuarios ... '" + senha + "'`)
e devolvida nas respostas: `models.py:83` e `models.py:99` incluem o campo `senha` no dicionário
serializado por `GET /usuarios` e `GET /usuarios/<id>`. Confirmado na execução: `GET /usuarios`
devolve `"senha":"admin123"` para o usuário Admin.
Impact: qualquer chamador anônimo coleta as senhas reais de todos os usuários; o vazamento se
propaga para outros serviços por reuso de senha.
Recommendation: hash com `werkzeug.security.generate_password_hash` na escrita, verificação com
`check_password_hash` no login e serialização por allowlist de campos, sem `senha`.

### [CRITICAL] Endpoint de health expõe a chave secreta da aplicação
File: controllers.py:285-289
Description: `GET /health` devolve `secret_key`, `db_path`, `debug` e `ambiente` no corpo da
resposta, sem autenticação. Confirmado na execução: o valor da `SECRET_KEY` aparece na resposta.
Impact: entrega a chave de assinatura da aplicação a qualquer chamador, tornando inútil qualquer
proteção baseada nela.
Recommendation: o health check deve devolver apenas o estado do serviço e das dependências;
nunca configuração nem segredo.

### [CRITICAL] God Module concentra dados e regra de negócio de 4 domínios
File: models.py:1-314
Description: um único arquivo contém as queries de produtos, usuários, pedidos e itens, a
montagem de pedido com baixa de estoque (linhas 133-169), o cálculo do relatório de vendas com
faixas de desconto (linhas 256-262) e a formatação de saída (mapeamento linha → dicionário,
repetido em 5 pontos).
Impact: impossível testar qualquer regra isoladamente; toda mudança em um domínio arrisca os
outros três; o arquivo é ponto único de conflito.
Recommendation: separar em models por domínio (produto, usuário, pedido) com acesso a dados, e
mover o cálculo de pedido e de relatório para services.

### [HIGH] Regra de negócio dentro dos controllers
File: controllers.py:43-54
Description: o controller de criação de produto valida faixa de preço, tamanho de nome e a lista
de categorias válidas (linha 52); o mesmo bloco reaparece em controllers.py:87-90. Em
controllers.py:242 está a lista de status válidos do pedido e em controllers.py:247-250 os
efeitos colaterais de aprovação e cancelamento.
Impact: regra de domínio inacessível fora do HTTP, não testável sem subir a aplicação e
duplicada entre criação e atualização.
Recommendation: mover as regras para um service de produto e de pedido; o controller fica com
leitura da requisição, chamada e formatação da resposta.

### [HIGH] Cálculo de faturamento e desconto dentro da camada de dados
File: models.py:256-262
Description: `relatorio_vendas()` executa cinco contagens separadas e aplica as faixas de
desconto (10%, 5%, 2%) e o ticket médio (linha 272) dentro da função de acesso a dados.
Impact: regra de negócio presa ao SQL; mudar a política de desconto exige mexer na camada de
persistência; nenhuma das faixas é testável isoladamente.
Recommendation: o model devolve os números agregados; o service aplica as faixas, que ficam
como constantes nomeadas em config.

### [HIGH] Acoplamento direto sem injeção de dependência
File: controllers.py:2-3
Description: os controllers importam o módulo concreto `models` e ainda `get_db` diretamente;
`models.py:1` importa `get_db` de `database`; nada recebe suas dependências. Em
controllers.py:264-274 o controller de health abre cursor e executa SQL, passando por cima da
camada de dados — mesma violação em app.py:49-55 e app.py:66-76.
Impact: impossível substituir a camada de dados em teste; qualquer teste precisa de um SQLite
real; trocar o banco exigiria reescrever controllers.
Recommendation: models e services recebem a conexão/dependência por parâmetro, montados em um
composition root no entry point.

### [HIGH] Conexão global mutável compartilhada entre threads
File: database.py:4-11
Description: `db_connection` é uma variável de módulo reaproveitada por todas as requisições,
aberta com `check_same_thread=False` e nunca fechada; `get_db()` ainda mistura conexão, DDL das
4 tabelas e seed na mesma função.
Impact: o servidor de desenvolvimento do Flask é multithread; requisições concorrentes
compartilham cursor e transação, o que produz `database is locked` e leituras inconsistentes.
Além disso, o seed só roda na primeira conexão do processo, então após `/admin/reset-db` a base
fica vazia até reiniciar.
Recommendation: conexão com ciclo de vida por requisição (`g` + `teardown_appcontext`), e
separar conexão, criação de schema e seed em funções distintas.

### [HIGH] Criação de pedido sem transação e com corrida de estoque
File: models.py:133-169
Description: a função valida o estoque em um laço (linhas 139-146), depois insere o pedido
(148-151), os itens e o decremento de estoque em outro laço (154-166), com um único `commit` na
linha 168. Os `return` das linhas 143 e 145 saem sem `rollback`.
Impact: falha no meio da segunda iteração deixa pedido gravado com itens parciais e estoque
inconsistente. Entre a checagem e o decremento há janela de corrida que permite estoque negativo.
Recommendation: envolver a operação em transação explícita com rollback no erro e fazer o
decremento condicional (`UPDATE ... WHERE id = ? AND estoque >= ?`, verificando `rowcount`).

### [MEDIUM] Query N+1 na listagem de pedidos
File: models.py:187-199
Description: para cada pedido é executada uma query de itens (linha 188) e, para cada item, uma
query do nome do produto (linha 192). O mesmo padrão se repete em `get_todos_pedidos()`
(models.py:219-231). O relatório de vendas faz cinco contagens separadas (models.py:239-254) que
caberiam em uma única agregação.
Impact: `GET /pedidos` custa 1 + N + N×M idas ao banco; a latência cresce linearmente com o
número de pedidos e itens.
Recommendation: um único SELECT com JOIN entre pedidos, itens e produtos, agrupando o resultado
em memória; agregação do relatório com `COUNT`/`SUM` e `GROUP BY`.

### [MEDIUM] Validação de entrada ausente ou frágil
File: controllers.py:37-46
Description: `preco` e `estoque` são comparados com `<` sem verificação de tipo, então um corpo
com `"preco": "abc"` levanta `TypeError` e devolve 500 em vez de 400. Em controllers.py:146-162
não há validação de formato de e-mail, força de senha nem e-mail duplicado (a coluna também não
tem UNIQUE, database.py:29). Em controllers.py:239-240 o corpo pode ser `None`. Em
controllers.py:118-121 a conversão `float()` não é protegida. `atualizar_produto` não valida
categoria, embora `criar_produto` valide.
Impact: dados inconsistentes gravados no banco e erro de cliente reportado como falha do
servidor.
Recommendation: validar na borda com função ou schema dedicado por recurso, devolvendo 400 com
a lista de campos inválidos.

### [MEDIUM] Tratamento de erro duplicado que vaza detalhe interno
File: controllers.py:10-12
Description: o bloco `except Exception as e: return jsonify({"erro": str(e)}), 500` aparece 16
vezes em controllers.py (linhas 10, 21, 60, 95, 108, 125, 133, 143, 164, 185, 218, 226, 234,
254, 261, 291) e mais uma vez em app.py:77-78. A mensagem crua da exceção vai para o cliente.
Impact: o cliente recebe texto de erro do SQLite com trecho da query e estrutura do schema;
nenhum erro é registrado em log estruturado; qualquer correção precisa ser replicada 17 vezes.
Recommendation: hierarquia de exceções de domínio e handler global (`@app.errorhandler`) que
loga o detalhe e devolve mensagem genérica com o status correto.

### [MEDIUM] Duplicação de código em queries e serialização
File: models.py:171-201
Description: `get_pedidos_usuario` (171-201) e `get_todos_pedidos` (203-233) são praticamente
idênticas, diferindo apenas pela cláusula `WHERE`. O mapeamento de linha de produto para
dicionário está copiado em models.py:12-21, 31-40 e 304-313; o de usuário em models.py:79-86 e
95-102. O bloco de validação de produto está duplicado em controllers.py:28-50 e 72-90.
Impact: uma correção precisa ser feita em vários lugares e as cópias divergem com o tempo.
Recommendation: extrair uma função de listagem parametrizada pelo filtro e funções de
serialização únicas por entidade.

### [MEDIUM] CORS liberado para qualquer origem
File: app.py:9
Description: `CORS(app)` sem restrição aplica `Access-Control-Allow-Origin: *` a todas as rotas,
incluindo `/usuarios` (que devolve senhas) e `/admin/*`.
Impact: qualquer site pode ler as respostas da API a partir do navegador da vítima.
Recommendation: restringir a origens conhecidas por configuração de ambiente e aplicar apenas
às rotas que precisam.

### [MEDIUM] Filtros ignoram valores válidos por checagem de veracidade
File: models.py:294
Description: `if preco_min:` e `if preco_max:` (models.py:294 e 296) descartam o valor `0`, que é
um filtro legítimo; o mesmo em controllers.py:118-121 e em controllers.py:198
(`if not usuario_id:` rejeita o id `0`).
Impact: filtro silenciosamente ignorado; o cliente recebe resultado diferente do pedido, sem
erro.
Recommendation: comparar com `is not None` em vez de usar a veracidade do valor.

### [LOW] Magic numbers e listas de valores válidos espalhados
File: models.py:257-262
Description: as faixas de desconto (`10000`, `5000`, `1000`, `0.1`, `0.05`, `0.02`) estão soltas
no cálculo do relatório; a lista de categorias válidas está inline em controllers.py:52; a lista
de status de pedido em controllers.py:242; os limites de tamanho de nome (`2`, `200`) em
controllers.py:47-50.
Impact: a intenção fica ilegível e a mesma regra precisa ser caçada em vários arquivos quando
muda.
Recommendation: constantes nomeadas em um módulo de config, com fonte única para cada lista.

### [LOW] `print` usado como log, inclusive com dado pessoal
File: controllers.py:161
Description: há 14 chamadas de `print` em controllers.py (incluindo as linhas 161, 179 e 182,
que registram o e-mail do usuário) e 5 em app.py. As linhas 208-210 simulam envio de e-mail, SMS
e push com `print` dentro do controller.
Impact: sem nível, sem destino configurável e sem formato; dado pessoal escrito em stdout;
notificação acoplada ao handler HTTP.
Recommendation: usar o `logging` configurado pela aplicação e extrair a notificação para um
serviço próprio.

### [LOW] Sombreamento de builtin e nomes pouco descritivos
File: controllers.py:14
Description: o parâmetro `id` sombreia o builtin em controllers.py:14, 56, 64, 98 e 160 e em
models.py:24, 54, 65 e 89. Os cursores auxiliares chamam-se `cursor2` e `cursor3`
(models.py:187-193).
Impact: leitura ambígua e risco de erro sutil quando o builtin for necessário no mesmo escopo.
Recommendation: renomear para `produto_id`, `usuario_id` e nomes que digam o papel do cursor.

### [LOW] Imports mortos e envelope de resposta inconsistente
File: models.py:2
Description: `import sqlite3` em models.py:2 e `import os` em database.py:2 nunca são usados. As
respostas alternam entre `{"dados": ..., "sucesso": true}`, objetos com `"mensagem"` e, em
`/health` (controllers.py:276-290), um formato completamente diferente. Alguns erros trazem
`"sucesso": false`, outros não.
Impact: código morto confunde quem chega depois; o cliente precisa de tratamento especial por
rota.
Recommendation: remover os imports não usados e padronizar o envelope de resposta e de erro.

### [INFO] Varredura de APIs deprecated
File: (nenhuma ocorrência)
Description: a varredura do catálogo (AP-15) não encontrou nenhuma API deprecated neste projeto:
não há `datetime.utcnow()`, `@app.before_first_request`, `hashlib.md5`, `Query.get()` legado nem
`flask.Markup`. Registrado para documentar que a verificação foi executada.
Impact: nenhum.
Recommendation: nenhuma ação. Observação de estilo: o registro de rotas por `add_url_rule` com
funções soltas (app.py:11-30) é o padrão pré-Blueprint, desencorajado pela documentação atual do
Flask, e será substituído por Blueprints na Fase 3.

================================
Total: 22 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Confirmação

Resposta do usuário: **y** — a Fase 3 foi autorizada e executada. O resultado está em
`reports/logs/project-1-after.txt` e no README, seção Resultados.
