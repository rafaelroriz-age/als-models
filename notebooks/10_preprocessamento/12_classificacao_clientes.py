"""Protótipo da Fase 1b: classifica os clientes do Customer Status e compara com o status manual.

Entrada: <dados>/planilhas/customer_status.parquet (ou ALS_CUSTOMER_STATUS). Referência: ALS_REFERENCIA (padrão 2026-08-10).
Saída: <dados>/classificacao/clientes_classe.parquet e resumo.json.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2] if "__file__" in globals() else Path.cwd()
sys.path.insert(0, str(RAIZ))

import pandas as pd  # noqa: E402

from src.features.classificacao import (  # noqa: E402
    arvore_interpretavel, classificar, concordancia_status)
from src.pipeline.fabric import pasta_dados, salvar_json  # noqa: E402

DADOS = pasta_dados(RAIZ)
ARQ = Path(os.environ.get("ALS_CUSTOMER_STATUS", DADOS / "planilhas" / "customer_status.parquet"))
REF = pd.Timestamp(os.environ.get("ALS_REFERENCIA", "2026-08-10"))

df = pd.read_parquet(ARQ)
res = classificar(df, REF)
df = df.join(res)

dist = df.groupby("classe", observed=True).agg(
    clientes=("ERP ID", "size"), faturamento_12m=("Faturamento 12 meses", "sum"),
    amostras_ano_fy26=("Current Samples (Apr to July  FY 26/27)", "sum"))
dist["pct_clientes"] = dist["clientes"] / dist["clientes"].sum()
dist["pct_faturamento"] = dist["faturamento_12m"] / dist["faturamento_12m"].sum()
print(dist.round(3).to_string())

conc = concordancia_status(df["classe"], df["Real Status"])
print("\nClasse × Real Status manual\n", conc["tabela"].to_string())
print({k: v for k, v in conc.items() if k != "tabela"})

arv = arvore_interpretavel(df, REF, df["Real Status"])
print("\nÁrvore (prof. 3) acurácia CV 3 classes:", round(arv["acuracia_cv"], 3))
print(arv["regras"])

saida = DADOS / "classificacao"
saida.mkdir(parents=True, exist_ok=True)
df[["ERP ID", "CLIENT", "Real Status", "dias_sem_atividade", "pontos_piramide", "classe"]].to_parquet(
    saida / "clientes_classe.parquet", index=False)
salvar_json({
    "referencia": str(REF.date()), "distribuicao": dist.reset_index().astype({"classe": str}).to_dict("records"),
    "concordancia": {k: v for k, v in conc.items() if k != "tabela"},
    "arvore": {"acuracia_cv": arv["acuracia_cv"], "importancias": arv["importancias"]},
}, saida / "resumo.json")
