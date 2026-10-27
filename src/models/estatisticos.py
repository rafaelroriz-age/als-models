"""Modelos estatísticos de série temporal (ETS, Theta) e de demanda intermitente (Croston, SBA, TSB).

Mesma assinatura dos baselines: f(treino, h) -> previsão, com treino = [id, periodo, y] (mensal) e
previsão = [id, periodo, yhat]; entram direto em `backtest.harness.rolling_origin`.
ETS e Theta usam statsmodels (extra opcional `stats`); Croston/SBA/TSB são numpy puro.

Série curta (menos de `min_obs` meses) ou falha numérica do ajuste degradam para a média móvel,
sem levantar erro; as previsões nunca são negativas (amostras não têm valor negativo).
"""
from __future__ import annotations

import warnings
from functools import partial
from typing import Callable

import numpy as np
import pandas as pd

from src.models.baselines import _futuro, media_movel

_FALLBACK_K = 3


def _fallback(y: np.ndarray, h: int) -> np.ndarray:
    return np.repeat(y[-_FALLBACK_K:].mean() if len(y) else 0.0, h)


# ---------- previsores por série (np.ndarray -> np.ndarray de tamanho h) ----------

def _ets(y: np.ndarray, h: int, m: int = 12) -> np.ndarray:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    sazonal = m if len(y) >= 2 * m and y.std() > 0 else None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = ExponentialSmoothing(y, trend="add", damped_trend=True, seasonal="add" if sazonal else None,
                                   seasonal_periods=sazonal, initialization_method="estimated").fit()
        return np.asarray(fit.forecast(h))


def _theta(y: np.ndarray, h: int, m: int = 12) -> np.ndarray:
    from statsmodels.tsa.forecasting.theta import ThetaModel

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        periodo = m if len(y) >= 2 * m else 1
        fit = ThetaModel(pd.Series(y), period=periodo, deseasonalize=periodo > 1).fit()
        return np.asarray(fit.forecast(h))


def _croston(y: np.ndarray, h: int, alpha: float = 0.1, variante: str = "classico") -> np.ndarray:
    """Croston clássico e SBA (fator de viés 1 − α/2) sobre tamanho da demanda e intervalo entre demandas."""
    idx = np.flatnonzero(y > 0)
    if len(idx) == 0:
        return np.zeros(h)
    z = y[idx[0]]                      # tamanho médio da demanda
    p = float(idx[0] + 1)              # intervalo médio entre demandas
    q = 1
    for t in range(idx[0] + 1, len(y)):
        if y[t] > 0:
            z += alpha * (y[t] - z)
            p += alpha * (q - p)
            q = 1
        else:
            q += 1
    f = z / p
    if variante == "sba":
        f *= 1 - alpha / 2
    return np.repeat(f, h)


def _tsb(y: np.ndarray, h: int, alpha: float = 0.1, beta: float = 0.1) -> np.ndarray:
    """TSB: probabilidade de demanda atualizada todo mês (captura obsolescência) × tamanho da demanda."""
    if not (y > 0).any():
        return np.zeros(h)
    primeiro = np.flatnonzero(y > 0)[0]
    z = y[primeiro]
    pr = (y > 0).mean()
    for v in y[primeiro:]:
        ocorreu = v > 0
        pr += beta * (float(ocorreu) - pr)
        if ocorreu:
            z += alpha * (v - z)
    return np.repeat(pr * z, h)


# ---------- adaptador para a assinatura do harness ----------

def _aplicar(treino: pd.DataFrame, h: int, previsor: Callable[[np.ndarray, int], np.ndarray],
             min_obs: int) -> pd.DataFrame:
    partes = []
    for k, g in treino.sort_values("periodo").groupby("id", sort=False):
        y = g["y"].to_numpy(dtype=float)
        yhat = None
        if len(y) >= min_obs:
            try:
                yhat = previsor(y, h)
                if not np.all(np.isfinite(yhat)):
                    yhat = None
            except Exception:  # ajuste não convergiu, dependência ausente, série degenerada
                yhat = None
        if yhat is None:
            yhat = _fallback(y, h)
        partes.append(pd.DataFrame({"id": k, "periodo": _futuro(g["periodo"].max(), h),
                                    "yhat": np.clip(yhat, 0, None)}))
    return pd.concat(partes, ignore_index=True)


def ets(treino: pd.DataFrame, h: int, m: int = 12, min_obs: int = 8) -> pd.DataFrame:
    """Holt-Winters aditivo com tendência amortecida; sazonal só com ≥ 2 ciclos (2m meses)."""
    return _aplicar(treino, h, partial(_ets, m=m), min_obs)


def theta(treino: pd.DataFrame, h: int, m: int = 12, min_obs: int = 8) -> pd.DataFrame:
    return _aplicar(treino, h, partial(_theta, m=m), min_obs)


def croston(treino: pd.DataFrame, h: int, alpha: float = 0.1, min_obs: int = 3) -> pd.DataFrame:
    return _aplicar(treino, h, partial(_croston, alpha=alpha), min_obs)


def sba(treino: pd.DataFrame, h: int, alpha: float = 0.1, min_obs: int = 3) -> pd.DataFrame:
    return _aplicar(treino, h, partial(_croston, alpha=alpha, variante="sba"), min_obs)


def tsb(treino: pd.DataFrame, h: int, alpha: float = 0.1, beta: float = 0.1, min_obs: int = 3) -> pd.DataFrame:
    return _aplicar(treino, h, partial(_tsb, alpha=alpha, beta=beta), min_obs)


MODELOS = {"ets": ets, "theta": theta, "croston": croston, "sba": sba, "tsb": tsb}

__all__ = ["ets", "theta", "croston", "sba", "tsb", "MODELOS", "media_movel"]
