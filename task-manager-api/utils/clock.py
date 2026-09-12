"""Fonte única de "agora".

Antes o projeto chamava `datetime.utcnow()` em 24 pontos — API deprecated desde o Python 3.12,
que devolve datetime ingênuo (sem fuso). Aqui o valor nasce de `datetime.now(timezone.utc)`.

As colunas do banco continuam guardando UTC sem fuso, como antes, para não alterar o formato das
respostas já publicadas; `now_utc_naive()` faz essa conversão em um lugar só.
"""
from datetime import datetime, timezone


def now_utc():
    """Instante atual, com fuso (UTC)."""
    return datetime.now(timezone.utc)


def now_utc_naive():
    """Instante atual em UTC, sem fuso — formato usado nas colunas DateTime."""
    return now_utc().replace(tzinfo=None)


def as_naive_utc(valor):
    """Normaliza um datetime possivelmente com fuso para UTC sem fuso."""
    if valor is None:
        return None
    if valor.tzinfo is None:
        return valor
    return valor.astimezone(timezone.utc).replace(tzinfo=None)
