"""Reconciliação hierárquica Cliente → Equipamento → Compartimento (bottom-up e top-down).

Tabelas: [cliente, equipamento, compartimento, periodo, <valor>]. Os atributos de agregação
(tipo_equipamento, setor, segmento) vêm de uma tabela de atributos por folha
[cliente, equipamento, compartimento, tipo_equipamento, setor, segmento], para que a mesma folha
possa ser somada por qualquer corte sem perder a coerência com o total.

Extensão documentada (não implementada): MinT (Wickramasuriya et al., 2019). Reconciliação ótima
ŷ̃ = S (SᵀW⁻¹S)⁻¹ SᵀW⁻¹ ŷ, com S = matriz de soma da hierarquia e W = covariância dos erros de
previsão em h passos (ex.: shrinkage dos resíduos in-sample). Exige previsões independentes em todos
os níveis, a serem geradas pelos modelos de T10/T11; bottom-up equivale a W que ignora os níveis
superiores e top-down é o caso particular com proporções fixas.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

FOLHA = ["cliente", "equipamento", "compartimento"]
NIVEIS = {
    "total": [],
    "cliente": ["cliente"],
    "equipamento": ["cliente", "equipamento"],
    "compartimento": FOLHA,
}


def bottom_up(prev_folha: pd.DataFrame, valor: str = "yhat") -> dict[str, pd.DataFrame]:
    """Soma a previsão por compartimento para cada nível acima; níveis somam por construção."""
    out = {}
    for nome, chaves in NIVEIS.items():
        out[nome] = prev_folha.groupby(chaves + ["periodo"], as_index=False)[valor].sum()
    return out


def proporcoes_historicas(historico: pd.DataFrame, valor: str = "y", janela: int | None = None) -> pd.DataFrame:
    """Participação de cada compartimento no total do seu cliente, pelo histórico.

    janela = últimos N períodos (None = tudo). Cliente sem volume no histórico divide igualmente
    entre as folhas conhecidas. Devolve [cliente, equipamento, compartimento, proporcao]; soma 1 por cliente.
    """
    h = historico
    if janela is not None:
        corte = sorted(h["periodo"].unique())[-janela:]
        h = h[h["periodo"].isin(corte)]
    folhas = historico[FOLHA].drop_duplicates()
    vol = h.groupby(FOLHA, as_index=False)[valor].sum().rename(columns={valor: "_vol"})
    p = folhas.merge(vol, on=FOLHA, how="left").fillna({"_vol": 0.0})
    total = p.groupby("cliente")["_vol"].transform("sum")
    n = p.groupby("cliente")["_vol"].transform("size")
    p["proporcao"] = np.where(total > 0, p["_vol"] / total.where(total > 0, 1.0), 1.0 / n)
    return p[FOLHA + ["proporcao"]]


def top_down(prev_cliente: pd.DataFrame, historico: pd.DataFrame, valor: str = "yhat",
             valor_hist: str = "y", janela: int | None = None) -> dict[str, pd.DataFrame]:
    """Desagrega a previsão por cliente [cliente, periodo, yhat] até o compartimento, por proporções históricas.

    Equipamento = soma dos seus compartimentos, então os três níveis fecham exatamente com o cliente.
    """
    prop = proporcoes_historicas(historico, valor_hist, janela)
    folha = prev_cliente.merge(prop, on="cliente", how="inner")
    sem_hist = set(prev_cliente["cliente"]) - set(prop["cliente"])
    if sem_hist:
        raise ValueError(f"clientes sem histórico para proporções: {sorted(sem_hist)}")
    folha[valor] = folha[valor] * folha["proporcao"]
    return bottom_up(folha[FOLHA + ["periodo", valor]], valor)


def agregar(prev_folha: pd.DataFrame, atributos: pd.DataFrame, por: str | list[str],
            valor: str = "yhat") -> pd.DataFrame:
    """Soma a previsão por compartimento por tipo_equipamento, setor, segmento (ou combinação)."""
    por = [por] if isinstance(por, str) else list(por)
    dup = atributos.duplicated(FOLHA).any()
    if dup:
        raise ValueError("atributos com mais de uma linha por folha")
    m = prev_folha.merge(atributos[FOLHA + por], on=FOLHA, how="left")
    if m[por].isna().any().any():
        raise ValueError(f"folhas sem atributo {por}")
    return m.groupby(por + ["periodo"], as_index=False)[valor].sum()


def verificar_coerencia(niveis: dict[str, pd.DataFrame], valor: str = "yhat", tol: float = 1e-9) -> bool:
    """True se cada nível soma o mesmo total por período que o compartimento."""
    ref = niveis["compartimento"].groupby("periodo")[valor].sum()
    for nome, df in niveis.items():
        s = df.groupby("periodo")[valor].sum()
        if not np.allclose(s.reindex(ref.index).to_numpy(), ref.to_numpy(), atol=tol, rtol=0):
            return False
    return True
