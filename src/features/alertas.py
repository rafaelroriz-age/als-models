"""Alertas de consumo: queda >20% do cliente (RN-05) e compartimento churn (RN-06).

RN-05 compara as amostras do mês com uma base configurável: mesmo mês do ano anterior (`ano_anterior`),
média dos 3 meses anteriores (`mm3`) ou dos 12 meses anteriores (`mm12`). Padrão adotado: `ano_anterior`,
porque é a única base que já respeita a sazonalidade (RN-09). A escolha é decisão pendente com o negócio.

Entrada padrão de RN-05: tabela mensal por cliente com colunas `cliente`, `periodo` (1º dia do mês) e `valor`
(amostras). Mês sem linha na tabela é mês sem coleta: fica NaN, nunca zero, e não gera alerta.

Entrada padrão de RN-06: uma linha por coleta com `equipamento`, `compartimento`, `horimetro` (leitura na coleta),
`intervalo_h` (intervalo de coleta do compartimento, RN-01) e `horimetro_atual` (última leitura conhecida do equipamento).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

BASES = ("ano_anterior", "mm3", "mm12")
LIMIAR_QUEDA = 0.20   # "queda maior que 20%": 20,0% exatos não alertam
_TOL = 1e-9           # tolerância de ponto flutuante para o limiar


@dataclass(frozen=True)
class ParametrosChurnCompartimento:
    fator: float = 1.0   # "dentro do intervalo esperado": churn se horas sem coleta > fator × intervalo_h


def _serie_mensal(df: pd.DataFrame, chave: str, periodo: str, valor: str) -> pd.DataFrame:
    """Uma linha por chave × mês entre a primeira e a última coleta. Mês sem coleta fica NaN (não zero)."""
    df = df.assign(**{periodo: pd.to_datetime(df[periodo]).dt.to_period("M").dt.to_timestamp()})
    df = df.groupby([chave, periodo], as_index=False)[valor].sum()
    partes = []
    for k, g in df.groupby(chave, sort=False):
        idx = pd.date_range(g[periodo].min(), g[periodo].max(), freq="MS")
        s = g.set_index(periodo)[valor].reindex(idx)
        partes.append(pd.DataFrame({chave: k, periodo: idx, valor: s.to_numpy()}))
    if not partes:
        return pd.DataFrame(columns=[chave, periodo, valor])
    return pd.concat(partes, ignore_index=True)


def alertar_queda(mensal: pd.DataFrame, base: str = "ano_anterior", limiar: float = LIMIAR_QUEDA,
                  chave: str = "cliente", periodo: str = "periodo", valor: str = "valor") -> pd.DataFrame:
    """Por cliente × mês: `base_valor`, `queda` (1 − atual ÷ base) e `alerta_queda` (queda > limiar).

    Sem base calculável (série curta, mês base sem coleta, base ≤ 0) a queda é NaN e não há alerta.
    `mm3` e `mm12` usam só meses anteriores ao mês avaliado (shift), exigindo a janela completa.
    """
    if base not in BASES:
        raise ValueError(f"base de comparação inválida: {base!r}; use uma de {BASES}")
    s = _serie_mensal(mensal, chave, periodo, valor)
    partes = []
    for _, g in s.groupby(chave, sort=False):
        v = g[valor].astype(float)
        if base == "ano_anterior":
            ref = v.shift(12)
        else:
            n = 3 if base == "mm3" else 12
            ref = v.rolling(n, min_periods=n).mean().shift(1)
        partes.append(g.assign(base_valor=ref))
    out = pd.concat(partes, ignore_index=True) if partes else s.assign(base_valor=np.nan)
    out["queda"] = 1 - out[valor] / out["base_valor"].where(out["base_valor"] > 0)
    out["alerta_queda"] = out["queda"] > limiar + _TOL
    return out


def compartimento_churn(coletas: pd.DataFrame, p: ParametrosChurnCompartimento = ParametrosChurnCompartimento(),
                        ) -> pd.DataFrame:
    """Por equipamento × compartimento: `horas_sem_coleta` e `compartimento_churn` (RN-06).

    Churn = o equipamento rodou mais de `fator × intervalo_h` horas desde a última coleta do compartimento.
    Sem `horimetro_atual` ou sem horímetro na coleta, não é possível avaliar: fica False.
    """
    chaves = ["equipamento", "compartimento"]
    ultima = coletas.groupby(chaves, as_index=False).agg(
        horimetro=("horimetro", "max"),
        intervalo_h=("intervalo_h", "max"),
        horimetro_atual=("horimetro_atual", "max"),
    )
    ultima["horas_sem_coleta"] = ultima["horimetro_atual"] - ultima["horimetro"]
    ultima["compartimento_churn"] = ultima["horas_sem_coleta"] > p.fator * ultima["intervalo_h"]
    return ultima
