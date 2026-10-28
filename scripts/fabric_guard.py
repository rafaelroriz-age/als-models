"""Barreira contra escrita em dados que já existem no Fabric (tabelas Delta, schemas, views).

Permitido: ler, gravar em Files/als_oilmodel/, criar/atualizar notebooks `als_*`, views temporárias
(`CREATE [OR REPLACE] [GLOBAL] TEMP[ORARY] VIEW`, `createOrReplaceTempView`, `createTempView`).
Bloqueado: DML/DDL, `CREATE TABLE/VIEW` permanentes, saveAsTable/insertInto, operações Delta de
escrita e gravação em Tables/.
Quem decide liberar é uma pessoa, por variável de ambiente da sessão:
- ALS_FABRIC_ESCRITA=1 libera tudo;
- ALS_FABRIC_DEV=1 libera só tabelas/views cujo nome começa com `als_dev_` (criar, gravar, apagar).

O guard só lê o texto: nome montado dinamicamente vira violação, e escrita feita por outro caminho
não é vista. Uso como biblioteca: `violacoes(texto)`. Uso como hook: .claude/hooks/fabric_guard_hook.py.
"""
from __future__ import annotations

import os
import re

PREFIXO_DEV = "als_dev_"

_NOME = r"\s+(?:IF\s+(?:NOT\s+)?EXISTS\s+)?(?P<nome>[\w.`\"\[\]]+)?"
_ARG = r"\s*\(\s*[fFrR]?['\"]?(?P<nome>[\w.`]+)?"

# Padrões com grupo `nome`: aceitam exceção por prefixo als_dev_ quando ALS_FABRIC_DEV=1.
PADROES_COM_NOME = {
    "DML/DDL SQL": re.compile(
        r"\b(?:INSERT\s+INTO|DELETE\s+FROM|DROP\s+(?:TABLE|VIEW)|TRUNCATE\s+TABLE"
        r"|ALTER\s+(?:TABLE|VIEW)|MERGE\s+INTO)" + _NOME, re.I),
    "UPDATE SQL": re.compile(r"\bUPDATE\s+(?P<nome>[\w.\[\]`\"]+)\s+SET\b", re.I),
    "CREATE TABLE/VIEW permanente": re.compile(
        r"\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:EXTERNAL\s+)?(?:TABLE|VIEW)" + _NOME, re.I),
    "saveAsTable/insertInto": re.compile(r"\.(?:saveAsTable|insertInto)" + _ARG, re.I),
}

# Sem exceção possível.
PADROES_FIXOS = {
    "DDL de schema/database": re.compile(
        r"\b(?:DROP|ALTER|CREATE)\s+(?:OR\s+REPLACE\s+)?(?:SCHEMA|DATABASE)\b", re.I),
    "CREATE OR REPLACE de outro objeto": re.compile(
        r"\bCREATE\s+OR\s+REPLACE\s+(?!(?:GLOBAL\s+)?TEMP(?:ORARY)?\s+VIEW\b|(?:EXTERNAL\s+)?(?:TABLE|VIEW)\b)", re.I),
    "operação Delta de escrita": re.compile(r"DeltaTable[\s\S]{0,200}\.(delete|update|merge|vacuum|optimize)\s*\(", re.I),
    "gravação em Tables/": re.compile(
        r"(\.write\b|\.save\(|to_parquet\(|to_delta\(|put\(|upload)[^\n]{0,200}/Tables/", re.I),
}


def liberado() -> bool:
    return os.environ.get("ALS_FABRIC_ESCRITA") == "1"


def dev_liberado() -> bool:
    return os.environ.get("ALS_FABRIC_DEV") == "1"


def _nome_dev(nome: str | None) -> bool:
    if not nome:
        return False
    ultimo = re.sub(r"[`\"\[\]]", "", nome).split(".")[-1]
    return ultimo.lower().startswith(PREFIXO_DEV)


def violacoes(texto: str) -> list[str]:
    if liberado():
        return []
    dev = dev_liberado()
    achados = [
        nome for nome, rx in PADROES_COM_NOME.items()
        if any(not (dev and _nome_dev(m.group("nome"))) for m in rx.finditer(texto))
    ]
    achados += [nome for nome, rx in PADROES_FIXOS.items() if rx.search(texto)]
    return achados
