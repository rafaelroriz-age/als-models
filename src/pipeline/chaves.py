"""Normalização e medição de casamento de chaves entre fontes (S360, Protheus, Zoho)."""
from __future__ import annotations

import re

import pandas as pd


def chave_erp(valor) -> str | None:
    """ERP ID normalizado (trim + maiúsculas); vazio vira None."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    s = str(valor).strip().upper()
    return s or None


def chave_grupo(valor) -> str | None:
    """Código-grupo do Protheus: o S360/Zoho numérico de 6 dígitos (ex. 191295) é 'A' + 5 dígitos + 1 dígito
    de filial (A19129 + 5). Demais códigos ficam como estão."""
    k = chave_erp(valor)
    if k and re.fullmatch(r"\d{6}", k):
        return "A" + k[:5]
    return k


def raiz_cnpj(valor) -> str | None:
    """Raiz do CNPJ (8 primeiros dígitos). Aceita 12 a 14 dígitos (completa com zeros à esquerda)."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    d = re.sub(r"\D", "", str(valor))
    if len(d) < 12 or len(d) > 14 or not set(d) - {"0"}:
        return None
    return d.zfill(14)[:8]


def taxa_casamento(origem: pd.Series, destino: pd.Series, pesos: pd.Series | None = None) -> dict:
    """Quantas chaves distintas de `origem` existem em `destino` (nulas fora do denominador).

    Com `pesos` (mesmo índice de `origem`), informa também a fração ponderada (ex.: faturamento).
    """
    dest = set(destino.dropna())
    ok = origem.notna()
    casa = origem.isin(dest) & ok
    res = {"n_chaves": int(origem[ok].nunique()), "n_casam": int(origem[casa].nunique())}
    res["pct"] = round(100 * res["n_casam"] / res["n_chaves"], 2) if res["n_chaves"] else None
    if pesos is not None:
        tot = pesos[ok].sum()
        res["pct_peso"] = round(100 * pesos[casa].sum() / tot, 2) if tot else None
    return res
