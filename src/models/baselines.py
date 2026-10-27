"""Baselines obrigatórios do backtest: ingênuo sazonal, média móvel e a regra atual do Forecast 27.

Assinatura comum dos modelos de série: f(treino, h) -> previsão,
treino = DataFrame [id, periodo, y] (mensal, contínuo), previsão = DataFrame [id, periodo, yhat].
"""
from __future__ import annotations

import pandas as pd


def _futuro(ultimo: pd.Timestamp, h: int) -> pd.DatetimeIndex:
    return pd.date_range(ultimo + pd.offsets.MonthBegin(1), periods=h, freq="MS")


def ingenuo_sazonal(treino: pd.DataFrame, h: int, m: int = 12) -> pd.DataFrame:
    """yhat(t) = y(t − m); sem histórico de m meses, repete o último valor."""
    partes = []
    for k, g in treino.sort_values("periodo").groupby("id", sort=False):
        y = g.set_index("periodo")["y"]
        fut = _futuro(y.index.max(), h)
        yhat = [y.get(t - pd.DateOffset(months=m), y.iloc[-1]) if len(y) >= m else y.iloc[-1] for t in fut]
        partes.append(pd.DataFrame({"id": k, "periodo": fut, "yhat": yhat}))
    return pd.concat(partes, ignore_index=True)


def media_movel(treino: pd.DataFrame, h: int, k: int = 3) -> pd.DataFrame:
    partes = []
    for i, g in treino.sort_values("periodo").groupby("id", sort=False):
        fut = _futuro(g["periodo"].max(), h)
        partes.append(pd.DataFrame({"id": i, "periodo": fut, "yhat": g["y"].tail(k).mean()}))
    return pd.concat(partes, ignore_index=True)


def regra_forecast27(componentes: pd.DataFrame, lag_conversao: int = 3, fracao_conversao: float = 0.5) -> pd.DataFrame:
    """Réplica da aba 'Projeção Receita' do Forecast 27.

    componentes: uma linha por mês, colunas recorrente_base, nao_recorrente, novos, reativados, churn, var_mercado.
    Recorrente(t) = base(t) + fração × (novos + reativados)(t − lag); Total = (rec + não rec + novos + reat) − churn;
    Novo total = Total × (1 + var_mercado).
    """
    c = componentes.reset_index(drop=True).copy()
    conv = (c["novos"] + c["reativados"]).shift(lag_conversao).fillna(0) * fracao_conversao
    c["recorrente"] = c["recorrente_base"] + conv
    c["total"] = c["recorrente"] + c["nao_recorrente"] + c["novos"] + c["reativados"] - c["churn"]
    c["total_ajustado"] = c["total"] * (1 + c["var_mercado"])
    return c


def ler_forecast27(path) -> pd.DataFrame:
    """Lê os componentes e os totais da planilha (valores calculados) para validar a réplica."""
    df = pd.read_excel(path, sheet_name="Projeção Receita", header=0, nrows=7)
    df = df.rename(columns={df.columns[0]: "mes", df.columns[1]: "recorrente_base"})
    return pd.DataFrame({
        "mes": df["mes"],
        "recorrente_base": df["recorrente_base"],
        "recorrente_planilha": df["Receita Recorrente Estimada"],
        "nao_recorrente": df["Receita Não Recorrente Ativa Estimada"],
        "novos": df["Receita Novos Clientes (Média)"],
        "reativados": df["Receita Clientes Reativados (Média)"],
        "churn": df["Perda de Receita (Churn)"],
        "total_planilha": df["Receita Total Estimada"],
        "var_mercado": df["Variaveis de Mercado/Cenário"],
        "total_ajustado_planilha": df["Novo Total Estimado"],
        "projecao_amostras": df[[c for c in df.columns if str(c).startswith("Projeção")][0]],
        "budget": df["BUDGET"],
    })
