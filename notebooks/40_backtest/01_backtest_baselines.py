"""Backtest dos baselines (sem escolher modelo): KPI 1 amostras e KPI 2 faturamento, total e por cliente.

Entrada: <dados>/perfil/{amostras_cliente_mes,faturamento_cliente_mes}.parquet (gerados por 00_validacao/01).
Saída: <dados>/backtest/{previsoes,resumo}.parquet e, com ALS_MLFLOW=1, runs no MLflow (experimento als_backtest).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2] if "__file__" in globals() else Path.cwd()
sys.path.insert(0, str(RAIZ))

import pandas as pd  # noqa: E402

from src.backtest.harness import agregar_total, registrar_mlflow, resumir, rolling_origin  # noqa: E402
from src.features.regras import completar_meses  # noqa: E402
from src.gates.checks import avaliar_g1  # noqa: E402
from src.models.baselines import ingenuo_sazonal, media_movel  # noqa: E402
from src.pipeline.fabric import pasta_dados, salvar_json  # noqa: E402

DADOS = pasta_dados(RAIZ)
H = int(os.environ.get("ALS_HORIZONTE", "3"))
N_ORIGENS = int(os.environ.get("ALS_N_ORIGENS", "12"))
MODELOS = {
    "ingenuo_sazonal": ingenuo_sazonal,
    "media_movel_3": lambda t, h: media_movel(t, h, k=3),
    "media_movel_12": lambda t, h: media_movel(t, h, k=12),
}


def serie_mensal(path: Path, id_col: str, valor: str, excluir: str | None = None) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df = df[df["ano"].notna() & df[id_col].notna()]
    df["periodo"] = pd.to_datetime(dict(year=df["ano"].astype(int), month=df["mes"].astype(int), day=1))
    df["y"] = df[valor].astype(float) - (df[excluir].astype(float) if excluir else 0)
    df[id_col] = df[id_col].astype(str)
    ultimo_completo = pd.Timestamp.now().to_period("M").to_timestamp() - pd.DateOffset(months=1)
    df = df[(df["periodo"] <= ultimo_completo) & (df["periodo"] >= "2015-01-01")]
    base = completar_meses(df.rename(columns={id_col: "id"})[["id", "periodo", "y"]], chave="id", valor="y",
                           ate=ultimo_completo)
    return base


def rodar(nome: str, base: pd.DataFrame) -> pd.DataFrame:
    gates = avaliar_g1(base, ["id", "periodo"], "y")
    origens = pd.date_range(end=base["periodo"].max() - pd.DateOffset(months=H), periods=N_ORIGENS, freq="MS")
    prev_id = rolling_origin(base, MODELOS, origens, h=H)
    total = base.groupby("periodo", as_index=False)["y"].sum().assign(id="TOTAL")
    prev_tot = rolling_origin(total, MODELOS, origens, h=H)
    prev = pd.concat([prev_id.assign(nivel="cliente"), prev_tot.assign(nivel="total"),
                      agregar_total(prev_id).assign(nivel="soma_clientes")], ignore_index=True).assign(kpi=nome)
    resumo = resumir(prev, ["kpi", "nivel", "modelo", "horizonte"])
    salvar_json(gates, DADOS / "backtest" / f"gates_g1_{nome}.json")
    return prev, resumo


def main() -> None:
    perfil = DADOS / "perfil"
    kpis = {
        "kpi1_amostras": serie_mensal(perfil / "amostras_cliente_mes.parquet", "cliente_id", "amostras", excluir="avulsas"),
        "kpi2_faturamento": serie_mensal(perfil / "faturamento_cliente_mes.parquet", "cod_cliente", "total"),
    }
    prevs, resumos = [], []
    for nome, base in kpis.items():
        print(f"{nome}: {base['id'].nunique()} séries, {base['periodo'].min():%Y-%m}..{base['periodo'].max():%Y-%m}")
        p, r = rodar(nome, base)
        prevs.append(p)
        resumos.append(r)
    (DADOS / "backtest").mkdir(parents=True, exist_ok=True)
    prev, resumo = pd.concat(prevs), pd.concat(resumos)
    prev.to_parquet(DADOS / "backtest" / "previsoes.parquet", index=False)
    resumo.to_parquet(DADOS / "backtest" / "resumo.parquet", index=False)
    print(resumo[resumo["nivel"] != "cliente"].pivot_table(index=["kpi", "nivel", "modelo"], columns="horizonte",
                                                          values="wape").round(3).to_string())
    if os.environ.get("ALS_MLFLOW") == "1":
        geral = resumir(prev[prev["nivel"] == "total"], ["kpi", "modelo"])
        for kpi, g in geral.groupby("kpi"):
            registrar_mlflow(g, experimento=f"als_backtest_{kpi}", params={"h": H, "n_origens": N_ORIGENS})


if __name__ == "__main__":
    main()
