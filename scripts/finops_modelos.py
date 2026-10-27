"""T22 (FinOps): tempo e proxy de CU por modelo candidato do KPI 1 e por execução completa do pipeline.

Proxy de CU: tempo de parede × núcleos usados (todos os modelos rodam com 1 núcleo) → núcleo-segundos; CU-s = núcleo-s / 2
(1 CU = 2 vCores no Spark do Fabric; premissa a confirmar na métrica de capacidade). Não consulta o Fabric: lê só
<dados>/base/base_cliente_mes.parquet (somente leitura) e grava <dados>/finops/*.json.

Cada modelo roda num recorte determinístico de `ALS_FINOPS_AMOSTRA` séries (hash do id) e o custo é extrapolado linearmente
para o universo completo (válido para modelos por série; o ML global é medido em duas amostras para checar a escala).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1] if "__file__" in globals() else Path.cwd()
sys.path.insert(0, str(RAIZ))

import pandas as pd  # noqa: E402

from src.backtest.comparacao import avaliar_g3, tabela_comparativa  # noqa: E402
from src.backtest.harness import resumir, rolling_origin  # noqa: E402
from src.features.regras import completar_meses  # noqa: E402
from src.gates.checks import avaliar_g1  # noqa: E402
from src.models.baselines import ingenuo_sazonal, media_movel  # noqa: E402
from src.models.estatisticos import MODELOS as ESTAT  # noqa: E402
from src.models.ml_global import ml_global  # noqa: E402
from src.pipeline.fabric import pasta_dados, salvar_json  # noqa: E402

DADOS = pasta_dados(RAIZ)
H = int(os.environ.get("ALS_HORIZONTE", "3"))
N_ORIGENS = int(os.environ.get("ALS_N_ORIGENS", "3"))
AMOSTRA = int(os.environ.get("ALS_FINOPS_AMOSTRA", "400"))
NUCLEOS = 1
MODELOS = {
    "ingenuo_sazonal": ingenuo_sazonal,
    "media_movel_3": lambda t, h: media_movel(t, h, k=3),
    "media_movel_12": lambda t, h: media_movel(t, h, k=12),
    **ESTAT,
    "ml_global": ml_global,
}


def carregar() -> pd.DataFrame:
    cli = pd.read_parquet(DADOS / "base" / "base_cliente_mes.parquet")
    ate = cli["periodo"].max()
    cli = cli[(cli["periodo"] >= "2015-01-01") & cli["entidade"].notna()]
    ativos = cli[cli["periodo"] > ate - pd.DateOffset(months=12)].groupby("entidade")["amostras"].sum()
    cli = cli[cli["entidade"].isin(ativos[ativos > 0].index)]
    base = completar_meses(cli.rename(columns={"entidade": "id", "amostras": "y"})[["id", "periodo", "y"]],
                           chave="id", valor="y", ate=ate)
    return base


def recorte(base: pd.DataFrame, n: int) -> pd.DataFrame:
    h = base["id"].map(lambda s: int(hashlib.md5(str(s).encode()).hexdigest(), 16))
    ids = base.assign(h=h).drop_duplicates("id").sort_values("h")["id"].head(n)
    return base[base["id"].isin(ids)]


def medir(nome: str, modelo, base: pd.DataFrame, origens) -> dict:
    t0, c0 = time.perf_counter(), time.process_time()
    prev = rolling_origin(base, {nome: modelo}, origens, h=H)
    t, c = time.perf_counter() - t0, time.process_time() - c0
    m = resumir(prev, ["modelo"]).iloc[0]
    cob = float(m["cobertura"]) if "cobertura" in m and pd.notna(m["cobertura"]) else None
    return {"modelo": nome, "series": int(base["id"].nunique()), "origens": len(origens), "tempo_s": t,
            "cpu_s": c, "wape": float(m["wape"]), "bias_pct": float(m["bias_pct"]), "cobertura": cob}


def main() -> None:
    inicio = time.perf_counter()
    t0 = time.perf_counter()
    base = carregar()
    t_carga = time.perf_counter() - t0
    n_total = base["id"].nunique()
    t0 = time.perf_counter()
    avaliar_g1(base, ["id", "periodo"], "y")
    t_g1 = time.perf_counter() - t0
    origens = pd.date_range(end=base["periodo"].max() - pd.DateOffset(months=H), periods=N_ORIGENS, freq="MS")
    amostra = recorte(base, AMOSTRA)

    linhas = []
    for nome, f in MODELOS.items():
        r = medir(nome, f, amostra, origens)
        r["s_por_serie_origem"] = r["tempo_s"] / (r["series"] * r["origens"])
        r["tempo_universo_origem_s"] = r["s_por_serie_origem"] * n_total
        linhas.append(r)
        print(f"{nome}: {r['tempo_s']:.1f}s wape={r['wape']:.3f}", flush=True)
    # ML global: checa escala com o dobro de séries
    r2 = medir("ml_global", ml_global, recorte(base, 2 * AMOSTRA), origens)
    r2["s_por_serie_origem"] = r2["tempo_s"] / (r2["series"] * r2["origens"])
    r2["tempo_universo_origem_s"] = r2["s_por_serie_origem"] * n_total
    linhas.append(r2)
    print(f"ml_global x2: {r2['tempo_s']:.1f}s wape={r2['wape']:.3f}", flush=True)

    # execução completa (recorte): carga + G1 + backtest de todos os modelos + comparação + G3
    t0 = time.perf_counter()
    prev = rolling_origin(amostra, MODELOS, origens, h=H)
    t_back = time.perf_counter() - t0
    t0 = time.perf_counter()
    g3 = avaliar_g3(tabela_comparativa(prev.assign(nivel="cliente", segmento="TODOS")))
    t_comp = time.perf_counter() - t0
    out = {
        "universo_series": int(n_total), "amostra_series": AMOSTRA, "origens": N_ORIGENS, "horizonte": H,
        "nucleos": NUCLEOS, "cpu_logicas": os.cpu_count(), "python": sys.version.split()[0],
        "etapas_s": {"carga_e_grade": t_carga, "g1": t_g1, "backtest_recorte_todos_modelos": t_back,
                     "comparacao_g3": t_comp},
        "modelos": linhas, "total_script_s": time.perf_counter() - inicio, "g3_linhas": int(len(g3)),
    }
    salvar_json(out, DADOS / "finops" / "custos.json")
    print(json.dumps({k: v for k, v in out.items() if k != "modelos"}, indent=1, default=str))


if __name__ == "__main__":
    main()
