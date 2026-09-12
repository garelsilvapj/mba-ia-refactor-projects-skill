---
name: refactor-arch
description: |
  Use quando o usuário pedir "/refactor-arch", "auditar a arquitetura", "refatorar para MVC",
  "revisar code smells", "achar anti-patterns", "esse projeto é um monólito, organiza isso" ou
  herdar um projeto legado que precisa de saneamento arquitetural e de segurança. Serve para
  qualquer stack (Python/Flask, Node/Express, PHP/Laravel, Ruby/Rails, Go, Java), inclusive
  projetos que já têm alguma separação de camadas.
---

# refactor-arch — Auditoria e Refatoração Arquitetural para MVC

Transforma um projeto com problemas de arquitetura, segurança e qualidade em um projeto
organizado no padrão **MVC**, de forma **agnóstica de tecnologia**.

O workflow tem **3 fases sequenciais**. Execute-as na ordem. **A Fase 3 nunca começa sem
confirmação explícita do usuário.**

## Princípios inegociáveis

1. **Nunca invente achados.** Todo finding aponta `arquivo:linha` real, verificado com
   `grep -n`/leitura do arquivo. Se não conseguir citar a linha, o finding não entra.
2. **Nenhuma escrita antes do `y`.** Fases 1 e 2 são somente-leitura. A primeira modificação de
   arquivo acontece depois da confirmação do usuário.
3. **Comportamento preservado.** Rotas, status codes e o formato das respostas continuam os
   mesmos após a Fase 3. Mudança de contrato só com aviso explícito no relatório final.
4. **Baseline antes de tocar.** Sem a captura do comportamento original (Fase 3, passo 1) não há
   como provar que nada quebrou. Não pule.
5. **Adapte-se ao contexto.** Um monólito de 4 arquivos e um projeto que já tem `models/` e
   `routes/` exigem transformações diferentes. Leia a arquitetura antes de escolher o alvo.

---

## Fase 1 — Análise do projeto (somente leitura)

Objetivo: entender o que é o projeto antes de julgá-lo.

**Leia `references/project-analysis.md`** e siga as heurísticas de lá para detectar:

1. **Linguagem e framework + versão** — pelos manifestos (`requirements.txt`, `package.json`,
   `composer.json`, `go.mod`, `Gemfile`) e pelos imports.
2. **Dependências relevantes** — ORM, driver de banco, CORS, validação, auth.
3. **Domínio** — as entidades do negócio (produtos/pedidos, cursos/matrículas, tarefas/usuários).
4. **Arquitetura atual** — monólito de N arquivos? camadas parciais? onde estão a regra de
   negócio, o acesso a dados e o roteamento?
5. **Arquivos-fonte** — contagem real (exclua `node_modules`, `.venv`, `dist`, `__pycache__`,
   lockfiles).
6. **Tabelas/coleções** — de `CREATE TABLE`, migrations ou classes de ORM.
7. **Inventário de endpoints** — método + rota + `arquivo:linha`. Esta lista é o contrato que a
   Fase 3 tem de preservar; guarde-a.

Imprima o bloco **PHASE 1: PROJECT ANALYSIS** exatamente como em `references/report-template.md`.

---

## Fase 2 — Auditoria (somente leitura)

Objetivo: produzir o relatório de achados classificados por severidade.

**Leia `references/antipatterns-catalog.md`** (catálogo de anti-patterns com sinais de detecção
e severidade) e **`references/report-template.md`** (formato do relatório).

1. Para **cada** anti-pattern do catálogo, rode os sinais de detecção sugeridos (`grep -n` e
   leitura dirigida) contra os arquivos-fonte. O catálogo tem uma seção dedicada a **APIs
   deprecated** — rode-a sempre e reporte o equivalente moderno de cada API obsoleta achada.
2. Para cada achado confirmado registre: **título do padrão**, `arquivo:linha` (ou faixa
   `linha-linha`), **Description**, **Impact**, **Recommendation**.
3. Ordene os achados por severidade: **CRITICAL → HIGH → MEDIUM → LOW**.
4. Imprima o bloco **ARCHITECTURE AUDIT REPORT** e salve o mesmo conteúdo em
   `reports/audit-project-N.md` na raiz do repositório (ou em `AUDIT_REPORT.md` na raiz do
   projeto, se não houver `reports/`).
5. **PARE.** Pergunte, literalmente:

   ```
   Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
   ```

   Espere a resposta do usuário. Só um `y`/`sim` explícito autoriza a Fase 3. Qualquer outra
   coisa encerra o trabalho com o relatório entregue.

> Apoio opcional: `python scripts/audit.py <projeto>` faz uma varredura estática inicial
> (segredos, SQL injection, God Module, N+1, magic numbers). É um **ponto de partida**;
> confirme cada `arquivo:linha` e complete com a leitura dirigida — heurística não substitui a
> análise do agente.

**Mínimos de qualidade da Fase 2:** ≥ 5 findings, ≥ 1 CRITICAL ou HIGH, todos com
`arquivo:linha`, ordenados por severidade.

---

## Fase 3 — Refatoração para MVC + validação

**Só execute após o `y` do usuário.**

**Leia `references/architecture-guidelines.md`** (a arquitetura MVC alvo e as responsabilidades
de cada camada) e **`references/refactoring-playbook.md`** (as transformações concretas,
anti-pattern por anti-pattern, com código antes/depois).

### Passo 1 — Capturar o baseline (antes de qualquer modificação)

1. Instale as dependências e suba a aplicação original.
2. Faça uma requisição a **cada endpoint** do inventário da Fase 1 e grave status + corpo em um
   arquivo de log (ex.: `reports/logs/project-N-before.txt`).
3. Derrube a aplicação. Esse log é o gabarito da validação final.

Se a aplicação não subir no estado original, registre isso no relatório e use os testes
existentes (ou o próprio inventário de rotas) como contrato.

### Passo 2 — Refatorar incrementalmente

Resolva os achados na ordem **CRITICAL → HIGH → MEDIUM → LOW**, aplicando os padrões do
playbook. A estrutura alvo sai de `architecture-guidelines.md` e depende da stack detectada.

Regras:

- Uma preocupação por vez; não misture "mover arquivo" com "mudar comportamento".
- Cada segredo hardcoded vira variável de ambiente com `.env.example` documentando a chave.
- Toda query concatenada vira query parametrizada.
- Regra de negócio sai do controller para um service/model.
- O error handling vira centralizado (handler global), não `try/except` copiado em cada rota.
- O entry point fica explícito e mínimo (composition root).

### Passo 3 — Validar

1. Suba a aplicação refatorada. **Ela tem de iniciar sem erros.**
2. Repita **todas** as requisições do baseline e grave em `reports/logs/project-N-after.txt`.
3. Compare com o baseline: mesmos status codes e mesma forma de resposta.
   - Diferença esperada e desejada (ex.: senha que antes vazava e agora não aparece; 400 no lugar
     de 500 para entrada inválida) deve ser **listada explicitamente** como melhoria.
   - Qualquer outra diferença é regressão: **corrija antes de concluir.**
4. Rode os testes automatizados, se existirem.

### Passo 4 — Relatar

Imprima o bloco **PHASE 3: REFACTORING COMPLETE** de `references/report-template.md`, com:
estrutura antes → depois, mapa achado → correção → arquivo novo, resultado da validação
endpoint a endpoint, e a contagem de achados remanescentes.

Nenhum CRITICAL ou HIGH pode ficar sem tratamento ou sem justificativa explícita.

---

## Red flags — pare e volte atrás

| Você está prestes a... | Faça em vez disso |
|---|---|
| Escrever um finding sem abrir o arquivo | `grep -n` primeiro; sem linha, sem finding |
| Editar um arquivo antes do `y` | Pare. Fases 1 e 2 são somente-leitura |
| "Já entendi o projeto, pulo o baseline" | Sem baseline não há prova de que nada quebrou |
| Reescrever a aplicação do zero | Refatoração preserva comportamento; reescrita não |
| Deixar um endpoint sem testar "porque é simples" | Todo endpoint do inventário entra na validação |
| Concluir com a app sem subir | A Fase 3 só termina com a aplicação rodando |

## Arquivos de referência

| Arquivo | Usado na | Conteúdo |
|---|---|---|
| `references/project-analysis.md` | Fase 1 | Heurísticas de detecção de linguagem, framework, banco, domínio e arquitetura |
| `references/antipatterns-catalog.md` | Fase 2 | 19 anti-patterns com sinais de detecção, severidade e APIs deprecated |
| `references/report-template.md` | Fases 1-3 | Formato exato dos três blocos de saída |
| `references/architecture-guidelines.md` | Fase 3 | Regras do MVC alvo e responsabilidades das camadas |
| `references/refactoring-playbook.md` | Fase 3 | 15 transformações com código antes/depois |
| `scripts/audit.py` | Fase 2 (apoio) | Varredura estática opcional |
