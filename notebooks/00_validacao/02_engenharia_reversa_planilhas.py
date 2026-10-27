"""Fase 0: engenharia reversa das planilhas (R1, R2, H4) e validação das réplicas em Python.

Saídas versionadas (configuração, sem dado de cliente): specs/calculadora_familias.csv, specs/calculadora_compartimentos.csv.
Saídas com dado de cliente: <dados>/planilhas/*.parquet|json (fora do git).
No Fabric: suba as 3 .xlsx para Files/als_oilmodel/planilhas e defina ALS_PASTA_PLANILHAS para essa pasta.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2] if "__file__" in globals() else Path.cwd()
sys.path.insert(0, str(RAIZ))

import pandas as pd  # noqa: E402

from src.features.calculadora import ler_calculadora  # noqa: E402
from src.features.regras import ParametrosRecorrencia, status_real  # noqa: E402
from src.models.baselines import ler_forecast27, regra_forecast27  # noqa: E402
from src.pipeline.fabric import pasta_dados, salvar_json  # noqa: E402

PLANILHAS = Path(os.environ.get("ALS_PASTA_PLANILHAS", RAIZ))
CALC = PLANILHAS / "Calculadora de amostras v8 - horimetros preventiva - out.2022.xlsx"
F27 = PLANILHAS / "Forecast 27.xlsx"
CS = PLANILHAS / "Customer Status Novo_Geral_Novas Carteiras 2026.xlsx"
SAIDA = pasta_dados(RAIZ) / "planilhas"
SPECS = RAIZ / "specs"
MESES_CS = ["AGO", "SET", "OUT", "NOV", "DEZ", "JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL"]
REF_STATUS = pd.Timestamp("2026-08-10")  # data de referência que maximiza a concordância do Real Status


def calculadora() -> dict:
    blocos, comps = ler_calculadora(CALC)
    if SPECS.exists():
        blocos.to_csv(SPECS / "calculadora_familias.csv", index=False, encoding="utf-8")
        comps.to_csv(SPECS / "calculadora_compartimentos.csv", index=False, encoding="utf-8")
    return {
        "blocos": len(blocos),
        "familias_distintas": int(blocos["familia"].nunique()),
        "familias_por_setor": blocos.groupby("setor")["familia"].nunique().to_dict(),
        "blocos_reproduzidos": int(blocos["reproduz"].sum()),
        "blocos_divergentes": blocos.loc[~blocos["reproduz"], ["setor", "familia", "variante",
                                         "amostras_ano_planilha", "amostras_ano_python"]].to_dict("records"),
    }


def forecast27() -> dict:
    r = regra_forecast27(ler_forecast27(F27))
    r["dif_total_ajustado"] = (r["total_ajustado"] - r["total_ajustado_planilha"]).round(2)
    return {"meses": r["mes"].tolist(), "dif_total_ajustado": r["dif_total_ajustado"].tolist(),
            "meses_reproduzidos": int((r["dif_total_ajustado"] == 0).sum())}


def customer_status() -> dict:
    p = ParametrosRecorrencia()
    df = pd.read_excel(CS, sheet_name="data CLIENTES", header=9)
    df = df[df["ERP ID"].notna()].copy()
    vendas = pd.to_datetime(df["Last Date Sales"], errors="coerce")
    meses_compra = (df[MESES_CS].fillna(0) > p.limiar_valor).sum(axis=1)
    dias = (REF_STATUS - vendas).dt.days
    so6 = meses_compra >= p.min_meses
    pred = status_real(vendas, pd.to_datetime(df["Last Date Sample"], errors="coerce"), REF_STATUS)
    pot = pd.to_numeric(df["Annual Sample Potential"], errors="coerce")
    SAIDA.mkdir(parents=True, exist_ok=True)
    out = df.assign(status_python=pred, meses_compra_12m=meses_compra)
    texto = out.select_dtypes("object").columns
    out[texto] = out[texto].astype("string")
    out.to_parquet(SAIDA / "customer_status.parquet", index=False)
    return {
        "clientes": len(df),
        "status_planilha": df["Real Status"].value_counts().to_dict(),
        "status_concordancia": round(float((pred == df["Real Status"]).mean()), 4),
        "recorrentes_so_6_meses": int(so6.sum()),
        "recorrentes_6_meses_E_90_dias": int((so6 & (dias <= p.dias_recencia)).sum()),
        "recorrentes_6_meses_OU_90_dias": int((so6 | (dias <= p.dias_recencia)).sum()),
        "potencial_preenchido": int(pot.notna().sum()),
        "potencial_por_segmento": df.assign(pot=pot).groupby("Segment")["pot"].count().sort_values(ascending=False)
        .head(10).to_dict(),
        "erp_id_formatos": df["ERP ID"].astype(str).str.replace(r"\d", "9", regex=True).value_counts().head(5).to_dict(),
    }


def main() -> None:
    res = {"calculadora": calculadora(), "forecast27": forecast27(), "customer_status": customer_status()}
    salvar_json(res, SAIDA / "engenharia_reversa.json")
    c, f, s = res["calculadora"], res["forecast27"], res["customer_status"]
    print(f"Calculadora: {c['blocos_reproduzidos']}/{c['blocos']} blocos reproduzidos; {c['familias_distintas']} famílias")
    print(f"Forecast 27: {f['meses_reproduzidos']}/{len(f['meses'])} meses reproduzidos; diferenças {f['dif_total_ajustado']}")
    print(f"Customer Status: concordância do status {s['status_concordancia']:.1%}; recorrentes só≥6={s['recorrentes_so_6_meses']}"
          f" E={s['recorrentes_6_meses_E_90_dias']} OU={s['recorrentes_6_meses_OU_90_dias']}")


if __name__ == "__main__":
    main()
