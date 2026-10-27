"""T18: oportunidades Zoho >80% somadas ao forecast de faturamento × descontadas (dupla contagem), no histórico.

Entrada: <dados>/base/ (T14) + deals em nível de negócio (silver_zoho.deals, só SELECT), em cache em <dados>/kpi2/bruto/.
Para cada corte mensal e horizonte 1..3, prevê o faturamento total do mês-alvo com o Forecast 27 calculado dos dados
(src/features/receita.py) e as quatro variantes de src/features/crosscheck.py; compara com o faturamento realizado.
Limitação: o Zoho só guarda o estado atual do negócio; a "probabilidade no corte" é a final, e "vivo no corte" usa
data_criacao e data_fechamento_real. Sensibilidades: limiar ≥ 80, valor rateado pelo prazo do contrato.
Saída: <dados>/kpi2/crosscheck_previsoes.parquet e crosscheck.json.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2] if "__file__" in globals() else Path.cwd()
sys.path.insert(0, str(RAIZ))

import pandas as pd  # noqa: E402

from src.features.base import mapa_zoho  # noqa: E402
from src.features.crosscheck import metricas, previsoes_corte, risco_dupla_contagem  # noqa: E402
from src.pipeline.fabric import Fabric, pasta_dados, salvar_json  # noqa: E402

DADOS = pasta_dados(RAIZ)
SAIDA = DADOS / "kpi2"
H = 3
SQL_DEALS = """
    SELECT d.zoho_id, d.conta_id, d.estagio, d.probabilidade, d.valor, d.prazo_meses, d.data_criacao,
           d.data_fechamento_prevista, d.data_fechamento_real
    FROM silver_zoho.deals d"""
CENARIOS = {"principal": dict(limiar=80, estrito=True, ratear=False),
            "limiar_ge80": dict(limiar=80, estrito=False, ratear=False),
            "rateado_prazo": dict(limiar=80, estrito=True, ratear=True)}


def carregar_deals() -> pd.DataFrame:
    cache = SAIDA / "bruto" / "deals_nivel_negocio.parquet"
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        with Fabric() as fb:
            fb.query(SQL_DEALS).to_parquet(cache, index=False)
    return pd.read_parquet(cache)


def fat_ganhas(deals: pd.DataFrame, fat: pd.DataFrame) -> pd.DataFrame:
    """Negócios ganhos com probabilidade > 80 e o faturamento da entidade no mês do fechamento real."""
    g = deals[(deals["estagio"] == "Closed Won") & (pd.to_numeric(deals["probabilidade"], errors="coerce") > 80)
              & deals["entidade"].notna() & deals["data_fechamento_real"].notna()].copy()
    g["periodo"] = pd.to_datetime(g["data_fechamento_real"]).dt.to_period("M").dt.to_timestamp()
    g = g[g["periodo"] >= fat["periodo"].min()]
    f = fat.groupby(["entidade", "periodo"], as_index=False)["faturamento"].sum()
    g = g.merge(f, on=["entidade", "periodo"], how="left").fillna({"faturamento": 0.0})
    return g.rename(columns={"valor": "valor_oportunidade", "faturamento": "faturamento_mes_fechamento"})


def main() -> None:
    base = pd.read_parquet(DADOS / "base" / "base_cliente_mes.parquet")
    z = mapa_zoho(pd.read_parquet(DADOS / "base" / "bruto" / "zoho.parquet"))
    deals = carregar_deals().merge(z[["zoho_id", "entidade"]].rename(columns={"zoho_id": "conta_id"}),
                                   on="conta_id", how="left")
    fat = base[base["faturamento"].notna()]
    mensal = fat.loc[fat["faturamento"] > 0, ["entidade", "periodo", "faturamento"]] \
        .rename(columns={"entidade": "cliente", "faturamento": "valor"})
    real = fat.groupby("periodo")["faturamento"].sum()
    ini, fim = fat["periodo"].min(), fat["periodo"].max()
    cortes = pd.date_range(ini + pd.DateOffset(months=11), fim - pd.DateOffset(months=1), freq="MS")
    rel: dict = {"cortes": [str(c.date()) for c in cortes], "horizonte_max": H, "meses_alvo_ate": str(fim.date())}
    ganhas = fat_ganhas(deals, fat)
    partes = []
    for c in cortes:  # o Forecast 27 de cada corte é calculado uma vez e serve aos três cenários
        h = min(H, (fim.year - c.year) * 12 + fim.month - c.month)
        partes.append(previsoes_corte(mensal, deals, c + pd.offsets.MonthEnd(0), h, cenarios=CENARIOS))
        print(f"corte {c.date()} ok", flush=True)
    todas = pd.concat(partes, ignore_index=True)
    SAIDA.mkdir(parents=True, exist_ok=True)
    todas.to_parquet(SAIDA / "crosscheck_previsoes.parquet", index=False)
    for nome in CENARIOS:
        prev = todas[todas["cenario"] == nome]
        met = metricas(prev, real)
        rel[nome] = {"metricas": met.to_dict("records"), "dupla_contagem": risco_dupla_contagem(prev, ganhas)}
        print(f"== {nome}\n{met.round(4).to_string(index=False)}\n{rel[nome]['dupla_contagem']}", flush=True)
    salvar_json(rel, SAIDA / "crosscheck.json")


if __name__ == "__main__":
    main()
