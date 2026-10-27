"""Regras de negócio de clientes (RN-03, churn, status, % Achieved) conforme Forecast 27 e Customer Status 2026.

Entrada padrão: tabela mensal por cliente com colunas
`cliente`, `periodo` (1º dia do mês), `valor` e, opcionalmente, `ultima_data` (última emissão no mês).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ParametrosRecorrencia:
    janela_meses: int = 12          # "últimos 12 meses completos"
    min_meses: int = 6              # "pelo menos 6 meses diferentes"
    dias_recencia: int = 90         # "última compra nos últimos 90 dias" (E, não OU: Forecast 27, linha 12)
    limiar_valor: float = 1.0       # Customer Status: COUNTIF(mês, ">1")
    meses_churn: int = 6            # "mais de seis meses sem comprar"
    meses_novo: int = 3             # novos/reativados viram recorrentes em 3 meses (Diego)
    meses_reativacao: int = 12      # reativado: "+1 ano desde o último faturamento"


def inicio_mes(s: pd.Series | pd.Timestamp):
    if isinstance(s, pd.Timestamp):
        return s.to_period("M").to_timestamp()
    return pd.to_datetime(s).dt.to_period("M").dt.to_timestamp()


def completar_meses(df: pd.DataFrame, chave: str = "cliente", periodo: str = "periodo",
                    valor: str = "valor", ate: pd.Timestamp | None = None) -> pd.DataFrame:
    """Uma linha por chave × mês, do primeiro mês da chave até `ate` (ou ao último mês global), com zeros."""
    df = df.assign(**{periodo: inicio_mes(df[periodo])})
    df = df.groupby([chave, periodo], as_index=False)[valor].sum()
    fim = inicio_mes(ate) if ate is not None else df[periodo].max()
    partes = []
    for k, g in df.groupby(chave, sort=False):
        idx = pd.date_range(g[periodo].min(), fim, freq="MS")
        partes.append(g.set_index(periodo)[[valor]].reindex(idx, fill_value=0).rename_axis(periodo)
                      .reset_index().assign(**{chave: k}))
    if not partes:
        return df.iloc[0:0]
    return pd.concat(partes, ignore_index=True)[[chave, periodo, valor]]


def classificar_clientes(mensal: pd.DataFrame, data_corte: str | pd.Timestamp,
                         p: ParametrosRecorrencia = ParametrosRecorrencia()) -> pd.DataFrame:
    """Classe por cliente na data de corte: recorrente, nao_recorrente_ativo, novo, reativado ou churn."""
    corte = pd.Timestamp(data_corte)
    mes_corte = inicio_mes(corte)
    df = mensal.copy()
    df["periodo"] = inicio_mes(df["periodo"])
    if "ultima_data" not in df:
        df["ultima_data"] = df["periodo"] + pd.offsets.MonthEnd(0)
    df = df[(df["periodo"] <= mes_corte) & (df["valor"] > 0)]
    ini_janela = mes_corte - pd.DateOffset(months=p.janela_meses - 1)

    g = df.groupby("cliente")
    out = pd.DataFrame({
        "primeira_compra": g["periodo"].min(),
        "ultima_compra": g["ultima_data"].max().clip(upper=corte),
        "meses_com_compra_12m": df[(df["periodo"] >= ini_janela) & (df["valor"] > p.limiar_valor)]
        .groupby("cliente")["periodo"].nunique(),
        "valor_12m": df[df["periodo"] >= ini_janela].groupby("cliente")["valor"].sum(),
    })
    out[["meses_com_compra_12m", "valor_12m"]] = out[["meses_com_compra_12m", "valor_12m"]].fillna(0)
    out["dias_desde_ultima"] = (corte - out["ultima_compra"]).dt.days

    # maior intervalo sem compra antes da compra mais recente (para reativação)
    def _gap_antes_da_ultima(s: pd.Series) -> float:
        meses = np.sort(s.unique())
        if len(meses) < 2:
            return np.nan
        m = pd.DatetimeIndex(meses)
        return (m[-1].year - m[-2].year) * 12 + (m[-1].month - m[-2].month)

    out["gap_meses_antes_ultima"] = g["periodo"].apply(_gap_antes_da_ultima)

    limite_churn = corte - pd.DateOffset(months=p.meses_churn)
    ini_novo = mes_corte - pd.DateOffset(months=p.meses_novo - 1)
    recorrente = (out["meses_com_compra_12m"] >= p.min_meses) & (out["dias_desde_ultima"] <= p.dias_recencia)
    churn = out["ultima_compra"] < limite_churn
    novo = out["primeira_compra"] >= ini_novo
    reativado = (inicio_mes(out["ultima_compra"]) >= ini_novo) & (out["gap_meses_antes_ultima"] > p.meses_reativacao)

    out["classe"] = np.select(
        [churn, recorrente, novo, reativado],
        ["churn", "recorrente", "novo", "reativado"],
        default="nao_recorrente_ativo",
    )
    out["data_corte"] = corte
    return out.reset_index()


def status_real(ultima_venda: pd.Series, ultima_amostra: pd.Series, referencia: str | pd.Timestamp,
                dias_ativo: int = 90, dias_inativo: int = 180) -> pd.Series:
    """Customer Status 'Real Status' (concorda em ~91% com a planilha de 2026):
    última atividade = max(última venda, última amostra); ≤90 d Active, ≤180 d Inactive, senão Churn."""
    ultima = pd.concat([pd.to_datetime(ultima_venda), pd.to_datetime(ultima_amostra)], axis=1).max(axis=1)
    dias = (pd.Timestamp(referencia) - ultima).dt.days
    st = np.where(dias <= dias_ativo, "Active", np.where(dias <= dias_inativo, "Inactive", "Churn"))
    return pd.Series(np.where(ultima.isna(), "Churn", st), index=ultima_venda.index)


def receita_churn(mensal: pd.DataFrame, clientes_churn: pd.DataFrame, meses: int = 6) -> pd.DataFrame:
    """Receita perdida = média mensal dos `meses` meses até a última compra (inclusive), com meses sem compra = 0."""
    base = completar_meses(mensal[["cliente", "periodo", "valor"]])
    ult = clientes_churn.set_index("cliente")["ultima_compra"].pipe(inicio_mes)
    base = base[base["cliente"].isin(ult.index)].copy()
    base["ultimo_mes"] = base["cliente"].map(ult)
    janela = (base["periodo"] <= base["ultimo_mes"]) & (
        base["periodo"] > base["ultimo_mes"] - pd.DateOffset(months=meses))
    soma = base[janela].groupby("cliente")["valor"].sum()
    return (soma / meses).rename("receita_churn_mensal").reset_index()


def pct_achieved(realizadas: pd.Series, potencial_anual: pd.Series) -> pd.Series:
    """% Achieved = amostras realizadas ÷ potencial anual (D6). Potencial ausente ou ≤0 → NaN."""
    pot = pd.to_numeric(potencial_anual, errors="coerce")
    return pd.to_numeric(realizadas, errors="coerce") / pot.where(pot > 0)


def marcar_avulsas(amostras: pd.DataFrame, col_compartimento: str = "compartimento_id") -> pd.DataFrame:
    """D9: amostra avulsa = sem compartimento (logo sem equipamento). Só marca; a exclusão é do pré-processamento."""
    return amostras.assign(avulsa=amostras[col_compartimento].isna())
