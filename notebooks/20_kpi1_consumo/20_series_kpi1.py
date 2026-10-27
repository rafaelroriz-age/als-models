"""T15 (1/2): séries mensais do KPI 1 (amostras consumidas, sem avulsas) por nível: cliente, equipamento, compartimento.

Entrada: <dados>/base/ da T14 (base_cliente_mes, base_equipamento_mes, mapa_s360). O nível compartimento não está na
tabela-base: vem do LakehouseOel (somente leitura), agregado no SQL endpoint e guardado em cache em <dados>/kpi1/bruto/.
Equipamento e compartimento usam uma amostra determinística (equipamento_id % ALS_AMOSTRA_MOD == 0, mesma amostra
nos dois níveis); o cliente usa todas as entidades.
Saída: <dados>/kpi1/series_{cliente,equipamento,compartimento}.parquet com [id, periodo, y, segmento].
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2] if "__file__" in globals() else Path.cwd()
sys.path.insert(0, str(RAIZ))

import pandas as pd  # noqa: E402

from src.backtest.comparacao import rotular_segmento  # noqa: E402
from src.features.regras import completar_meses  # noqa: E402
from src.gates.checks import avaliar_g1  # noqa: E402
from src.pipeline.fabric import Fabric, pasta_dados, salvar_json  # noqa: E402

DADOS = pasta_dados(RAIZ)
SAIDA = DADOS / "kpi1"
MOD = int(os.environ.get("ALS_AMOSTRA_MOD", "100"))

# mesmas regras de data e de exclusão de notebooks/10_preprocessamento/10_base_amostras.py (T14, D9)
NAO_EXCLUIDA = "COALESCE(CAST(a.excluido AS INT), 0) = 0"
DATA = ("CASE WHEN a.data_coleta >= '2010-01-01' AND a.data_coleta < '{lim}' THEN a.data_coleta "
        "WHEN a.data_entrada_laboratorio >= '2010-01-01' AND a.data_entrada_laboratorio < '{lim}' "
        "THEN a.data_entrada_laboratorio END")
SQL_COMPARTIMENTOS = """
    SELECT c.id AS compartimento_id, e.id AS equipamento_id, a.cliente_id,
           YEAR({data}) AS ano, MONTH({data}) AS mes, COUNT(DISTINCT a.id) AS amostras
    FROM bronze_s360.amostra a
    JOIN bronze_s360.compartimento c ON c.id = a.compartimento_id
    JOIN bronze_s360.equipamento e ON e.id = c.equipamento_id
    WHERE {nao_excluida} AND e.id % {mod} = 0 AND ({data}) IS NOT NULL
    GROUP BY c.id, e.id, a.cliente_id, YEAR({data}), MONTH({data})"""


def _grade(df: pd.DataFrame, ate: pd.Timestamp, seg: pd.Series) -> pd.DataFrame:
    """[id, periodo, y] esparso → mês a mês contínuo até `ate`, com o segmento da entidade dona."""
    dono = df.groupby("id")["entidade"].agg(lambda s: s.mode().iat[0] if s.notna().any() else pd.NA)
    base = completar_meses(df[["id", "periodo", "y"]], chave="id", valor="y", ate=ate)
    base["segmento"] = rotular_segmento(base["id"].map(dono).map(seg))
    return base


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    cli = pd.read_parquet(DADOS / "base" / "base_cliente_mes.parquet")
    ate = cli["periodo"].max()
    seg = cli.dropna(subset=["segmento"]).drop_duplicates("entidade").set_index("entidade")["segmento"]
    mapa = pd.read_parquet(DADOS / "base" / "mapa_s360.parquet").set_index("cliente_id")["entidade"]

    series = {"cliente": cli.rename(columns={"entidade": "id", "amostras": "y"})
              .assign(segmento=lambda x: rotular_segmento(x["segmento"]))[["id", "periodo", "y", "segmento"]]}

    eq = pd.read_parquet(DADOS / "base" / "base_equipamento_mes.parquet")
    eq = eq[eq["equipamento_id"] % MOD == 0]
    series["equipamento"] = _grade(eq.assign(id=eq["equipamento_id"].astype(str), y=eq["amostras"].astype(float)),
                                   ate, seg)

    cache = SAIDA / "bruto" / f"compartimentos_mod{MOD}.parquet"
    if not cache.exists():
        lim = (pd.Timestamp.now().normalize() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        sql = SQL_COMPARTIMENTOS.format(data=DATA.format(lim=lim), nao_excluida=NAO_EXCLUIDA, mod=MOD)
        cache.parent.mkdir(parents=True, exist_ok=True)
        with Fabric() as fb:
            fb.query(sql).to_parquet(cache, index=False)
    co = pd.read_parquet(cache).dropna(subset=["ano", "mes"])
    co["periodo"] = pd.to_datetime(dict(year=co["ano"].astype(int), month=co["mes"].astype(int), day=1))
    co = co[co["periodo"] <= ate]
    series["compartimento"] = _grade(co.assign(id=co["compartimento_id"].astype(str), y=co["amostras"].astype(float),
                                               entidade=co["cliente_id"].map(mapa)), ate, seg)

    rel = {"ate": ate, "amostra_mod": MOD, "niveis": {}, "gates_g1": []}
    for nivel, s in series.items():
        s.to_parquet(SAIDA / f"series_{nivel}.parquet", index=False)
        rel["gates_g1"] += avaliar_g1(s, ["id", "periodo"], "y")
        rel["niveis"][nivel] = {"series": int(s["id"].nunique()), "linhas": int(len(s)), "amostras": float(s["y"].sum()),
                                "sem_segmento_pct": round(100 * float((s["segmento"] == "sem_segmento").mean()), 1)}
        print(nivel, rel["niveis"][nivel])
    salvar_json(rel, SAIDA / "series_relatorio.json")


if __name__ == "__main__":
    main()
