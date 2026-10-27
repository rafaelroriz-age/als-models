"""Comparação de candidatos contra os baselines no backtest: tabela modelo × nível × segmento × horizonte e gate G3.

Entrada: previsões longas do `harness.rolling_origin` com as colunas extras `nivel` e `segmento`.
G3 (docs_fabric/10): o candidato só é promovido se bater o melhor baseline no mesmo recorte (WAPE menor).
"""
from __future__ import annotations

import pandas as pd

from src.backtest.harness import resumir

BASELINES = ("ingenuo_sazonal", "media_movel_3", "media_movel_12")
SEM_SEGMENTO = "sem_segmento"
TODOS = "TODOS"


def rotular_segmento(s: pd.Series) -> pd.Series:
    """Segmento como texto; nulo, vazio e '-' viram `sem_segmento`."""
    s = s.astype("string").str.strip()
    return s.where(s.notna() & ~s.isin(["", "-"]), SEM_SEGMENTO).astype(str)


def ids_ativos(serie: pd.DataFrame, ate: str | pd.Timestamp, meses: int = 12) -> pd.Index:
    """Ids com consumo > 0 nos `meses` meses até `ate` (inclusive). Usar `ate` ≤ primeira origem: sem vazamento."""
    ate = pd.Timestamp(ate)
    janela = serie[(serie["periodo"] > ate - pd.DateOffset(months=meses)) & (serie["periodo"] <= ate)]
    soma = janela.groupby("id")["y"].sum()
    return soma[soma > 0].index


def tabela_comparativa(prev: pd.DataFrame, horizontes: tuple[int, ...] | None = (1, 3, 6)) -> pd.DataFrame:
    """Métricas por nível × segmento × modelo × horizonte, mais a linha segmento = TODOS de cada nível."""
    if horizontes is not None:
        prev = prev[prev["horizonte"].isin(horizontes)]
    por = ["nivel", "segmento", "modelo", "horizonte"]
    tab = pd.concat([resumir(prev, por), resumir(prev.assign(segmento=TODOS), por)], ignore_index=True)
    if "cobertura" not in tab:
        tab["cobertura"] = float("nan")
    return tab.sort_values(por, ignore_index=True)


def avaliar_g3(tabela: pd.DataFrame, baselines: tuple[str, ...] = BASELINES,
               por: tuple[str, ...] = ("nivel", "segmento", "horizonte")) -> pd.DataFrame:
    """Cada candidato contra o melhor baseline (menor WAPE) do mesmo recorte.

    Colunas: recorte, modelo, wape, bias_pct, cobertura, baseline, wape_baseline, ganho (1 − wape/wape_baseline),
    bate (wape < wape_baseline). Recorte sem baseline avaliável fica de fora.
    """
    por = list(por)
    base = tabela[tabela["modelo"].isin(baselines) & tabela["wape"].notna()]
    melhor = (base.sort_values("wape").drop_duplicates(por)[por + ["modelo", "wape"]]
              .rename(columns={"modelo": "baseline", "wape": "wape_baseline"}))
    cand = tabela[~tabela["modelo"].isin(baselines)]
    out = cand[por + ["modelo", "wape", "bias_pct", "cobertura"]].merge(melhor, on=por, how="inner")
    out["ganho"] = 1 - out["wape"] / out["wape_baseline"]
    out["bate"] = out["wape"] < out["wape_baseline"]
    return out.sort_values(por + ["wape"], ignore_index=True)


def resumo_g3(g3: pd.DataFrame, segmento: str = TODOS) -> pd.DataFrame:
    """Por modelo × nível: em quantos horizontes bate o baseline no recorte `segmento` e em quantos segmentos."""
    geral = g3[g3["segmento"] == segmento]
    segs = g3[g3["segmento"] != TODOS]
    a = geral.groupby(["nivel", "modelo"]).agg(horizontes_ganhos=("bate", "sum"), horizontes=("bate", "size"),
                                               ganho_medio=("ganho", "mean"))
    b = segs.groupby(["nivel", "modelo"]).agg(recortes_segmento_ganhos=("bate", "sum"),
                                              recortes_segmento=("bate", "size"))
    out = a.join(b, how="outer").reset_index()
    out["passa_g3"] = out["horizontes_ganhos"] == out["horizontes"]
    return out.sort_values(["nivel", "ganho_medio"], ascending=[True, False], ignore_index=True)


def registrar_mlflow_tabela(tabela: pd.DataFrame, experimento: str, params: dict | None = None) -> int:
    """Um run por nível × modelo × horizonte (segmento TODOS), métricas por segmento com sufixo; devolve nº de runs."""
    import mlflow

    mlflow.set_experiment(experimento)
    n = 0
    for (nivel, modelo, h), g in tabela.groupby(["nivel", "modelo", "horizonte"]):
        with mlflow.start_run(run_name=f"{modelo}|{nivel}|h{h}"):
            mlflow.log_params({**(params or {}), "modelo": modelo, "nivel": nivel, "horizonte": int(h)})
            metr = {}
            for _, r in g.iterrows():
                suf = "" if r["segmento"] == TODOS else "__" + "".join(c if c.isalnum() else "_" for c in r["segmento"])
                metr.update({f"{k}{suf}": float(r[k]) for k in ("wape", "bias_pct", "mae", "cobertura")
                             if pd.notna(r.get(k))})
            mlflow.log_metrics(metr)
        n += 1
    return n
