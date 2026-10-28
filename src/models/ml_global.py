"""Modelo ML global: LightGBM com regressão quantílica (p10, p50, p90) treinado em todas as séries ao mesmo tempo.

Mesma assinatura dos baselines (`f(treino, h) -> previsão`): treino = [id, periodo, y] (+ `segmento` opcional),
previsão = [id, periodo, yhat, yhat_lo, yhat_hi] com yhat = p50, yhat_lo = p10 e yhat_hi = p90 (o harness lê
yhat_lo/yhat_hi para a cobertura do intervalo).

Estratégia direta empilhada: cada linha de treino é (mês t, horizonte k), com as features de T07 do mês t (que só
usam meses < t, ver `src/features/series.py`) e o alvo y(t + k − 1). A origem é o último mês do treino; só entram
alvos ≤ origem e a previsão usa as features do mês origem + 1, ou seja, só dados ≤ origem (sem vazamento, G2).
Com `normalizar=True` lags, médias e alvo são divididos por uma escala da própria linha (mm_12 → mm_3 → lag_1),
para o modelo aprender o formato da série e não o tamanho do cliente.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from src.features.series import ParametrosSeries, gerar_features

CATEGORICAS = ("segmento", "status")


@dataclass(frozen=True)
class ParametrosML:
    quantis: tuple[float, float, float] = (0.1, 0.5, 0.9)
    normalizar: bool = True
    nao_negativo: bool = True                 # consumo e receita não ficam negativos
    lgbm: dict = field(default_factory=lambda: {
        "n_estimators": 300, "learning_rate": 0.05, "num_leaves": 15, "min_child_samples": 20,
        "subsample": 0.8, "subsample_freq": 1, "colsample_bytree": 0.8, "reg_lambda": 1.0,
        "random_state": 42, "n_jobs": 1, "verbose": -1,
    })
    series: ParametrosSeries = field(default_factory=lambda: ParametrosSeries(incluir_status=False))


def _escala(f: pd.DataFrame) -> pd.Series:
    esc = f["mm_12"] if "mm_12" in f else pd.Series(np.nan, index=f.index)
    for c in ("mm_3", "lag_1"):
        if c in f:
            esc = esc.fillna(f[c])
    return esc.where(esc > 0, 1.0).fillna(1.0)


def montar_base(treino: pd.DataFrame, h: int, p: ParametrosML = ParametrosML()) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Matrizes de treino e de previsão (com `periodo_alvo`, `horizonte`, `escala` e o alvo `alvo`)."""
    df = treino.rename(columns={"id": "entidade", "y": "valor"})
    df = df.assign(periodo=pd.to_datetime(df["periodo"]).dt.to_period("M").dt.to_timestamp())
    origem = df["periodo"].max()
    cols = ["entidade", "periodo", "valor"] + (["segmento"] if "segmento" in df else [])
    f = gerar_features(df[cols], ate=origem + pd.DateOffset(months=1), p=p.series)
    for c in CATEGORICAS:
        if c in f:
            f[c] = f[c].astype("category")
    f["escala"] = _escala(f) if p.normalizar else 1.0
    num = [c for c in f if c.startswith(("lag_", "mm_", "tendencia_"))]
    f[num] = f[num].div(f["escala"], axis=0)

    partes = []
    for k in range(1, h + 1):
        g = f.copy()
        g["horizonte"] = k
        g["periodo_alvo"] = g["periodo"] + pd.DateOffset(months=k - 1)
        g["alvo"] = g.groupby("entidade", sort=False)["valor"].shift(-(k - 1)) / g["escala"]
        mes = g["periodo_alvo"].dt.month
        g["mes_sin"], g["mes_cos"] = np.sin(2 * np.pi * mes / 12), np.cos(2 * np.pi * mes / 12)
        partes.append(g)
    tudo = pd.concat(partes, ignore_index=True)
    fut = tudo["periodo"] == origem + pd.DateOffset(months=1)
    treino_ml = tudo[~fut & (tudo["periodo_alvo"] <= origem) & tudo["lag_1"].notna()]
    return treino_ml.reset_index(drop=True), tudo[fut].reset_index(drop=True)


def colunas_features(base: pd.DataFrame) -> list[str]:
    return [c for c in base if c.startswith(("lag_", "mm_", "tendencia_"))] + \
        ["mes_sin", "mes_cos", "horizonte"] + [c for c in CATEGORICAS if c in base]


def _ajustar(base: pd.DataFrame, p: ParametrosML) -> tuple[list, list[str]]:
    from lightgbm import LGBMRegressor

    x_cols = colunas_features(base)
    return [LGBMRegressor(objective="quantile", alpha=q, **p.lgbm).fit(base[x_cols], base["alvo"])
            for q in p.quantis], x_cols


def _prever_fut(modelos: list, x_cols: list[str], fut: pd.DataFrame, p: ParametrosML) -> pd.DataFrame:
    preds = np.column_stack([m.predict(fut[x_cols]) for m in modelos])
    preds = np.sort(preds, axis=1) * fut["escala"].to_numpy()[:, None]  # sem cruzamento de quantis
    if p.nao_negativo:
        preds = np.clip(preds, 0, None)
    return pd.DataFrame({"id": fut["entidade"].to_numpy(), "periodo": fut["periodo_alvo"].to_numpy(),
                         "yhat": preds[:, 1], "yhat_lo": preds[:, 0], "yhat_hi": preds[:, 2]})


def treinar(treino: pd.DataFrame, h: int, p: ParametrosML = ParametrosML()) -> tuple[list, list[str]]:
    """Ajusta um LGBMRegressor(objective='quantile') por quantil em todas as séries de `treino`."""
    return _ajustar(montar_base(treino, h, p)[0], p)


def prever(modelos: list, x_cols: list[str], historico: pd.DataFrame, h: int,
           p: ParametrosML = ParametrosML(), lote: int | None = None) -> pd.DataFrame:
    """Previsão dos h meses após o último mês de `historico` com modelos já treinados (`treinar`).

    `historico` pode ter séries que não entraram no treino (ex.: treino numa amostra, previsão em toda a frota);
    basta trazer os últimos 13 meses de cada série. `lote` divide as séries em blocos para caber na memória.
    """
    ids = historico["id"].unique()
    passo = lote or max(len(ids), 1)
    return pd.concat([_prever_fut(modelos, x_cols, montar_base(historico[historico["id"].isin(ids[i:i + passo])],
                                                                h, p)[1], p)
                      for i in range(0, len(ids), passo)], ignore_index=True)


def ml_global(treino: pd.DataFrame, h: int, p: ParametrosML = ParametrosML()) -> pd.DataFrame:
    """Um LGBMRegressor(objective='quantile') por quantil, treinado em todas as séries; quantis ordenados."""
    base, fut = montar_base(treino, h, p)
    modelos, x_cols = _ajustar(base, p)
    return _prever_fut(modelos, x_cols, fut, p)
