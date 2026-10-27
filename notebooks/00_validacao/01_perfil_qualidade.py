"""Fase 0: perfil de qualidade das tabelas-chave e descobertas R2–R7 (somente agregados).

Local: `python notebooks/00_validacao/01_perfil_qualidade.py` a partir da raiz (abre o login no navegador na 1ª vez).
No Fabric: anexar o LakehouseOel como lakehouse padrão do notebook.
Saídas: <dados>/perfil/*.parquet, perfil.json e gates_g0.json (data/ local, fora do git; Files/ no Fabric).
"""
from __future__ import annotations

import sys
import traceback
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2] if "__file__" in globals() else Path.cwd()
sys.path.insert(0, str(RAIZ))

import pandas as pd  # noqa: E402

from src.gates.checks import avaliar_g0  # noqa: E402
from src.pipeline.fabric import Fabric, pasta_dados, salvar_json  # noqa: E402

SAIDA = pasta_dados(RAIZ) / "perfil"

TABELAS = {
    "bronze_s360.amostra": {"datas": ["data_coleta", "data_criacao", "data_entrada_laboratorio", "data_finalizacao"],
                            "chaves": ["id", "cliente_id", "compartimento_id"]},
    "bronze_s360.cliente": {"datas": ["data_registro"], "chaves": ["id", "codigo_legado", "id_cigam", "sam_id"]},
    "bronze_s360.equipamento": {"datas": ["data_registro"], "chaves": ["id", "familia_equipamento_id", "obra_id"]},
    "bronze_s360.compartimento": {"datas": ["data_registro"], "chaves": ["id", "equipamento_id"]},
    "silver_protheus.notassaida": {"datas": ["emissao"], "chaves": ["numero", "cod_cliente", "cod_produto"]},
    "silver_protheus.contasreceber": {"datas": ["emissao"], "chaves": ["numero", "cliente"]},
    "silver_zoho.accounts": {"datas": ["data_criacao"], "chaves": ["zoho_id", "cnpj", "erp_id", "id_protheus"]},
    "silver_zoho.deals": {"datas": ["data_criacao", "data_fechamento_prevista"], "chaves": ["zoho_id", "conta_id"]},
}

NAO_EXCLUIDA = "COALESCE(CAST(a.excluido AS INT), 0) = 0"

DESCOBERTAS = {
    "serie_amostras_mensal": f"""
        SELECT YEAR(a.data_coleta) AS ano, MONTH(a.data_coleta) AS mes,
               COUNT(*) AS amostras,
               SUM(CASE WHEN a.compartimento_id IS NULL THEN 1 ELSE 0 END) AS avulsas,
               SUM(CASE WHEN a.horimetro_equipado IS NOT NULL AND a.horimetro_equipado > 0 THEN 1 ELSE 0 END) AS com_horimetro,
               SUM(CASE WHEN a.horas_oleo IS NOT NULL AND a.horas_oleo > 0 THEN 1 ELSE 0 END) AS com_horas_oleo,
               COUNT(DISTINCT a.cliente_id) AS clientes
        FROM bronze_s360.amostra a WHERE {NAO_EXCLUIDA}
        GROUP BY YEAR(a.data_coleta), MONTH(a.data_coleta)""",
    "serie_faturamento_mensal": """
        SELECT YEAR(n.emissao) AS ano, MONTH(n.emissao) AS mes, COUNT(*) AS itens,
               COUNT(DISTINCT n.cod_cliente) AS clientes, SUM(n.total) AS total
        FROM silver_protheus.notassaida n GROUP BY YEAR(n.emissao), MONTH(n.emissao)""",
    "amostras_cliente_mes": f"""
        SELECT a.cliente_id, YEAR(a.data_coleta) AS ano, MONTH(a.data_coleta) AS mes, COUNT(*) AS amostras,
               SUM(CASE WHEN a.compartimento_id IS NULL THEN 1 ELSE 0 END) AS avulsas,
               MAX(a.data_coleta) AS ultima_data
        FROM bronze_s360.amostra a WHERE {NAO_EXCLUIDA}
        GROUP BY a.cliente_id, YEAR(a.data_coleta), MONTH(a.data_coleta)""",
    "faturamento_cliente_mes": """
        SELECT TRIM(n.cod_cliente) AS cod_cliente, YEAR(n.emissao) AS ano, MONTH(n.emissao) AS mes,
               SUM(n.total) AS total, COUNT(*) AS itens, MAX(n.emissao) AS ultima_data
        FROM silver_protheus.notassaida n GROUP BY TRIM(n.cod_cliente), YEAR(n.emissao), MONTH(n.emissao)""",
    "produtos_faturados": """
        SELECT TRIM(n.cod_produto) AS cod_produto, n.unid_medida, n.cfop, YEAR(n.emissao) AS ano,
               COUNT(*) AS itens, SUM(n.quantidade) AS quantidade, SUM(n.total) AS total
        FROM silver_protheus.notassaida n GROUP BY TRIM(n.cod_produto), n.unid_medida, n.cfop, YEAR(n.emissao)""",
    "familias_equipamento": f"""
        SELECT e.familia_equipamento_id, CAST(e.ativo AS INT) AS ativo,
               COUNT(DISTINCT e.id) AS equipamentos, COUNT(a.id) AS amostras,
               MAX(a.data_coleta) AS ultima_coleta
        FROM bronze_s360.equipamento e
        LEFT JOIN bronze_s360.compartimento c ON c.equipamento_id = e.id
        LEFT JOIN bronze_s360.amostra a ON a.compartimento_id = c.id AND {NAO_EXCLUIDA}
        GROUP BY e.familia_equipamento_id, CAST(e.ativo AS INT)""",
    "equipamento_ultima_coleta": f"""
        SELECT e.id AS equipamento_id, e.familia_equipamento_id, CAST(e.ativo AS INT) AS ativo,
               e.data_registro, MIN(a.data_coleta) AS primeira_coleta, MAX(a.data_coleta) AS ultima_coleta,
               COUNT(a.id) AS amostras, COUNT(DISTINCT a.cliente_id) AS clientes
        FROM bronze_s360.equipamento e
        LEFT JOIN bronze_s360.compartimento c ON c.equipamento_id = e.id
        LEFT JOIN bronze_s360.amostra a ON a.compartimento_id = c.id AND {NAO_EXCLUIDA}
        GROUP BY e.id, e.familia_equipamento_id, CAST(e.ativo AS INT), e.data_registro""",
    "chaves_s360_cliente": """
        SELECT c.id AS cliente_id, TRIM(c.codigo_legado) AS codigo_legado, TRIM(c.id_cigam) AS id_cigam,
               TRIM(c.sam_id) AS sam_id, CAST(c.ativo AS INT) AS ativo, c.seguimento_cliente_id, c.setor_cliente_id
        FROM bronze_s360.cliente c""",
    "chaves_zoho_accounts": """
        SELECT z.zoho_id, TRIM(z.cnpj) AS cnpj, TRIM(z.erp_id) AS erp_id, TRIM(z.id_protheus) AS id_protheus,
               z.conta_pai_id, z.setor, z.segmento, z.status, z.status_real
        FROM silver_zoho.accounts z""",
    "deals_probabilidade": """
        SELECT d.estagio, d.probabilidade, YEAR(d.data_fechamento_prevista) AS ano_prev,
               MONTH(d.data_fechamento_prevista) AS mes_prev, COUNT(*) AS deals, SUM(d.valor) AS valor
        FROM silver_zoho.deals d
        GROUP BY d.estagio, d.probabilidade, YEAR(d.data_fechamento_prevista), MONTH(d.data_fechamento_prevista)""",
}


def perfil_tabela(fb: Fabric, nome: str, cfg: dict) -> dict:
    schema, tabela = nome.split(".")
    cols = fb.colunas(schema, tabela)["COLUMN_NAME"].tolist()
    partes = ["COUNT(*) AS n_linhas"]
    partes += [f"SUM(CASE WHEN {c} IS NULL THEN 1 ELSE 0 END) AS nulo__{c}" for c in cols]
    partes += [f"COUNT(DISTINCT {c}) AS distinto__{c}" for c in cfg["chaves"]]
    for d in cfg["datas"]:
        partes += [f"MIN({d}) AS min__{d}", f"MAX({d}) AS max__{d}"]
    linha = fb.query(f"SELECT {', '.join(partes)} FROM {nome}").iloc[0]
    n = int(linha["n_linhas"])
    return {
        "tabela": nome,
        "n_linhas": n,
        "n_colunas": len(cols),
        "nulos_pct": {c: round(100 * float(linha[f"nulo__{c}"]) / n, 2) if n else None for c in cols},
        "distintos": {c: int(linha[f"distinto__{c}"]) for c in cfg["chaves"]},
        "datas": {d: [str(linha[f"min__{d}"]), str(linha[f"max__{d}"])] for d in cfg["datas"]},
    }


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    perfis, erros = [], {}
    with Fabric() as fb:
        for nome, cfg in TABELAS.items():
            print(f"perfil {nome} ...", flush=True)
            try:
                perfis.append(perfil_tabela(fb, nome, cfg))
            except Exception as e:  # registra e segue: uma tabela não derruba o perfil
                erros[nome] = f"{type(e).__name__}: {e}"
                traceback.print_exc()
        for nome, sql in DESCOBERTAS.items():
            print(f"descoberta {nome} ...", flush=True)
            try:
                fb.query(sql).to_parquet(SAIDA / f"{nome}.parquet", index=False)
            except Exception as e:
                erros[nome] = f"{type(e).__name__}: {e}"
                traceback.print_exc()
    salvar_json({"gerado_em": datetime.now().isoformat(), "perfis": perfis, "erros": erros}, SAIDA / "perfil.json")
    gates = avaliar_g0(perfis)
    salvar_json(gates, SAIDA / "gates_g0.json")
    falhas = [g for g in gates if not g["ok"]]
    print(f"ok: {len(perfis)} perfis, {len(erros)} erros, G0 {len(gates) - len(falhas)}/{len(gates)} checagens aprovadas.")
    for g in falhas:
        print(f"  G0 FALHA {g['checagem']} {g['alvo']}: {g['detalhe']}")


if __name__ == "__main__":
    main()
