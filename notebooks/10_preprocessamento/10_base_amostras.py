"""T14: tabela-base por entidade × mês (amostras, faturamento, oportunidades), validada pelo G1.

Somente leitura no LakehouseOel: o SQL agrega no endpoint (a amostra tem ~8,7 mi de linhas) e a limpeza,
a ponte de clientes e a grade mensal rodam em pandas (`src/features/base.py`).
Local: `python notebooks/10_preprocessamento/10_base_amostras.py` a partir da raiz.
No Fabric: anexar o LakehouseOel como lakehouse padrão do notebook.
Saídas em <dados>/base/ (data/ local, fora do git; Files/als_oilmodel/ no Fabric):
  base_cliente_mes.parquet   entidade × mês contínuo até o último mês completo (G1)
  base_equipamento_mes.parquet  equipamento × mês com coleta (esparsa; sem avulsas)
  mapa_s360.parquet, mapa_protheus.parquet  ponte de clientes e a regra usada
  relatorio.json             descartes, cobertura de join e gates G1
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2] if "__file__" in globals() else Path.cwd()
sys.path.insert(0, str(RAIZ))

import pandas as pd  # noqa: E402

from src.features.base import (ParametrosBase, cobertura_ponderada, faturamento_mensal, limpar_amostras,  # noqa: E402
                               mapa_zoho, mapear_protheus, mapear_s360, montar_base, oportunidades_mensal)
from src.features.regras import inicio_mes  # noqa: E402
from src.gates.checks import avaliar_g1, avaliar_g1_limpo, cobertura_join  # noqa: E402
from src.pipeline.fabric import Fabric, pasta_dados, salvar_json  # noqa: E402

SAIDA = pasta_dados(RAIZ) / "base"
P = ParametrosBase()
HOJE = pd.Timestamp.now().normalize()
ATE = inicio_mes(HOJE) - pd.DateOffset(months=1)       # último mês completo
LIMITE = (HOJE + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

NAO_EXCLUIDA = "COALESCE(CAST(a.excluido AS INT), 0) = 0"
PLAUSIVEL = "{c} >= '" + P.data_min + "' AND {c} < '" + LIMITE + "'"
# data da amostra: coleta; se ausente ou implausível, entrada no laboratório. Sem nenhuma das duas = não consumida.
DATA = (f"CASE WHEN {PLAUSIVEL.format(c='a.data_coleta')} THEN a.data_coleta "
        f"WHEN {PLAUSIVEL.format(c='a.data_entrada_laboratorio')} THEN a.data_entrada_laboratorio END")
STATUS_DATA = (f"CASE WHEN {PLAUSIVEL.format(c='a.data_coleta')} THEN 'coleta' "
               f"WHEN {PLAUSIVEL.format(c='a.data_entrada_laboratorio')} THEN 'entrada' "
               "WHEN a.data_coleta IS NULL AND a.data_entrada_laboratorio IS NULL THEN 'sem_data' "
               "ELSE 'fora_intervalo' END")
# D9: avulsa = sem compartimento, ou compartimento/equipamento inexistente no cadastro
AVULSA = "CASE WHEN e.id IS NULL THEN 1 ELSE 0 END"
JOIN_EQUIP = """LEFT JOIN bronze_s360.compartimento c ON c.id = a.compartimento_id
        LEFT JOIN bronze_s360.equipamento e ON e.id = c.equipamento_id"""

SQL = {
    "excluidas": f"SELECT COUNT(*) AS n FROM bronze_s360.amostra a WHERE NOT ({NAO_EXCLUIDA})",
    "amostras": f"""
        SELECT a.cliente_id, YEAR({DATA}) AS ano, MONTH({DATA}) AS mes, {STATUS_DATA} AS status_data,
               {AVULSA} AS avulsa, COUNT(*) AS n, COUNT(DISTINCT a.id) AS n_ids
        FROM bronze_s360.amostra a {JOIN_EQUIP}
        WHERE {NAO_EXCLUIDA}
        GROUP BY a.cliente_id, YEAR({DATA}), MONTH({DATA}), {STATUS_DATA}, {AVULSA}""",
    "equipamentos": f"""
        SELECT e.id AS equipamento_id, a.cliente_id, YEAR({DATA}) AS ano, MONTH({DATA}) AS mes,
               COUNT(DISTINCT a.id) AS amostras, COUNT(DISTINCT a.compartimento_id) AS compartimentos
        FROM bronze_s360.amostra a {JOIN_EQUIP}
        WHERE {NAO_EXCLUIDA} AND e.id IS NOT NULL AND ({DATA}) IS NOT NULL
        GROUP BY e.id, a.cliente_id, YEAR({DATA}), MONTH({DATA})""",
    "clientes": """
        SELECT c.id AS cliente_id, TRIM(c.id_cigam) AS id_cigam, TRIM(c.codigo_legado) AS codigo_legado,
               CAST(c.ativo AS INT) AS ativo
        FROM bronze_s360.cliente c""",
    "zoho": "SELECT z.zoho_id, z.cnpj, z.erp_id, z.conta, z.razao_social, z.segmento FROM silver_zoho.accounts z",
    "nomes_protheus": """
        SELECT TRIM(r.cliente) AS cod_cliente, MAX(r.nome_cliente) AS nome_cliente
        FROM silver_protheus.contasreceber r WHERE r.nome_cliente IS NOT NULL GROUP BY TRIM(r.cliente)""",
    "faturamento": """
        SELECT TRIM(n.cod_cliente) AS cod_cliente, TRIM(n.cfop) AS cfop, YEAR(n.emissao) AS ano,
               MONTH(n.emissao) AS mes, COUNT(*) AS itens, SUM(n.total) AS total
        FROM silver_protheus.notassaida n WHERE n.emissao IS NOT NULL
        GROUP BY TRIM(n.cod_cliente), TRIM(n.cfop), YEAR(n.emissao), MONTH(n.emissao)""",
    "deals": f"""
        SELECT d.conta_id, d.estagio,
               YEAR(CASE WHEN d.estagio IN ('{P.estagio_ganho}', '{P.estagio_perdido}')
                    THEN COALESCE(d.data_fechamento_real, d.data_fechamento_prevista)
                    ELSE d.data_fechamento_prevista END) AS ano,
               MONTH(CASE WHEN d.estagio IN ('{P.estagio_ganho}', '{P.estagio_perdido}')
                    THEN COALESCE(d.data_fechamento_real, d.data_fechamento_prevista)
                    ELSE d.data_fechamento_prevista END) AS mes,
               COUNT(*) AS n, SUM(d.valor) AS valor,
               SUM(d.valor * COALESCE(d.probabilidade, 0) / 100.0) AS valor_ponderado
        FROM silver_zoho.deals d
        GROUP BY d.conta_id, d.estagio,
               YEAR(CASE WHEN d.estagio IN ('{P.estagio_ganho}', '{P.estagio_perdido}')
                    THEN COALESCE(d.data_fechamento_real, d.data_fechamento_prevista)
                    ELSE d.data_fechamento_prevista END),
               MONTH(CASE WHEN d.estagio IN ('{P.estagio_ganho}', '{P.estagio_perdido}')
                    THEN COALESCE(d.data_fechamento_real, d.data_fechamento_prevista)
                    ELSE d.data_fechamento_prevista END)""",
}


def extrair(cache: Path) -> dict[str, pd.DataFrame]:
    """Roda as consultas (somente SELECT) e guarda cada resultado em <dados>/base/bruto/ para reprocessar sem o Fabric."""
    cache.mkdir(parents=True, exist_ok=True)
    falta = [k for k in SQL if not (cache / f"{k}.parquet").exists()]
    if falta:
        with Fabric() as fb:
            for k in falta:
                print(f"consulta {k} ...", flush=True)
                fb.query(SQL[k]).to_parquet(cache / f"{k}.parquet", index=False)
    return {k: pd.read_parquet(cache / f"{k}.parquet") for k in SQL}


def main() -> None:
    d = extrair(SAIDA / "bruto")
    rel: dict = {"gerado_em": datetime.now().isoformat(), "ate": str(ATE.date()), "parametros": P.__dict__}

    # ponte de clientes
    clientes = d["clientes"].assign(cliente_id=lambda x: x["cliente_id"].astype("int64"))
    z = mapa_zoho(d["zoho"])
    m_s360 = mapear_s360(clientes, z)
    nomes = d["nomes_protheus"].set_index("cod_cliente")["nome_cliente"]
    m_prot = mapear_protheus(d["faturamento"]["cod_cliente"], z, clientes, m_s360, nomes)

    # amostras
    amostras, descarte = limpar_amostras(d["amostras"], ATE, set(clientes["cliente_id"]))
    descarte["excluidas"] = int(d["excluidas"]["n"].iloc[0])
    descarte["total_bruto"] = int(d["amostras"]["n"].sum()) + descarte["excluidas"]
    rel["amostras"] = descarte
    amostras = amostras.merge(m_s360[["cliente_id", "entidade"]], on="cliente_id", how="left")

    # faturamento e oportunidades
    fat, info_fat = faturamento_mensal(d["faturamento"], P)
    fat = fat[fat["periodo"] <= ATE].merge(m_prot[["cod_cliente", "entidade"]], on="cod_cliente", how="left")
    rel["faturamento"] = info_fat
    opp = oportunidades_mensal(d["deals"].dropna(subset=["ano", "mes"]), P)
    opp = opp[opp["periodo"] <= ATE].merge(z[["zoho_id", "entidade"]].rename(columns={"zoho_id": "conta_id"}),
                                           on="conta_id", how="left")
    rel["oportunidades"] = {"sem_conta": int(opp["entidade"].isna().sum())}
    opp = opp.dropna(subset=["entidade"])

    # atributos: segmento Zoho (moda por entidade)
    seg = z.dropna(subset=["segmento"]).groupby("entidade")["segmento"].agg(lambda s: s.value_counts().idxmax())
    base = montar_base(amostras.drop(columns="cliente_id"), fat.drop(columns="cod_cliente"),
                       opp.drop(columns="conta_id"), ATE, seg.rename("segmento").reset_index())

    # equipamento × mês (esparsa): entidade do cliente que mais coletou
    eq = d["equipamentos"].dropna(subset=["ano", "mes"]).copy()
    eq["periodo"] = pd.to_datetime(dict(year=eq["ano"].astype(int), month=eq["mes"].astype(int), day=1))
    eq = eq[(eq["periodo"] <= ATE) & eq["cliente_id"].isin(set(clientes["cliente_id"]))]
    eq = eq.merge(m_s360[["cliente_id", "entidade"]], on="cliente_id", how="left")
    dono = eq.groupby(["equipamento_id", "entidade"])["amostras"].sum().reset_index() \
        .sort_values("amostras", ascending=False).drop_duplicates("equipamento_id")
    rel["equipamentos"] = {"equipamentos": int(eq["equipamento_id"].nunique()),
                           "com_mais_de_uma_entidade": int((eq.groupby("equipamento_id")["entidade"].nunique() > 1).sum())}
    eq = (eq.groupby(["equipamento_id", "periodo"], as_index=False)[["amostras", "compartimentos"]].sum()
          .merge(dono[["equipamento_id", "entidade"]], on="equipamento_id"))

    # cobertura de join (ponderada pelo volume que cada chave carrega)
    am_cli = d["amostras"].assign(n=d["amostras"]["n_ids"].astype(int))
    fat_cod, _ = faturamento_mensal(d["faturamento"], P)
    rel["cobertura"] = {
        "s360_para_zoho_por_amostras": cobertura_ponderada(m_s360, am_cli, "cliente_id", "n"),
        "protheus_para_entidade_por_faturamento": cobertura_ponderada(m_prot, fat_cod, "cod_cliente", "faturamento"),
        "s360_regras": m_s360["regra"].value_counts().to_dict(),
        "protheus_regras": m_prot["regra"].value_counts().to_dict(),
        "zoho_contas_com_raiz": int(z["raiz"].notna().sum()), "zoho_contas": int(len(z)),
        "entidades_com_amostras_e_faturamento": int(base.groupby("entidade")[["tem_amostras", "tem_faturamento"]]
                                                    .first().all(axis=1).sum()),
    }

    # gates G1
    ini_fat = base.loc[base["faturamento"].notna(), "periodo"].min()
    ini_opp = base.loc[base["oport_abertas_n"].notna(), "periodo"].min()
    chave = ["entidade", "periodo"]
    gates = (avaliar_g1(base, chave, "amostras")
             + avaliar_g1(base[base["periodo"] >= ini_fat], chave, "faturamento")
             + avaliar_g1(base[base["periodo"] >= ini_opp], chave, "oport_ganhas_valor")
             + avaliar_g1_limpo(m_s360, ["cliente_id", "entidade"], ["cliente_id"], [])
             + avaliar_g1_limpo(m_prot, ["cod_cliente", "entidade"], ["cod_cliente"], [])
             + avaliar_g1_limpo(eq, ["equipamento_id", "entidade"], ["equipamento_id", "periodo"], ["periodo"], hoje=HOJE)
             + cobertura_join(am_cli, m_s360[m_s360["regra"].ne("sem_ponte")], "cliente_id", 90.0, "s360→ponte (linhas)")
             + cobertura_join(d["faturamento"].assign(cod_cliente=lambda x: x["cod_cliente"].str.upper()),
                              m_prot[m_prot["regra"].ne("sem_ponte")], "cod_cliente", 90.0, "protheus→ponte (linhas)"))
    rel["gates_g1"] = gates
    rel["base"] = {"linhas": int(len(base)), "entidades": int(base["entidade"].nunique()),
                   "periodo": [str(base["periodo"].min().date()), str(base["periodo"].max().date())],
                   "inicio_faturamento": str(ini_fat.date()), "inicio_oportunidades": str(ini_opp.date()),
                   "amostras": int(base["amostras"].sum()), "faturamento": round(float(base["faturamento"].sum()), 2),
                   "equipamento_linhas": int(len(eq))}

    base.to_parquet(SAIDA / "base_cliente_mes.parquet", index=False)
    eq.to_parquet(SAIDA / "base_equipamento_mes.parquet", index=False)
    m_s360.to_parquet(SAIDA / "mapa_s360.parquet", index=False)
    m_prot.to_parquet(SAIDA / "mapa_protheus.parquet", index=False)
    salvar_json(rel, SAIDA / "relatorio.json")

    falhas = [g for g in gates if not g["ok"]]
    print(f"base: {rel['base']}")
    print(f"amostras: {descarte}")
    print(f"cobertura: {rel['cobertura']}")
    print(f"G1 {len(gates) - len(falhas)}/{len(gates)} checagens aprovadas.")
    for g in falhas:
        print(f"  G1 FALHA {g['checagem']} {g['alvo']}: {g['detalhe']}")


if __name__ == "__main__":
    main()
