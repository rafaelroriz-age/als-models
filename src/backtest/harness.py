"""Backtest com origem móvel (rolling origin), igual para todo modelo candidato e para os baselines."""
from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

Modelo = Callable[[pd.DataFrame, int], pd.DataFrame]


def metricas(y: pd.Series, yhat: pd.Series, lo: pd.Series | None = None, hi: pd.Series | None = None) -> dict:
    y, yhat = y.astype(float), yhat.astype(float)
    err = yhat - y
    denom = np.abs(y).sum()
    smape_den = (np.abs(y) + np.abs(yhat))
    out = {
        "n": int(len(y)),
        "wape": float(np.abs(err).sum() / denom) if denom else np.nan,
        "mae": float(np.abs(err).mean()),
        "bias_pct": float(err.sum() / denom) if denom else np.nan,
        "smape": float(np.mean(np.where(smape_den == 0, 0, 2 * np.abs(err) / smape_den.replace(0, 1)))),
    }
    if lo is not None and hi is not None:
        # só linhas com intervalo: modelo sem intervalo empilhado com outro que tem fica NaN (não 0)
        com = lo.notna() & hi.notna()
        out["cobertura"] = float(((y >= lo) & (y <= hi))[com].mean()) if com.any() else np.nan
    return out


def rolling_origin(serie: pd.DataFrame, modelos: dict[str, Modelo], origens: list[str | pd.Timestamp],
                   h: int = 3, min_treino: int = 12) -> pd.DataFrame:
    """serie [id, periodo, y] mensal. Para cada origem, treina com periodo ≤ origem e prevê h meses.

    Retorna previsões longas: modelo, origem, id, periodo, horizonte, y, yhat (+ yhat_lo/yhat_hi se houver).
    """
    serie = serie.assign(periodo=pd.to_datetime(serie["periodo"]).dt.to_period("M").dt.to_timestamp())
    linhas = []
    for origem in pd.to_datetime(origens):
        origem = origem.to_period("M").to_timestamp()
        treino = serie[serie["periodo"] <= origem]
        n_meses = treino.groupby("id")["periodo"].nunique()
        treino = treino[treino["id"].isin(n_meses[n_meses >= min_treino].index)]
        if treino.empty:
            continue
        teste = serie[(serie["periodo"] > origem) & (serie["periodo"] <= origem + pd.DateOffset(months=h))]
        for nome, modelo in modelos.items():
            prev = modelo(treino, h)
            prev = prev.merge(teste, on=["id", "periodo"], how="inner")
            prev["horizonte"] = ((prev["periodo"].dt.year - origem.year) * 12 + prev["periodo"].dt.month - origem.month)
            prev["modelo"], prev["origem"] = nome, origem
            linhas.append(prev)
    return pd.concat(linhas, ignore_index=True) if linhas else pd.DataFrame()


def resumir(prev: pd.DataFrame, por: list[str] | None = None) -> pd.DataFrame:
    por = por or ["modelo"]
    tem_intervalo = {"yhat_lo", "yhat_hi"} <= set(prev.columns)
    rows = []
    for k, g in prev.groupby(por):
        m = metricas(g["y"], g["yhat"], g.get("yhat_lo") if tem_intervalo else None,
                     g.get("yhat_hi") if tem_intervalo else None)
        rows.append({**dict(zip(por, k if isinstance(k, tuple) else (k,))), **m})
    return pd.DataFrame(rows).sort_values(por)


def agregar_total(prev: pd.DataFrame) -> pd.DataFrame:
    """Soma previsões e realizados de todos os ids por modelo/origem/período (visão do KPI agregado)."""
    cols = ["y", "yhat"] + [c for c in ("yhat_lo", "yhat_hi") if c in prev]
    return (prev.groupby(["modelo", "origem", "periodo", "horizonte"], as_index=False)[cols].sum()
            .assign(id="TOTAL"))


def registrar_mlflow(resumo: pd.DataFrame, experimento: str = "als_backtest", params: dict | None = None) -> None:
    import mlflow

    mlflow.set_experiment(experimento)
    for _, r in resumo.iterrows():
        with mlflow.start_run(run_name=str(r["modelo"])):
            mlflow.log_params({**(params or {}), "modelo": r["modelo"]})
            mlflow.log_metrics({k: float(v) for k, v in r.items()
                                if k in ("wape", "mae", "bias_pct", "smape", "cobertura") and pd.notna(v)})
