#!/usr/bin/env python3
"""Compara dois logs de smoke test (antes/depois), requisição a requisição."""
import re, sys


def parse(caminho):
    itens, atual = [], None
    for linha in open(caminho, encoding="utf-8", errors="replace"):
        linha = linha.rstrip("\n")
        if linha.startswith("--- "):
            atual = {"req": linha[4:], "status": None, "corpo": ""}
            itens.append(atual)
        elif atual is not None and atual["status"] is None and re.fullmatch(r"\d{3}", linha):
            atual["status"] = linha
        elif atual is not None and linha:
            atual["corpo"] += linha
    return itens


antes, depois = parse(sys.argv[1]), parse(sys.argv[2])
assert len(antes) == len(depois), f"nº de requisições difere: {len(antes)} vs {len(depois)}"

iguais = status_dif = corpo_dif = 0
for i, (a, d) in enumerate(zip(antes, depois), 1):
    assert a["req"] == d["req"], f"requisição {i} difere: {a['req']} vs {d['req']}"
    marca = "  "
    if a["status"] != d["status"]:
        marca, status_dif = "!!", status_dif + 1
    elif a["corpo"] != d["corpo"]:
        marca, corpo_dif = " ~", corpo_dif + 1
    else:
        iguais += 1
    print(f"{marca} {i:2d}. {a['req']:<55} {a['status']} -> {d['status']}")
    if marca != "  ":
        print(f"      antes : {a['corpo'][:220]}")
        print(f"      depois: {d['corpo'][:220]}")

print(f"\nidênticos: {iguais} | status diferente: {status_dif} | só corpo diferente: {corpo_dif}"
      f" | total: {len(antes)}")
