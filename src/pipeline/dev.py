"""T30: pré-consultas e saídas dos notebooks de desenvolvimento (notebooks/50_dev), lakehouse por parâmetro.

Fase 5b (docs_fabric/09 §0): lê o lakehouse escolhido (padrão `LakehouseOel`) só com SELECT, monta as entradas
como temp views `v_als_src_*` / `v_als_amostras_mes` e as saídas do contrato da T28 (`v_als_*` + parquet em
`Files/als_oilmodel/saida/`). Nada de tabela permanente nem escrita em /Tables/.

O forecast aqui é o baseline ingênuo sazonal com intervalo pelos resíduos sazonais da própria série: serve para
exercitar o fluxo ponta a ponta no Fabric e o contrato; o modelo escolhido entra na T15. Potencial, churn e
vendas ficam de fora (T16, RN-06 com horímetro e KPI 2): as colunas anuláveis saem vazias.
Pandas puro (sem Spark) para rodar igual local e no Fabric e ser testado sem acesso aos dados.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.backtest.comparacao import rotular_segmento
from src.backtest.snapshot import versao_dados
from src.features.alertas import alertar_queda
from src.features.base import ParametrosBase, mapa_zoho, mapear_s360
from src.features.regras import inicio_mes
from src.serving.contrato import CONTRATOS, aprovado, validar

LAKEHOUSE_PADRAO = "LakehouseOel"
# S360 só existe em bronze_s360 no LakehouseOel (T14); Zoho e Protheus estão em silver_*.
SCHEMAS_PADRAO = {"s360": "bronze_s360", "zoho": "silver_zoho"}
MODELO = "ingenuo_sazonal_dev"
_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Temp views de entrada: só projeção das colunas usadas, sem filtro (o lakehouse de origem não é tocado).
FONTES = {
    "v_als_src_amostra": ("s360", "amostra",
                          "id, cliente_id, compartimento_id, data_coleta, data_entrada_laboratorio, excluido"),
    "v_als_src_compartimento": ("s360", "compartimento", "id, equipamento_id"),
    "v_als_src_equipamento": ("s360", "equipamento", "id"),
    "v_als_src_cliente": ("s360", "cliente", "id AS cliente_id, TRIM(id_cigam) AS id_cigam, "
                                              "TRIM(codigo_legado) AS codigo_legado, CAST(ativo AS INT) AS ativo"),
    "v_als_src_zoho_accounts": ("zoho", "accounts", "zoho_id, cnpj, erp_id, conta, razao_social, segmento"),
}


def resolver_lakehouse(valor: str | None = None) -> str:
    """Parâmetro do notebook > ALS_LAKEHOUSE > LakehouseOel. Só identificador simples (vai para o SQL)."""
    lh = (valor or os.environ.get("ALS_LAKEHOUSE") or LAKEHOUSE_PADRAO).strip()
    if not _IDENT.match(lh):
        raise ValueError(f"nome de lakehouse inválido: {lh!r}")
    return lh


def qualificar(lakehouse: str, schema: str, tabela: str) -> str:
    for parte in (lakehouse, schema, tabela):
        if not _IDENT.match(parte):
            raise ValueError(f"identificador inválido: {parte!r}")
    return f"`{lakehouse}`.{schema}.{tabela}"


def sql_fontes(lakehouse: str, schemas: dict[str, str] | None = None) -> dict[str, str]:
    """temp view → SELECT no lakehouse de origem."""
    sch = {**SCHEMAS_PADRAO, **(schemas or {})}
    return {v: f"SELECT {cols} FROM {qualificar(lakehouse, sch[fonte], tab)}"
            for v, (fonte, tab, cols) in FONTES.items()}


def janela(data_corte: str | pd.Timestamp | None = None, meses: int = 36) -> tuple[pd.Timestamp, pd.Timestamp]:
    """(início do histórico, data de corte). Corte = 1º dia do mês corrente (ou do informado); histórico < corte."""
    corte = inicio_mes(pd.Timestamp(data_corte) if data_corte else pd.Timestamp.now().normalize())
    return corte - pd.DateOffset(months=meses), corte


def sql_amostras_mes(desde: pd.Timestamp, corte: pd.Timestamp, p: ParametrosBase = ParametrosBase()) -> str:
    """Amostras por cliente S360 × equipamento × mês sobre as temp views; mesmas regras de data e exclusão da T14,
    sem avulsas (D9: só amostra com compartimento e equipamento no cadastro)."""
    lim = corte.strftime("%Y-%m-%d")
    plaus = "{c} >= '" + p.data_min + "' AND {c} < '" + lim + "'"
    data = (f"CASE WHEN {plaus.format(c='a.data_coleta')} THEN a.data_coleta "
            f"WHEN {plaus.format(c='a.data_entrada_laboratorio')} THEN a.data_entrada_laboratorio END")
    return f"""
        SELECT a.cliente_id, e.id AS equipamento_id, YEAR({data}) AS ano, MONTH({data}) AS mes,
               COUNT(DISTINCT a.id) AS amostras
        FROM v_als_src_amostra a
        JOIN v_als_src_compartimento c ON c.id = a.compartimento_id
        JOIN v_als_src_equipamento e ON e.id = c.equipamento_id
        WHERE COALESCE(CAST(a.excluido AS INT), 0) = 0 AND ({data}) >= '{desde.strftime("%Y-%m-%d")}'
        GROUP BY a.cliente_id, e.id, YEAR({data}), MONTH({data})"""


# ---------------------------------------------------------------- séries
def series_mensais(amostras_mes: pd.DataFrame, clientes: pd.DataFrame, accounts: pd.DataFrame,
                   desde: pd.Timestamp, corte: pd.Timestamp) -> pd.DataFrame:
    """[nivel, entidade_id, entidade_nome, cliente_id, segmento, periodo, y] mensal contínuo (zeros) de
    max(desde, 1ª coleta da entidade) até o mês anterior ao corte, nos níveis segmento, cliente e equipamento.
    Cliente = entidade da ponte S360 → Zoho da T14 (raiz do CNPJ quando há)."""
    z = mapa_zoho(accounts)
    cli = clientes.assign(cliente_id=lambda x: pd.to_numeric(x["cliente_id"]).astype("int64"))
    mapa = mapear_s360(cli, z).set_index("cliente_id")["entidade"]
    seg = z.dropna(subset=["segmento"]).groupby("entidade")["segmento"].agg(lambda s: s.value_counts().idxmax())
    nome = z.dropna(subset=["nome"]).groupby("entidade")["nome"].agg(lambda s: s.value_counts().idxmax())

    a = amostras_mes.dropna(subset=["ano", "mes"]).copy()
    a["periodo"] = pd.to_datetime(dict(year=a["ano"].astype(int), month=a["mes"].astype(int), day=1))
    a = a[(a["periodo"] >= desde) & (a["periodo"] < corte)]
    a["cliente"] = pd.to_numeric(a["cliente_id"]).astype("int64").map(mapa)
    a = a.dropna(subset=["cliente"])
    a["equipamento_id"] = a["equipamento_id"].astype("int64").astype(str)
    dono = (a.groupby(["equipamento_id", "cliente"])["amostras"].sum().reset_index()
            .sort_values(["amostras", "cliente"], ascending=[False, True]).drop_duplicates("equipamento_id")
            .set_index("equipamento_id")["cliente"])

    meses = pd.date_range(max(desde, a["periodo"].min()) if len(a) else desde, corte - pd.DateOffset(months=1),
                          freq="MS")
    partes = []
    for nivel, chave in (("cliente", "cliente"), ("equipamento", "equipamento_id")):
        g = a.groupby([chave, "periodo"], as_index=False)["amostras"].sum().rename(columns={chave: "entidade_id"})
        primeiro = g.groupby("entidade_id")["periodo"].min()
        grade = pd.MultiIndex.from_product([primeiro.index, meses], names=["entidade_id", "periodo"]).to_frame(False)
        grade = grade[grade["periodo"] >= grade["entidade_id"].map(primeiro)]
        s = grade.merge(g, on=["entidade_id", "periodo"], how="left").fillna({"amostras": 0})
        s["cliente_id"] = s["entidade_id"] if nivel == "cliente" else s["entidade_id"].map(dono)
        s["nivel"] = nivel
        partes.append(s)
    s = pd.concat(partes, ignore_index=True).rename(columns={"amostras": "y"})
    s["segmento"] = rotular_segmento(s["cliente_id"].map(seg))
    s["entidade_nome"] = np.where(s["nivel"] == "cliente", s["cliente_id"].map(nome).fillna(s["cliente_id"]),
                                  "equip " + s["entidade_id"].astype(str))
    porseg = (s[s["nivel"] == "cliente"].groupby(["segmento", "periodo"], as_index=False)["y"].sum()
              .assign(nivel="segmento", entidade_id=lambda x: x["segmento"], entidade_nome=lambda x: x["segmento"]))
    cols = ["nivel", "entidade_id", "entidade_nome", "segmento", "periodo", "y"]
    out = pd.concat([porseg[cols], s[cols]], ignore_index=True)
    out["y"] = out["y"].astype(float)
    out["entidade_id"] = out["entidade_id"].astype(str)
    out["entidade_nome"] = out["entidade_nome"].astype(str)
    cli = [None] * len(porseg) + [None if pd.isna(v) else str(v) for v in s["cliente_id"]]
    out.insert(3, "cliente_id", pd.Series(cli, dtype=object))
    return out


# ---------------------------------------------------------------- saídas do contrato
_CHAVE = ["nivel", "entidade_id"]
_DIM = ["nivel", "entidade_id", "entidade_nome", "cliente_id", "segmento"]


def forecast_consumo(serie: pd.DataFrame, corte: pd.Timestamp, h: int = 12, modelo: str = MODELO) -> pd.DataFrame:
    """Histórico (realizado) + h meses a partir do corte. p50 = y(t−12) (série com < 12 meses repete o último);
    p10/p90 = p50 + quantis 10/90 dos resíduos sazonais y(t) − y(t−12) da entidade (sem resíduo: p10 = p90 = p50)."""
    if not 1 <= h <= 12:
        raise ValueError("h entre 1 e 12: o ingênuo sazonal só usa meses já observados")
    s = serie.sort_values(_CHAVE + ["periodo"])
    dim = s.drop_duplicates(_CHAVE)[_DIM]
    ant = s[_CHAVE + ["periodo", "y"]].assign(periodo=lambda x: x["periodo"] + pd.DateOffset(months=12))
    res = s.merge(ant, on=_CHAVE + ["periodo"], suffixes=("", "_12"))
    res = res.assign(r=res["y"] - res["y_12"]).groupby(_CHAVE)["r"]
    res = pd.DataFrame({"q10": res.quantile(0.1), "q90": res.quantile(0.9)})
    ult = s.groupby(_CHAVE).agg(ultimo=("y", "last"), n=("y", "size"))

    fut = pd.MultiIndex.from_product([range(len(dim)), pd.date_range(corte, periods=h, freq="MS")])
    f = dim.iloc[fut.get_level_values(0)].reset_index(drop=True).assign(periodo=fut.get_level_values(1))
    f = f.merge(ant.rename(columns={"y": "base"}), on=_CHAVE + ["periodo"], how="left")
    f = f.join(ult, on=_CHAVE).join(res, on=_CHAVE)
    p50 = np.where((f["n"] >= 12) & f["base"].notna(), f["base"], f["ultimo"]).astype(float)
    q10, q90 = f["q10"].fillna(0).to_numpy(), f["q90"].fillna(0).to_numpy()
    f["prev_p50"] = p50
    f["prev_p10"] = np.clip(np.minimum(p50, p50 + q10), 0, None)
    f["prev_p90"] = np.maximum(p50, p50 + q90)

    hist = s.rename(columns={"y": "realizado"})
    out = pd.concat([hist, f[_DIM + ["periodo", "prev_p10", "prev_p50", "prev_p90"]]], ignore_index=True)
    out = out.assign(granularidade="mes", potencial=np.nan, potencial_p10=np.nan, potencial_p90=np.nan,
                     data_corte=corte, versao_modelo=f"{modelo}+{versao_dados(serie[['nivel', 'entidade_id', 'periodo', 'y']])}")
    return out[CONTRATOS["forecast_consumo"].nomes()]


def pct_achieved(serie: pd.DataFrame, corte: pd.Timestamp, potencial: pd.DataFrame | None = None) -> pd.DataFrame:
    """Realizado dos 12 meses antes do corte ÷ potencial anual (D6). Sem `potencial` [nivel, entidade_id,
    potencial_12m] (T16), potencial e % saem vazios."""
    ini = corte - pd.DateOffset(months=12)
    s = serie[(serie["periodo"] >= ini) & (serie["periodo"] < corte)]
    out = s.groupby(_CHAVE, as_index=False).agg(realizado_12m=("y", "sum"))
    out = out.merge(serie.drop_duplicates(_CHAVE)[_DIM], on=_CHAVE)
    eq = s[(s["nivel"] == "equipamento") & (s["y"] > 0)]
    n_cli = eq.groupby("cliente_id")["entidade_id"].nunique()
    n_seg = eq.groupby("segmento")["entidade_id"].nunique()
    out["n_equip"] = np.select([out["nivel"] == "cliente", out["nivel"] == "segmento"],
                               [out["cliente_id"].map(n_cli), out["entidade_id"].map(n_seg)], 1.0)
    out["n_equip"] = out["n_equip"].fillna(0).astype("int64")
    if potencial is not None:
        out = out.merge(potencial[_CHAVE + ["potencial_12m"]], on=_CHAVE, how="left")
    else:
        out["potencial_12m"] = np.nan
    out["pct_achieved"] = out["realizado_12m"] / out["potencial_12m"].where(out["potencial_12m"] > 0)
    out = out.assign(porte=None, data_corte=corte)
    return out[CONTRATOS["pct_achieved"].nomes()]


def alertas(serie: pd.DataFrame, corte: pd.Timestamp, base: str = "ano_anterior") -> pd.DataFrame:
    """Queda > 20% do cliente no último mês fechado (RN-05, base configurável; mês sem coleta não alerta).
    Churn de compartimento (RN-06) depende de horímetro e fica fora desta versão."""
    cli = serie[(serie["nivel"] == "cliente") & (serie["y"] > 0)]
    q = alertar_queda(cli, base=base, chave="entidade_id", valor="y")
    q = q[(q["periodo"] == corte - pd.DateOffset(months=1)) & q["alerta_queda"]]
    q = q.merge(serie.drop_duplicates(_CHAVE)[_DIM].query("nivel == 'cliente'"), on="entidade_id")
    out = q.assign(tipo="queda", valor_atual=q["y"].astype(float), valor_base=q["base_valor"].astype(float),
                   variacao_pct=q["queda"].astype(float), detalhe=f"base={base}")
    return out[CONTRATOS["alertas"].nomes()].reset_index(drop=True)


def gerar(serie: pd.DataFrame, corte: pd.Timestamp, h: int = 12, base_alerta: str = "ano_anterior") -> dict:
    return {"forecast_consumo": forecast_consumo(serie, corte, h), "pct_achieved": pct_achieved(serie, corte),
            "alertas": alertas(serie, corte, base_alerta)}


def gravar(saidas: dict[str, pd.DataFrame], pasta: Path) -> dict:
    """Valida cada saída no contrato (G4) e grava em `pasta` só as aprovadas; o relatório dos gates sempre."""
    pasta.mkdir(parents=True, exist_ok=True)
    rel = {"gravadas": [], "reprovadas": [], "gates": []}
    for nome, df in saidas.items():
        res = validar(nome, df)
        rel["gates"].extend(res)
        if aprovado(res):
            df.to_parquet(pasta / CONTRATOS[nome].arquivo, index=False)
            rel["gravadas"].append({"saida": nome, "arquivo": CONTRATOS[nome].arquivo, "linhas": len(df)})
        else:
            rel["reprovadas"].append(nome)
    (pasta / "relatorio_dev.json").write_text(json.dumps(rel, indent=2, ensure_ascii=False, default=str),
                                             encoding="utf-8")
    return rel
