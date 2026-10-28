"""T29: monta as saídas do KPI 1 no contrato da T28 (`src/serving/contrato.py`).

Funções puras (pandas), iguais local e no Fabric: recebem séries e previsões já calculadas e devolvem os
DataFrames de `forecast_consumo`, `pct_achieved`, `alertas` e `backtest_metricas` com as colunas do contrato.
Convenções: séries mensais [id, periodo, y]; previsões [id, periodo, yhat, yhat_lo, yhat_hi] (p50, p10, p90);
`atributos` indexado por id com `entidade_nome`, `cliente_id` e `segmento`; potencial anual por id.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.alertas import LIMIAR_QUEDA, ParametrosChurnCompartimento, alertar_queda, compartimento_churn
from src.models.potencial import pct_achieved as _pct
from src.serving.contrato import ALERTAS, BACKTEST_METRICAS, FORECAST_CONSUMO, PCT_ACHIEVED

MESES_ANO = 12
HORAS_MES = 365 * 24 / 12   # 730 h: converte meses de calendário em horas (proxy do horímetro no churn)


def _mes(s) -> pd.Series:
    return pd.to_datetime(s).dt.to_period("M").dt.to_timestamp()


def _meses_entre(a: pd.Series, b: pd.Timestamp | pd.Series) -> pd.Series:
    """Nº de meses de calendário de `a` até `b` (b − a)."""
    b_ano, b_mes = (b.year, b.month) if isinstance(b, pd.Timestamp) else (b.dt.year, b.dt.month)
    return (b_ano - a.dt.year) * 12 + (b_mes - a.dt.month)


def grade_mensal(df: pd.DataFrame, inicio, fim, chave: str = "id", periodo: str = "periodo",
                 valor: str = "y") -> pd.DataFrame:
    """Série esparsa (só meses com valor) → [id, periodo, y] contínua de max(1º mês do id, `inicio`) até `fim`.

    Vetorizado (pivot), para centenas de milhares de séries; equivale a `regras.completar_meses` na janela.
    """
    df = df.assign(**{periodo: _mes(df[periodo])})
    inicio, fim = pd.Timestamp(inicio), pd.Timestamp(fim)
    df = df[df[periodo] <= fim]
    primeiro = df.groupby(chave)[periodo].min()
    jan = df[df[periodo] >= inicio].groupby([chave, periodo])[valor].sum().unstack(periodo)
    meses = pd.date_range(inicio, fim, freq="MS")
    ids = primeiro.index[primeiro <= fim]
    m = jan.reindex(index=ids, columns=meses).fillna(0.0)
    m = m.where(np.asarray(meses)[None, :] >= primeiro.reindex(ids).to_numpy()[:, None])
    out = m.stack().rename("y").reset_index()
    out.columns = ["id", "periodo", "y"]
    return out


def _ident(nivel: str, ids: pd.Series, atributos: pd.DataFrame) -> pd.DataFrame:
    """Colunas de identificação do contrato; nome ausente vira o próprio id, segmento ausente `sem_segmento`."""
    ids = ids.astype(str).to_numpy()
    a = atributos.reindex(ids)
    nome, cli, seg = (a[c].astype(object).to_numpy() for c in ("entidade_nome", "cliente_id", "segmento"))
    return pd.DataFrame({
        "nivel": nivel, "entidade_id": ids,
        "entidade_nome": np.where(pd.isna(nome), ids, nome).astype(str),
        "cliente_id": np.where(pd.isna(cli), None, cli),
        "segmento": np.where(pd.isna(seg), "sem_segmento", seg).astype(str),
    })


def forecast_consumo(nivel: str, historico: pd.DataFrame, previsao: pd.DataFrame, corte, versao_modelo: str,
                     atributos: pd.DataFrame, potencial: pd.DataFrame | None = None) -> pd.DataFrame:
    """Linhas do contrato `forecast_consumo` de um nível: histórico (realizado, períodos < corte) + horizonte.

    `potencial` (opcional): [id, potencial, potencial_p10, potencial_p90] anuais; vira valor mensal (÷ 12) em todas
    as linhas da entidade (é o potencial vigente no corte, não reconstruído para o passado).
    """
    corte = pd.Timestamp(corte)
    h = historico[_mes(historico["periodo"]) < corte]
    f = previsao[_mes(previsao["periodo"]) >= corte]
    linhas = pd.concat([
        pd.DataFrame({"id": h["id"].to_numpy(), "periodo": _mes(h["periodo"]).to_numpy(),
                      "realizado": h["y"].astype(float).to_numpy()}),
        pd.DataFrame({"id": f["id"].to_numpy(), "periodo": _mes(f["periodo"]).to_numpy(),
                      "prev_p10": f["yhat_lo"].to_numpy(), "prev_p50": f["yhat"].to_numpy(),
                      "prev_p90": f["yhat_hi"].to_numpy()}),
    ], ignore_index=True)
    linhas["id"] = linhas["id"].astype(str)
    out = _ident(nivel, linhas["id"], atributos)
    out["granularidade"] = "mes"
    out["periodo"] = linhas["periodo"].to_numpy()
    for c in ("realizado", "prev_p10", "prev_p50", "prev_p90"):
        out[c] = linhas[c].astype(float).to_numpy()
    pot = (potencial.assign(id=potencial["id"].astype(str)).set_index("id") if potencial is not None
           else pd.DataFrame(columns=["potencial", "potencial_p10", "potencial_p90"]))
    for c in ("potencial", "potencial_p10", "potencial_p90"):
        out[c] = linhas["id"].map(pot[c].astype(float) / MESES_ANO).to_numpy() if c in pot else np.nan
    out["data_corte"] = corte
    out["versao_modelo"] = versao_modelo
    return out[FORECAST_CONSUMO.nomes()]


def segmento_bottom_up(previsao_cliente: pd.DataFrame, segmento_de: pd.Series,
                       previsao_segmento: pd.DataFrame | None = None) -> pd.DataFrame:
    """Previsão do nível segmento: p50 = Σ p50 dos clientes (bottom-up, soma exata com o nível cliente).

    Somar p10/p90 não dá o p10/p90 da soma. Com `previsao_segmento` (modelo direto nas séries de segmento) o
    intervalo usa a largura relativa dele: p10 = p50_bu × p10_dir ÷ p50_dir (idem p90); sem ela, soma os quantis.
    """
    p = previsao_cliente.assign(segmento=previsao_cliente["id"].astype(str).map(segmento_de).fillna("sem_segmento"))
    s = p.groupby(["segmento", "periodo"], as_index=False)[["yhat", "yhat_lo", "yhat_hi"]].sum()
    if previsao_segmento is not None:
        d = previsao_segmento.rename(columns={"id": "segmento"})
        d = d.assign(r_lo=(d["yhat_lo"] / d["yhat"]).where(d["yhat"] > 0, 1.0),
                     r_hi=(d["yhat_hi"] / d["yhat"]).where(d["yhat"] > 0, 1.0))
        s = s.merge(d[["segmento", "periodo", "r_lo", "r_hi"]], on=["segmento", "periodo"], how="left")
        tem = s["r_lo"].notna()
        s.loc[tem, "yhat_lo"] = s.loc[tem, "yhat"] * s.loc[tem, "r_lo"].clip(upper=1)
        s.loc[tem, "yhat_hi"] = s.loc[tem, "yhat"] * s.loc[tem, "r_hi"].clip(lower=1)
        s = s.drop(columns=["r_lo", "r_hi"])
    return s.rename(columns={"segmento": "id"})


def pct_achieved(nivel: str, tabela: pd.DataFrame, corte, atributos: pd.DataFrame) -> pd.DataFrame:
    """Contrato `pct_achieved` (D6): tabela [id, realizado_12m, potencial_12m, porte?, n_equip?] de um nível."""
    out = _ident(nivel, tabela["id"].astype(str), atributos).drop(columns="cliente_id")
    out["porte"] = (tabela["porte"].astype(object).where(tabela["porte"].notna(), None).to_numpy()
                    if "porte" in tabela else None)
    out["n_equip"] = tabela["n_equip"].to_numpy() if "n_equip" in tabela else np.nan
    out["data_corte"] = pd.Timestamp(corte)
    out["realizado_12m"] = tabela["realizado_12m"].astype(float).to_numpy()
    out["potencial_12m"] = tabela["potencial_12m"].astype(float).to_numpy()
    out["pct_achieved"] = _pct(out["realizado_12m"], out["potencial_12m"])
    return out[PCT_ACHIEVED.nomes()]


def alertas_queda(mensal: pd.DataFrame, mes, atributos: pd.DataFrame, base: str = "ano_anterior",
                  limiar: float = LIMIAR_QUEDA) -> pd.DataFrame:
    """RN-05 no mês fechado `mes`: clientes com queda > limiar contra `base`. `mensal` = [id, periodo, y].

    Mês com y = 0 é tratado como mês sem coleta (NaN, sem alerta), como em `alertas.alertar_queda`.
    """
    m = mensal[mensal["y"] > 0].rename(columns={"id": "cliente", "y": "valor"})
    q = alertar_queda(m[["cliente", "periodo", "valor"]], base=base, limiar=limiar)
    q = q[(q["periodo"] == pd.Timestamp(mes)) & q["alerta_queda"]]
    out = _ident("cliente", q["cliente"].astype(str), atributos)
    out.insert(0, "tipo", "queda")
    out["cliente_id"] = out["entidade_id"]
    out["periodo"] = pd.Timestamp(mes)
    out["valor_atual"] = q["valor"].astype(float).to_numpy()
    out["valor_base"] = q["base_valor"].astype(float).to_numpy()
    out["variacao_pct"] = q["queda"].astype(float).to_numpy()
    out["detalhe"] = f"base={base}; limiar={limiar:.0%}"
    return out[ALERTAS.nomes()]


def alertas_churn(coletas: pd.DataFrame, corte, atributos: pd.DataFrame,
                  p: ParametrosChurnCompartimento = ParametrosChurnCompartimento(), min_coletas: int = 3,
                  meses_ativo: int = 12) -> pd.DataFrame:
    """RN-06 por equipamento com **proxy de calendário** (sem horímetro): `coletas` = [id, periodo, y] com y > 0.

    Intervalo esperado = mediana dos meses entre coletas consecutivas × 730 h; horas sem coleta = horas de
    calendário do 1º dia do último mês com coleta até o corte. Só equipamentos ativos (T05: coleta nos
    `meses_ativo` meses até o corte) com ≥ `min_coletas` meses coletados. Usa `alertas.compartimento_churn`.
    """
    corte = pd.Timestamp(corte)
    c = coletas[(coletas["y"] > 0)].assign(periodo=lambda d: _mes(d["periodo"]))
    c = c[c["periodo"] < corte].drop_duplicates(["id", "periodo"]).sort_values(["id", "periodo"])
    idx = c["periodo"].dt.year * 12 + c["periodo"].dt.month
    c = c.assign(gap=idx.groupby(c["id"]).diff())
    g = c.groupby("id").agg(ultima=("periodo", "max"), n=("periodo", "size"), gap=("gap", "median"))
    g = g[(g["n"] >= min_coletas) & (_meses_entre(g["ultima"], corte) <= meses_ativo)]
    epoca = pd.Timestamp("2000-01-01")
    entrada = pd.DataFrame({"equipamento": g.index, "compartimento": "todos",
                            "horimetro": ((g["ultima"] - epoca).dt.days * 24.0).to_numpy(),
                            "intervalo_h": (g["gap"] * HORAS_MES).to_numpy(),
                            "horimetro_atual": float((corte - epoca).days * 24)})
    r = compartimento_churn(entrada, p)
    r = r[r["compartimento_churn"]].merge(g[["gap"]], left_on="equipamento", right_index=True)
    out = _ident("equipamento", r["equipamento"].astype(str), atributos)
    out.insert(0, "tipo", "churn")
    out["periodo"] = corte
    out["valor_atual"] = r["horas_sem_coleta"].astype(float).to_numpy()
    out["valor_base"] = r["intervalo_h"].astype(float).to_numpy()
    out["variacao_pct"] = np.nan
    out["detalhe"] = [f"proxy calendário (sem horímetro); intervalo mediano {x:g} m; fator {p.fator:g}"
                      for x in r["gap"]]
    return out[ALERTAS.nomes()]


def backtest_metricas(tabela: pd.DataFrame, kpi: str, data_corte, versao_modelo: str) -> pd.DataFrame:
    """`comparacao.tabela_comparativa` → contrato `backtest_metricas` (segmento TODOS vira 'todos')."""
    t = tabela.copy()
    t["kpi"] = kpi
    t["segmento"] = t["segmento"].replace({"TODOS": "todos"}).astype(str)
    t["horizonte"] = t["horizonte"].astype(int)
    t["n"] = t["n"].astype(int)
    t["data_corte"] = pd.Timestamp(data_corte)
    t["versao_modelo"] = versao_modelo
    for c in ("wape", "mae", "bias_pct", "smape", "cobertura"):
        t[c] = t[c].astype(float) if c in t else np.nan
    return t[BACKTEST_METRICAS.nomes()].reset_index(drop=True)
