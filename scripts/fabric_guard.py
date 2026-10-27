"""Barreira contra escrita em dados que já existem no Fabric (tabelas Delta, schemas, views).

Permitido: ler, gravar em Files/als_oilmodel/, criar/atualizar notebooks `als_*`.
Bloqueado: DML/DDL, saveAsTable/insertInto, operações Delta de escrita e gravação em Tables/.
Quem decide liberar é uma pessoa: defina ALS_FABRIC_ESCRITA=1 no ambiente da sessão.

Uso como biblioteca: `violacoes(texto)`. Uso como hook: .claude/hooks/fabric_guard_hook.py.
"""
from __future__ import annotations

import os
import re

PADROES = {
    "DML/DDL SQL": re.compile(
        r"\b(INSERT\s+INTO|UPDATE\s+[\w.\[\]`\"]+\s+SET|DELETE\s+FROM|DROP\s+(TABLE|VIEW|SCHEMA|DATABASE)"
        r"|TRUNCATE\s+TABLE|ALTER\s+(TABLE|VIEW|SCHEMA)|MERGE\s+INTO|CREATE\s+OR\s+REPLACE)\b", re.I),
    "saveAsTable/insertInto": re.compile(r"\.(saveAsTable|insertInto)\s*\(", re.I),
    "operação Delta de escrita": re.compile(r"DeltaTable[\s\S]{0,200}\.(delete|update|merge|vacuum|optimize)\s*\(", re.I),
    "gravação em Tables/": re.compile(
        r"(\.write\b|\.save\(|to_parquet\(|to_delta\(|put\(|upload)[^\n]{0,200}/Tables/", re.I),
}


def liberado() -> bool:
    return os.environ.get("ALS_FABRIC_ESCRITA") == "1"


def violacoes(texto: str) -> list[str]:
    if liberado():
        return []
    return [nome for nome, rx in PADROES.items() if rx.search(texto)]
