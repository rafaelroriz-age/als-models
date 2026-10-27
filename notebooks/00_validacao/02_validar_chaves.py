"""T03: taxa de casamento das chaves entre S360, Protheus e Zoho (somente leitura; saída = agregados).

Local: `python notebooks/00_validacao/02_validar_chaves.py` a partir da raiz. Saída: <dados>/chaves/chaves.json.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2] if "__file__" in globals() else Path.cwd()
sys.path.insert(0, str(RAIZ))

import pandas as pd  # noqa: E402

from src.pipeline.chaves import chave_erp, chave_grupo, raiz_cnpj, taxa_casamento  # noqa: E402
from src.pipeline.fabric import Fabric, pasta_dados, salvar_json  # noqa: E402

SAIDA = pasta_dados(RAIZ) / "chaves"
NAO_EXC = "COALESCE(CAST(a.excluido AS INT), 0) = 0"


def escalar(fb, sql):
    return fb.query(sql).iloc[0].to_dict()


def main():
    out = {}
    with Fabric() as fb:
        cli = fb.query("SELECT id, codigo_legado, id_cigam, sam_id FROM bronze_s360.cliente")
        for c in ("codigo_legado", "id_cigam"):
            cli[c + "_n"] = cli[c].map(chave_erp)
        acc = fb.query("SELECT zoho_id, cnpj, erp_id, razao_social FROM silver_zoho.accounts")
        acc["erp_n"] = acc["erp_id"].map(chave_erp)
        acc["raiz"] = acc["cnpj"].map(raiz_cnpj)
        nf = fb.query("""SELECT cod_cliente, COUNT(*) AS n_linhas, SUM(total) AS total,
                                MIN(emissao) AS ini, MAX(emissao) AS fim
                         FROM silver_protheus.notassaida GROUP BY cod_cliente""")
        nf["k"] = nf["cod_cliente"].map(chave_erp)
        nf12 = fb.query("""SELECT cod_cliente, SUM(total) AS total FROM silver_protheus.notassaida
                           WHERE emissao >= '2025-10-01' GROUP BY cod_cliente""")
        nf12["k"] = nf12["cod_cliente"].map(chave_erp)
        amo = fb.query(f"""SELECT a.cliente_id, COUNT(*) AS n FROM bronze_s360.amostra a
                           WHERE {NAO_EXC} AND a.data_coleta >= '2022-01-01' GROUP BY a.cliente_id""")
        ids_cli = cli["id"]
        for c in ("codigo_legado", "id_cigam"):
            cli[c + "_g"] = cli[c].map(chave_grupo)
        cli["g"] = cli["codigo_legado_g"].where(cli["codigo_legado_g"].notna(), cli["id_cigam_g"])
        acc["erp_g"] = acc["erp_id"].map(chave_grupo)
        nf["g"] = nf["cod_cliente"].map(chave_grupo)
        nf12["g"] = nf12["cod_cliente"].map(chave_grupo)
        g_keys = pd.concat([cli["codigo_legado_g"], cli["id_cigam_g"]])

        s360_keys = pd.concat([cli["codigo_legado_n"], cli["id_cigam_n"]])
        out["A_protheus_s360"] = {
            "cod_cliente_vs_codigo_legado": taxa_casamento(nf["k"], cli["codigo_legado_n"], nf["total"]),
            "cod_cliente_vs_id_cigam": taxa_casamento(nf["k"], cli["id_cigam_n"], nf["total"]),
            "cod_cliente_vs_legado_ou_cigam": taxa_casamento(nf["k"], s360_keys, nf["total"]),
            "ultimos_12m_vs_legado_ou_cigam": taxa_casamento(nf12["k"], s360_keys, nf12["total"]),
        }
        out["A_protheus_s360"]["com_regra_grupo_A+5"] = {
            "todo_periodo": taxa_casamento(nf["g"], g_keys, nf["total"]),
            "ultimos_12m": taxa_casamento(nf12["g"], g_keys, nf12["total"]),
            "so_legado": taxa_casamento(nf["g"], cli["codigo_legado_g"], nf["total"]),
            "so_cigam": taxa_casamento(nf["g"], cli["id_cigam_g"], nf["total"]),
        }
        nf_nao = nf[~nf["g"].isin(set(g_keys.dropna()))].sort_values("total", ascending=False)
        out["A_protheus_s360"]["nao_casam_top10"] = nf_nao.head(10)[["cod_cliente", "n_linhas", "total"]].to_dict("records")
        out["A_protheus_s360"]["nao_casam_grupo_prefixo"] = (
            nf_nao["k"].str[:1].value_counts().head(8).to_dict())
        out["A_protheus_s360"]["cliente_sem_codigo"] = {
            "sem_legado_nem_cigam": int((cli["codigo_legado_n"].isna() & cli["id_cigam_n"].isna()).sum()),
            "total_clientes": int(len(cli))}
        out["A_protheus_s360"]["colisao_legado_cigam"] = {
            "legado_repetido": int(cli["codigo_legado_n"].dropna().duplicated(keep=False).sum()),
            "cigam_repetido": int(cli["id_cigam_n"].dropna().duplicated(keep=False).sum()),
            "legado_difere_cigam": int((cli["codigo_legado_n"].notna() & cli["id_cigam_n"].notna()
                                        & (cli["codigo_legado_n"] != cli["id_cigam_n"])).sum())}

        # raiz CNPJ <-> ERP ID (Zoho é a única fonte com CNPJ)
        z = acc.dropna(subset=["erp_n"])
        out["B_cnpj_erp_zoho"] = {
            "contas": int(len(acc)),
            "cnpj_nulo": int(acc["cnpj"].isna().sum()),
            "cnpj_invalido_ou_zero": int((acc["cnpj"].notna() & acc["raiz"].isna()).sum()),
            "erp_nulo": int(acc["erp_n"].isna().sum()),
            "com_raiz_e_erp": int((acc["raiz"].notna() & acc["erp_n"].notna()).sum()),
            "raizes_distintas": int(acc["raiz"].nunique()),
            "raizes_com_varios_erp": int((z.groupby("raiz")["erp_n"].nunique() > 1).sum()),
            "erp_com_varias_raizes": int((z.groupby("erp_n")["raiz"].nunique() > 1).sum()),
            "erp_repetido_em_contas": int(z["erp_n"].duplicated(keep=False).sum()),
            "cnpj_completo_repetido_em_contas": int(acc["cnpj"].dropna().duplicated(keep=False).sum()),
        }
        out["B_cnpj_erp_zoho"]["erp_zoho_vs_protheus"] = taxa_casamento(acc["erp_n"], nf["k"])
        out["B_cnpj_erp_zoho"]["protheus_vs_erp_zoho"] = taxa_casamento(nf["k"], acc["erp_n"], nf["total"])
        out["B_cnpj_erp_zoho"]["grupo_erp_zoho_vs_protheus"] = taxa_casamento(acc["erp_g"], nf["g"])
        out["B_cnpj_erp_zoho"]["grupo_protheus_vs_erp_zoho"] = taxa_casamento(nf["g"], acc["erp_g"], nf["total"])
        # raiz CNPJ -> varios grupos ERP (um cliente econômico com várias contas/filiais)
        out["B_cnpj_erp_zoho"]["raizes_com_varios_grupos"] = int((acc.dropna(subset=["raiz", "erp_g"]).groupby("raiz")["erp_g"].nunique() > 1).sum())

        # Zoho conta <-> S360 cliente
        out["D_zoho_s360"] = {
            "erp_zoho_vs_legado_ou_cigam": taxa_casamento(acc["erp_n"], s360_keys),
            "s360_legado_ou_cigam_vs_erp_zoho": taxa_casamento(
                cli["codigo_legado_n"].where(cli["codigo_legado_n"].notna(), cli["id_cigam_n"]), acc["erp_n"]),
        }
        nome_s = cli.merge(fb.query("SELECT id, razao_social FROM bronze_s360.cliente"), on="id")
        rs = nome_s["razao_social"].dropna().str.upper().str.replace(r"[^A-Z0-9]", "", regex=True)
        ra = acc["razao_social"].dropna().str.upper().str.replace(r"[^A-Z0-9]", "", regex=True)
        out["D_zoho_s360"]["grupo_erp_zoho_vs_s360"] = taxa_casamento(acc["erp_g"], g_keys)
        out["D_zoho_s360"]["grupo_s360_vs_erp_zoho"] = taxa_casamento(cli["g"], acc["erp_g"])
        out["D_zoho_s360"]["razao_social_exata_zoho_em_s360"] = taxa_casamento(ra, rs)
        # contas Zoho sem casamento por ERP: casam por razão social?
        nao_erp = acc[~acc["erp_n"].isin(set(s360_keys.dropna()))]
        ra2 = nao_erp["razao_social"].dropna().str.upper().str.replace(r"[^A-Z0-9]", "", regex=True)
        out["D_zoho_s360"]["sem_casar_erp_mas_casa_razao"] = {
            "n": int(len(ra2)), "casam": int(ra2.isin(set(rs)).sum())}

        # cadeia S360
        out["C_cadeia_s360"] = {
            "amostras_cliente_id": escalar(fb, f"""
                SELECT COUNT(*) AS n, SUM(CASE WHEN a.cliente_id IS NULL THEN 1 ELSE 0 END) AS cliente_nulo,
                       SUM(CASE WHEN a.cliente_id IS NOT NULL AND c.id IS NULL THEN 1 ELSE 0 END) AS cliente_orfao
                FROM bronze_s360.amostra a LEFT JOIN bronze_s360.cliente c ON c.id = a.cliente_id
                WHERE {NAO_EXC} AND a.data_coleta >= '2022-01-01'"""),
            "amostras_compartimento": escalar(fb, f"""
                SELECT COUNT(*) AS n, SUM(CASE WHEN a.compartimento_id IS NULL THEN 1 ELSE 0 END) AS comp_nulo,
                       SUM(CASE WHEN a.compartimento_id IS NOT NULL AND k.id IS NULL THEN 1 ELSE 0 END) AS comp_orfao
                FROM bronze_s360.amostra a LEFT JOIN bronze_s360.compartimento k ON k.id = a.compartimento_id
                WHERE {NAO_EXC} AND a.data_coleta >= '2022-01-01'"""),
            "amostras_equipamento": escalar(fb, f"""
                SELECT COUNT(*) AS n,
                       SUM(CASE WHEN k.id IS NOT NULL AND k.equipamento_id IS NULL THEN 1 ELSE 0 END) AS comp_sem_equip,
                       SUM(CASE WHEN k.equipamento_id IS NOT NULL AND e.id IS NULL THEN 1 ELSE 0 END) AS equip_orfao,
                       SUM(CASE WHEN e.id IS NOT NULL THEN 1 ELSE 0 END) AS cadeia_completa
                FROM bronze_s360.amostra a
                LEFT JOIN bronze_s360.compartimento k ON k.id = a.compartimento_id
                LEFT JOIN bronze_s360.equipamento e ON e.id = k.equipamento_id
                WHERE {NAO_EXC} AND a.data_coleta >= '2022-01-01'"""),
            "compartimentos": escalar(fb, """
                SELECT COUNT(*) AS n, SUM(CASE WHEN k.equipamento_id IS NULL THEN 1 ELSE 0 END) AS sem_equip,
                       SUM(CASE WHEN k.equipamento_id IS NOT NULL AND e.id IS NULL THEN 1 ELSE 0 END) AS equip_orfao
                FROM bronze_s360.compartimento k LEFT JOIN bronze_s360.equipamento e ON e.id = k.equipamento_id"""),
            "equipamentos_com_amostra": escalar(fb, f"""
                SELECT COUNT(*) AS n_equip,
                       SUM(CASE WHEN x.eid IS NOT NULL THEN 1 ELSE 0 END) AS com_amostra_2022
                FROM bronze_s360.equipamento e
                LEFT JOIN (SELECT DISTINCT k.equipamento_id AS eid FROM bronze_s360.amostra a
                           JOIN bronze_s360.compartimento k ON k.id = a.compartimento_id
                           WHERE {NAO_EXC} AND a.data_coleta >= '2022-01-01') x ON x.eid = e.id"""),
            "equip_com_varios_clientes": escalar(fb, f"""
                SELECT COUNT(*) AS equip_multi_cliente FROM (
                  SELECT k.equipamento_id FROM bronze_s360.amostra a
                  JOIN bronze_s360.compartimento k ON k.id = a.compartimento_id
                  WHERE {NAO_EXC} AND a.data_coleta >= '2022-01-01' AND a.cliente_id IS NOT NULL
                  GROUP BY k.equipamento_id HAVING COUNT(DISTINCT a.cliente_id) > 1) t"""),
        }
        amo["pert"] = amo["cliente_id"].isin(set(ids_cli))
        # amostras 2022+ por cliente S360 que casa com Protheus/Zoho (impacto KPI 1)
        amo = amo.merge(cli[["id", "codigo_legado_n", "id_cigam_n", "g"]], left_on="cliente_id", right_on="id", how="left")
        amo["k"] = amo["codigo_legado_n"].where(amo["codigo_legado_n"].notna(), amo["id_cigam_n"])
        out["E_impacto"] = {
            "amostras_2022_com_cliente_com_chave_erp": taxa_casamento(amo["cliente_id"].where(amo["k"].notna()), amo["cliente_id"], amo["n"]),
            "amostras_2022_cliente_casa_protheus": taxa_casamento(amo["k"], nf["k"], amo["n"]),
            "amostras_2022_cliente_casa_protheus_grupo": taxa_casamento(amo["g"], nf["g"], amo["n"]),
            "amostras_2022_cliente_casa_zoho_grupo": taxa_casamento(amo["g"], acc["erp_g"], amo["n"]),
            "amostras_2022_cliente_casa_zoho": taxa_casamento(amo["k"], acc["erp_n"], amo["n"]),
        }
        # pesos: amostras do cliente; para o 1º item o denominador são clientes com amostra
        tot_am = int(amo["n"].sum())
        out["E_impacto"]["amostras_2022_total"] = tot_am
        out["E_impacto"]["amostras_2022_cliente_sem_chave_erp"] = int(amo.loc[amo["k"].isna(), "n"].sum())
    salvar_json(out, SAIDA / "chaves.json")
    import json
    print(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
