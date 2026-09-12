#!/usr/bin/env python3
"""audit.py — varredura estática de apoio à skill /refactor-arch (Fase 2).

Detecta heuristicamente os principais anti-patterns e emite o ARCHITECTURE AUDIT REPORT
com severidade + arquivo:linha. É um AUXÍLIO à skill (não a substitui): o agente revisa,
completa e conduz a refatoração da Fase 3.

Uso: python audit.py <caminho-do-projeto>
"""
import re
import sys
from pathlib import Path

IGNORE_DIRS = {"node_modules", "venv", ".git", "__pycache__", "dist", "build"}

# (severidade, título, regex, dica)
RULES = [
    ("CRITICAL", "Hardcoded Credentials",
     re.compile(r"""(SECRET_KEY|SECRET|PASSWORD|API_KEY|TOKEN)["'\]\s]*=\s*["'][^"']{6,}["']""", re.I),
     "Mover o segredo para variável de ambiente."),
    ("CRITICAL", "SQL Injection (f-string/concatenação em query)",
     re.compile(r"""(execute|query)\s*\(\s*f["']|["']\s*\+\s*\w+\s*\+\s*["']""", re.I),
     "Usar query parametrizada (placeholders)."),
    ("HIGH", "Regra de negócio no controller (rota calcula/valida)",
     re.compile(r"""(total\s*=\s*0|desconto|\btotal\s*\*=|preco\s*\*)""", re.I),
     "Mover a regra para um Service."),
    ("MEDIUM", "Possível N+1 (query dentro de laço)",
     re.compile(r"""for\s+\w+\s+in\s+.+:"""),
     "Resolver com JOIN/carregamento em lote (heurística: confirmar manualmente)."),
    ("LOW", "Magic number solto",
     re.compile(r"""[^.\w](\d{3,})[^.\w]"""),
     "Extrair para constante nomeada."),
]

SECRET_ASSIGN = RULES[0][2]


def iter_source(root: Path):
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in {".py", ".js", ".ts", ".php", ".rb"}:
            if not any(part in IGNORE_DIRS for part in p.parts):
                yield p


def scan(root: Path):
    findings = []
    files = list(iter_source(root))
    for f in files:
        try:
            lines = f.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, 1):
            for sev, title, rx, hint in RULES:
                if rx.search(line):
                    findings.append((sev, title, f.relative_to(root), i, line.strip()[:90], hint))
    return files, findings


def god_module_hint(files):
    """Heurística de God Module: um único arquivo grande com DDL + múltiplas tabelas."""
    for f in files:
        txt = f.read_text(encoding="utf-8", errors="ignore")
        tables = set(re.findall(r"CREATE TABLE(?: IF NOT EXISTS)?\s+(\w+)", txt, re.I))
        if len(tables) >= 3 and txt.count("\n") > 40:
            return f, tables
    return None, set()


SEV_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


def report(root: Path) -> str:
    files, findings = scan(root)
    gm_file, gm_tables = god_module_hint(files)
    if gm_file is not None:
        findings.append(("CRITICAL", "God Module (DB + queries de vários domínios num arquivo)",
                         gm_file.relative_to(root), 1,
                         f"tabelas: {', '.join(sorted(gm_tables))}", "Separar em models por domínio."))

    findings.sort(key=lambda x: (SEV_ORDER[x[0]], str(x[2]), x[3]))
    counts = {s: sum(1 for f in findings if f[0] == s) for s in SEV_ORDER}

    out = []
    out.append("=" * 32)
    out.append("PHASE 1: PROJECT ANALYSIS")
    out.append("=" * 32)
    out.append(f"Path:         {root}")
    out.append(f"Source files: {len(files)} analyzed")
    if gm_tables:
        out.append(f"DB tables:    {', '.join(sorted(gm_tables))}")
    out.append("=" * 32 + "\n")
    out.append("=" * 32)
    out.append("ARCHITECTURE AUDIT REPORT")
    out.append("=" * 32)
    out.append(f"Files:   {len(files)} analyzed")
    out.append(f"\nSummary\nCRITICAL: {counts['CRITICAL']} | HIGH: {counts['HIGH']} | "
               f"MEDIUM: {counts['MEDIUM']} | LOW: {counts['LOW']}\n")
    out.append("Findings\n")
    for sev, title, rel, line, snippet, hint in findings:
        out.append(f"[{sev}] {title}")
        out.append(f"File: {rel}:{line}")
        out.append(f"Description: {snippet}")
        out.append(f"Recommendation: {hint}\n")
    out.append("=" * 32)
    out.append(f"Total: {len(findings)} findings (heurística — o agente revisa e completa)")
    out.append("=" * 32)
    return "\n".join(out)


def main():
    if len(sys.argv) < 2:
        print("uso: python audit.py <caminho-do-projeto>")
        raise SystemExit(2)
    root = Path(sys.argv[1]).resolve()
    if not root.is_dir():
        print(f"não é um diretório: {root}")
        raise SystemExit(2)
    text = report(root)
    print(text)
    (root / "AUDIT_REPORT.md").write_text("# AUDIT_REPORT\n\n```\n" + text + "\n```\n", encoding="utf-8")
    print(f"\n(relatório salvo em {root / 'AUDIT_REPORT.md'})")


if __name__ == "__main__":
    main()
