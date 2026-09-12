#!/usr/bin/env bash
# Smoke test do projeto 1 (code-smells-project).
# Exercita todos os endpoints originais e imprime status + corpo normalizado.
# Uso: reports/smoke/project-1.sh <base-url>
set -u
BASE="${1:-http://127.0.0.1:5001}"

req() {
  local method="$1" path="$2" data="${3:-}"
  echo "--- $method $path"
  if [ -n "$data" ]; then
    curl -s -o /tmp/body.$$ -w '%{http_code}' -X "$method" "$BASE$path" \
      -H 'Content-Type: application/json' -d "$data"
  else
    curl -s -o /tmp/body.$$ -w '%{http_code}' -X "$method" "$BASE$path"
  fi
  echo ""
  # normaliza timestamps para o diff antes/depois ser estável
  sed -E 's/"criado_em":"[^"]*"/"criado_em":"<TS>"/g' /tmp/body.$$ | head -c 1200
  echo ""
  rm -f /tmp/body.$$
}

req GET  /
req GET  /health
req GET  /produtos
req GET  "/produtos/busca?q=Mouse"
req GET  "/produtos/busca?q=&categoria=moveis&preco_min=100&preco_max=2000"
req GET  "/produtos/busca?q=%27%20OR%201%3D1%20--"
req GET  /produtos/1
req GET  /produtos/9999
req POST /produtos '{"nome":"Produto Teste","descricao":"desc","preco":10.5,"estoque":3,"categoria":"geral"}'
req POST /produtos '{"nome":"X","preco":10,"estoque":1}'
req POST /produtos '{"nome":"Sem preco","estoque":1}'
req POST /produtos '{"nome":"Tipo invalido","preco":"abc","estoque":1}'
req PUT  /produtos/11 '{"nome":"Produto Teste Editado","descricao":"nova","preco":12.0,"estoque":4,"categoria":"geral"}'
req PUT  /produtos/9999 '{"nome":"X","preco":1,"estoque":1}'
req DELETE /produtos/11
req DELETE /produtos/9999
req GET  /usuarios
req GET  /usuarios/1
req GET  /usuarios/9999
req POST /usuarios '{"nome":"Carlos","email":"carlos@email.com","senha":"segredo123"}'
req POST /usuarios '{"nome":"Sem email"}'
req POST /login '{"email":"admin@loja.com","senha":"admin123"}'
req POST /login '{"email":"admin@loja.com","senha":"errada"}'
req POST /login "{\"email\":\"admin@loja.com' OR '1'='1\",\"senha\":\"qualquer\"}"
req POST /pedidos '{"usuario_id":2,"itens":[{"produto_id":2,"quantidade":2},{"produto_id":3,"quantidade":1}]}'
req POST /pedidos '{"usuario_id":2,"itens":[{"produto_id":9999,"quantidade":1}]}'
req POST /pedidos '{"usuario_id":2,"itens":[{"produto_id":1,"quantidade":99999}]}'
req POST /pedidos '{"usuario_id":2,"itens":[]}'
req GET  /pedidos
req GET  /pedidos/usuario/2
req PUT  /pedidos/1/status '{"status":"aprovado"}'
req PUT  /pedidos/1/status '{"status":"invalido"}'
req GET  /relatorios/vendas
req POST /admin/query '{"sql":"SELECT COUNT(*) AS n FROM produtos"}'
req POST /admin/reset-db ''
