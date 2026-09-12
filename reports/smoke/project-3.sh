#!/usr/bin/env bash
# Smoke test do projeto 3 (task-manager-api): todos os 22 endpoints.
# Timestamps são normalizados para que o diff antes/depois seja estável.
set -u
BASE="${1:-http://127.0.0.1:5021}"

# O token do administrador do seed é obtido no login. O código original ignora o header
# Authorization; o refatorado o exige nas rotas protegidas.
TOKEN=$(curl -s -X POST "$BASE/login" -H 'Content-Type: application/json' \
  -d '{"email":"joao@email.com","password":"1234"}' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin).get("token",""))' 2>/dev/null)

req() {
  local method="$1" path="$2" data="${3:-}" sem_token="${4:-}"
  echo "--- $method $path ${sem_token:+(sem token)}"
  local args=(-s -o /tmp/body3.$$ -w '%{http_code}' -X "$method" "$BASE$path")
  [ -z "$sem_token" ] && args+=(-H "Authorization: Bearer $TOKEN")
  if [ -n "$data" ]; then
    args+=(-H 'Content-Type: application/json' -d "$data")
  fi
  curl "${args[@]}"
  echo ""
  sed -E 's/[0-9]{4}-[0-9]{2}-[0-9]{2}[ T][0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?/<TS>/g' /tmp/body3.$$ \
    | head -c 2000
  echo ""
  rm -f /tmp/body3.$$
}

req GET  /
req GET  /health

req GET  /tasks
req GET  /tasks/1
req GET  /tasks/9999
req POST /tasks '{"title":"Task de smoke test","description":"criada pelo smoke","status":"pending","priority":2,"user_id":1,"category_id":1,"due_date":"2027-01-15","tags":["smoke","teste"]}'
req POST /tasks '{"title":"ab"}'
req POST /tasks '{"title":"Status invalido","status":"nao-existe"}'
req POST /tasks '{"title":"Prioridade textual","priority":"alta"}'
req POST /tasks '{"title":"Usuario inexistente","user_id":9999}'
req PUT  /tasks/11 '{"title":"Task de smoke test editada","status":"in_progress","priority":1}'
req PUT  /tasks/9999 '{"title":"nao existe"}'
req DELETE /tasks/11
req DELETE /tasks/9999
req GET  "/tasks/search?q=API"
req GET  "/tasks/search?status=done"
req GET  "/tasks/search?priority=abc"
req GET  /tasks/stats

req GET  /users
req GET  /users/1
req GET  /users/9999
req POST /users '{"name":"Carlos Smoke","email":"carlos@email.com","password":"segredo","role":"user"}'
req POST /users '{"name":"Duplicado","email":"joao@email.com","password":"segredo"}'
req POST /users '{"name":"Email ruim","email":"nao-e-email","password":"segredo"}'
req PUT  /users/4 '{"name":"Carlos Editado","role":"manager"}'
req DELETE /users/4
req GET  /users/1/tasks
req POST /login '{"email":"joao@email.com","password":"1234"}'
req POST /login '{"email":"joao@email.com","password":"errada"}'

req GET  /reports/summary
req GET  /reports/user/1
req GET  /reports/user/9999

req GET  /categories
req POST /categories '{"name":"Smoke","description":"categoria de teste","color":"#123456"}'
req POST /categories '{"description":"sem nome"}'
req POST /categories '{"name":"Cor invalida","color":"azul"}'
req PUT  /categories/5 '{"name":"Smoke Editada"}'
req DELETE /categories/5
req PUT  /categories/9999 '{"name":"nao existe"}'

# Últimos casos de propósito: rotas protegidas sem token.
# No código original respondiam normalmente (200); no refatorado devolvem 401.
req GET /tasks "" sem-token
req GET /reports/summary "" sem-token
