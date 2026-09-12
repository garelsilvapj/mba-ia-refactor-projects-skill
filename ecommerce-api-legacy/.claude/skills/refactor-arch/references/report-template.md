# Template de relatório

Reproduza estes três blocos textualmente, trocando apenas os valores. A moldura de `=` tem 32
caracteres. O relatório da Fase 2 é impresso no terminal **e** salvo em
`reports/audit-project-N.md` na raiz do repositório.

---

## Fase 1 — PROJECT ANALYSIS

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem>
Framework:     <framework + versão>
Dependencies:  <libs relevantes, separadas por vírgula>
Domain:        <domínio + entidades principais>
Architecture:  <classificação + uma frase explicando>
Source files:  <n> files analyzed
DB tables:     <tabelas ou coleções, separadas por vírgula>
Endpoints:     <n> routes
Entry point:   <comando de boot> (porta <n>)
================================
```

Regras:

- `Framework` inclui a versão do manifesto (ex.: `Flask 3.1.1`, `Express ^4.18.2`).
- `Architecture` é uma das classificações de `project-analysis.md`, seguida da justificativa.
- `Source files` exclui dependências, lockfiles e o diretório da skill.
- Se não houver banco, escreva `DB tables:     n/a`.

---

## Fase 2 — ARCHITECTURE AUDIT REPORT

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome da pasta do projeto>
Stack:   <linguagem + framework>
Files:   <n> analyzed | ~<linhas> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <Nome do anti-pattern>
File: <caminho/arquivo.ext>:<linha ou linha-linha>
Description: <o que está errado, concretamente, citando o identificador ou valor encontrado>
Impact: <consequência prática para segurança, manutenção ou performance>
Recommendation: <a correção, específica para este caso>

### [CRITICAL] <próximo>
...

### [HIGH] <...>
...

### [MEDIUM] <...>
...

### [LOW] <...>
...

================================
Total: <n> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Regras obrigatórias:

1. **Ordem:** todos os CRITICAL, depois HIGH, depois MEDIUM, depois LOW. Nunca intercalar.
2. **Localização:** todo finding tem `File:` com caminho relativo à raiz do projeto e linha ou
   faixa de linhas. Um finding que ocorre em muitos pontos cita o principal e lista os demais na
   `Description` (`também em models.py:57, 92, 140`).
3. **Description** é factual e específica: cite o nome da variável, o valor literal, a query, o
   endpoint. "Código mal escrito" não é descrição.
4. **Impact** responde "por que isso dói" em termos de risco, custo de manutenção ou performance.
5. **Recommendation** é acionável e cabe neste projeto: diz o que fazer, não "melhorar o código".
6. Se houver APIs deprecated, elas aparecem como finding próprio com o **equivalente moderno** na
   `Recommendation`. Se não houver nenhuma, registre na `Description` do relatório final:
   `Deprecated API scan: nenhuma ocorrência`.
7. A última linha é sempre a pergunta de confirmação. **Nada é modificado antes da resposta.**

---

## Fase 3 — REFACTORING COMPLETE

```
================================
PHASE 3: REFACTORING COMPLETE
================================
Project: <nome>

## New Project Structure
<árvore da estrutura nova, com uma linha por arquivo/pasta e o papel de cada camada>

## Findings Resolved
  [CRITICAL] <achado> → <o que foi feito> (<arquivo novo>)
  [HIGH]     <achado> → <o que foi feito> (<arquivo novo>)
  ...

## Validation
  ✓ Application boots without errors
  ✓ <n>/<n> endpoints respond as before
  ✓ <testes, se houver>
  ✓ Zero CRITICAL/HIGH findings remaining

## Intentional Behavior Changes
  - <mudança de resposta desejada e por quê, ex.: GET /usuarios não devolve mais 'senha'>

Remaining: CRITICAL: 0 | HIGH: 0 | MEDIUM: <n> | LOW: <n>
================================
```

Regras:

- A seção `Validation` reporta números reais da execução, não expectativas. Se um endpoint falhou,
  escreva `✗` e explique — não declare sucesso que não aconteceu.
- `Intentional Behavior Changes` é obrigatória sempre que a resposta mudar de propósito (campo
  sensível removido, 400 no lugar de 500, endpoint perigoso removido). Sem essa seção, qualquer
  diferença conta como regressão.
- `Remaining` só pode ter CRITICAL/HIGH diferente de zero com justificativa escrita logo abaixo.
