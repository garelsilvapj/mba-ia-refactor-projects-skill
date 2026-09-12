"""Funções auxiliares de uso geral.

Antes este módulo tinha nove funções e um bloco de constantes; quase nada era usado, enquanto as
rotas repetiam a mesma lógica inline. Aqui ficou só o que é realmente usado — as constantes de
domínio foram para `config.py`, que é a fonte única.
"""
import re

EMAIL_RE = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")
COR_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def formatar_data(valor):
    """Mantém o formato de data das respostas: `str(datetime)` ou None."""
    return str(valor) if valor else None


def calcular_percentual(parte, total):
    if not total:
        return 0
    return round((parte / total) * 100, 2)


def email_valido(email):
    return bool(email) and bool(EMAIL_RE.match(email))


def cor_valida(cor):
    """Antes `is_valid_color` só checava tamanho e o '#', e nunca era chamada."""
    return bool(cor) and bool(COR_HEX_RE.match(cor))


def texto_limpo(valor):
    return valor.strip() if isinstance(valor, str) else valor


def escapar_like(termo):
    """Escapa os curingas do LIKE para que `%` e `_` sejam buscados literalmente."""
    return termo.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
