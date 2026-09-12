#!/usr/bin/env bash
# Smoke test do projeto 2 (ecommerce-api-legacy).
# Exercita os 3 endpoints originais, incluindo os casos do api.http.
# O header X-Admin-Token é ignorado pelo código original e exigido pelo refatorado.
set -u
BASE="${1:-http://127.0.0.1:3101}"
TOKEN="${ADMIN_TOKEN:-token-de-teste}"

req() {
  local method="$1" path="$2" data="${3:-}" auth="${4:-}"
  echo "--- $method $path ${auth:+(com token)}"
  local args=(-s -o /tmp/body2.$$ -w '%{http_code}' -X "$method" "$BASE$path")
  [ -n "$auth" ] && args+=(-H "X-Admin-Token: $TOKEN")
  if [ -n "$data" ]; then
    args+=(-H 'Content-Type: application/json' -d "$data")
  fi
  curl "${args[@]}"
  echo ""
  head -c 1200 /tmp/body2.$$
  echo ""
  rm -f /tmp/body2.$$
}

req GET  /api/admin/financial-report "" auth
req GET  /api/admin/financial-report
req POST /api/checkout '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'
req POST /api/checkout '{"usr":"João","eml":"joao@teste.com","pwd":"123","c_id":1,"card":"5111222233334444"}'
req POST /api/checkout '{"usr":"Leonan","eml":"leonan@fullcycle.com.br","pwd":"123","c_id":2,"card":"4111222233334444"}'
req POST /api/checkout '{"usr":"Sem cartao","eml":"x@y.com","pwd":"123","c_id":1}'
req POST /api/checkout '{"usr":"Curso inexistente","eml":"z@y.com","pwd":"123","c_id":999,"card":"4111222233334444"}'
req GET  /api/admin/financial-report "" auth
req DELETE /api/users/1 "" auth
req DELETE /api/users/999 "" auth
req GET  /api/admin/financial-report "" auth

# Último caso de propósito: checkout com e-mail existente e senha errada.
# No código original era aceito (200); no refatorado é rejeitado (401).
req POST /api/checkout '{"usr":"Impostor","eml":"gui@fullcycle.com.br","pwd":"senha-errada","c_id":1,"card":"4111222233334444"}'
