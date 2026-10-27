"""KPI 2: receita derivada do consumo (H2), composição pelas classes do Forecast 27 e o Forecast 27 a partir dos dados.

Entrada padrão: tabela mensal por cliente (`cliente`, `periodo`, `valor`), como em src/features/regras.py.
O alvo é qualquer coluna de valor: faturamento e EBIT são targets separados (D2) e passam pelas mesmas funções.
Novos e reativados ficam fora do escopo (D3): entram como zero nos componentes e saem do realizado "em escopo".
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.regras import ParametrosRecorrencia, classificar_clientes, inicio_mes, receita_churn

# CFOP pelos 3 últimos dígitos (o 1º dígito só diz se é dentro ou fora do estado)
CFOP_ANALISE = ("933",)                     # prestação de serviço: análise processada
CFOP_KIT = ("101", "102", "108", "110", "117")  # venda de mercadoria: kit/frasco
CLASSES_ESCOPO = ("recorrente", "nao_recorrente_ativo")

# % manual por mês do Forecast 27 (coluna "Variaveis de Mercado/Cenário"), por mês do calendário
VAR_MERCADO_FY27 = {9: -0.03, 10: 0.0, 11: 0.02, 12: -0.24, 1: -0.20, 2: -0.15, 3: -0.08}


def tipo_cfop(cfop: pd.Series, analise=CFOP_ANALISE, kit=CFOP_KIT) -> pd.Series:
    """'analise', 'kit' ou 'outros' (remessas, bonificações, CFOP 949 etc.)."""
    c3 = cfop.astype(str).str.strip().str[-3:]
    return pd.Series(np.select([c3.isin(analise), c3.isin(kit)], ["analise", "kit"], "outros"), index=cfop.index)


def receita_por_tipo(faturamento: pd.DataFrame, mapa: pd.DataFrame, excluir: tuple[str, ...] = ()) -> pd.DataFrame:
    """Protheus agregado (cod_cliente, cfop, ano, mes, total) → entidade × periodo × [analise, kit, outros, total].

    `mapa`: cod_cliente → entidade (T14). `excluir`: CFOP (3 dígitos) fora do faturamento, como na tabela-base.
    """
    f = faturamento.copy()
    f = f[~f["cfop"].astype(str).str[-3:].isin(excluir)]
    f["valor"] = pd.to_numeric(f["total"], errors="coerce").fillna(0.0)
    f["tipo"] = tipo_cfop(f["cfop"])
    f["periodo"] = pd.to_datetime(dict(year=f["ano"], month=f["mes"], day=1))
    f = f.merge(mapa[["cod_cliente", "entidade"]], on="cod_cliente", how="inner")
    out = f.pivot_table(index=["entidade", "periodo"], columns="tipo", values="valor", aggfunc="sum", fill_value=0.0)
    out = out.reindex(columns=["analise", "kit", "outros"], fill_value=0.0)
    out["total"] = out.sum(axis=1)
    return out.reset_index().rename_axis(columns=None)


def receita_por_amostra(df: pd.DataFrame, receita: str = "faturamento", amostras: str = "amostras",
                        por: list[str] | None = None) -> pd.DataFrame:
    """Razão das somas (R$/amostra) e, quando há grupo, a mediana da razão por entidade dentro do grupo.

    Só entram linhas com amostras e receita no mesmo grão, para não misturar quem só compra com quem só coleta.
    """
    d = df[(df[amostras] > 0) & (df[receita] > 0)]
    por = por or []
    g = d.groupby(por) if por else d.assign(_t="total").groupby("_t")
    out = pd.DataFrame({"linhas": g.size(), "amostras": g[amostras].sum(), "receita": g[receita].sum()})
    out["receita_por_amostra"] = out["receita"] / out["amostras"]
    if "entidade" in d and "entidade" not in por:
        por_ent = d.groupby(por + ["entidade"])[[receita, amostras]].sum() if por else \
            d.groupby("entidade")[[receita, amostras]].sum()
        razao = por_ent[receita] / por_ent[amostras]
        med = razao.groupby(level=por).median() if por else pd.Series({"total": razao.median()})
        out["mediana_por_entidade"] = med
        out["entidades"] = razao.groupby(level=por).size() if por else len(razao)
    return out.reset_index().drop(columns="_t", errors="ignore")


def correlacao_defasada(df: pd.DataFrame, x: str, y: str, lags=(0, 1, 2, 3), por: str | None = None,
                        centrar: bool = False) -> pd.DataFrame:
    """corr(x(t), y(t + lag)) para cada lag. Com `por`, a defasagem é dentro do grupo (série contínua por entidade)
    e `centrar` tira a média do grupo (correlação dentro da entidade, sem o efeito de tamanho do cliente)."""
    d = df.sort_values([por, "periodo"] if por else "periodo").copy()
    if centrar and por:
        d[[x, y]] = d[[x, y]] - d.groupby(por)[[x, y]].transform("mean")
    linhas = []
    for lag in lags:
        fut = d.groupby(por)[y].shift(-lag) if por else d[y].shift(-lag)
        par = pd.DataFrame({"x": d[x], "y": fut}).dropna()
        linhas.append({"lag": lag, "n": len(par),
                       "pearson": par["x"].corr(par["y"]) if len(par) > 2 else np.nan,
                       "spearman": par["x"].corr(par["y"], method="spearman") if len(par) > 2 else np.nan})
    return pd.DataFrame(linhas)


def classes_no_corte(mensal: pd.DataFrame, data_corte, p: ParametrosRecorrencia = ParametrosRecorrencia()) -> pd.DataFrame:
    return classificar_clientes(mensal, data_corte, p)


def decompor_receita(mensal: pd.DataFrame, data_corte, p: ParametrosRecorrencia = ParametrosRecorrencia()) -> pd.DataFrame:
    """Receita dos 12 meses até o corte por classe do Forecast 27 (recorrente, não recorrente ativa, churn, novo, reativado)."""
    cl = classes_no_corte(mensal, data_corte, p)
    g = cl.groupby("classe")
    out = pd.DataFrame({"clientes": g.size(), "receita_12m": g["valor_12m"].sum()})
    out["receita_mensal"] = out["receita_12m"] / p.janela_meses
    out["pct_receita"] = out["receita_12m"] / out["receita_12m"].sum()
    out["em_escopo"] = out.index.isin(CLASSES_ESCOPO)
    return out.reset_index()


def _base_cliente(mensal: pd.DataFrame, clientes, mes_corte: pd.Timestamp, alvo: pd.Timestamp,
                  base: str, janela: int) -> float:
    m = mensal[mensal["cliente"].isin(clientes)]
    if base == "mesmo_mes":
        ref = alvo - pd.DateOffset(years=1)
        if ref > mes_corte:  # horizonte > 12: cai para a média
            base = "media"
        else:
            return float(m.loc[m["periodo"] == ref, "valor"].sum())
    ini = mes_corte - pd.DateOffset(months=janela - 1)
    return float(m.loc[(m["periodo"] >= ini) & (m["periodo"] <= mes_corte), "valor"].sum() / janela)


def churn_mensal(mensal: pd.DataFrame, data_corte, meses: int = 12,
                 p: ParametrosRecorrencia = ParametrosRecorrencia()) -> float:
    """Receita mensal média perdida com quem entrou em churn em cada um dos `meses` meses até o corte
    (média dos 6 meses antes da última compra, regra do Forecast 27)."""
    fim = inicio_mes(pd.Timestamp(data_corte))
    perdas = []
    anterior = None
    for k in range(meses, -1, -1):
        corte_k = fim - pd.DateOffset(months=k) + pd.offsets.MonthEnd(0)
        if not ((mensal["periodo"] <= corte_k) & (mensal["valor"] > 0)).any():  # corte antes do histórico
            anterior = pd.Series(dtype=object)
            continue
        cl =classes_no_corte(mensal, corte_k, p).set_index("cliente")
        if anterior is not None:
            entrou = cl[(cl["classe"] == "churn") & (anterior.reindex(cl.index) != "churn")]
            perdas.append(receita_churn(mensal, entrou.reset_index(), p.meses_churn)["receita_churn_mensal"].sum()
                          if len(entrou) else 0.0)
        anterior = cl["classe"]
    return float(np.mean(perdas)) if perdas else 0.0


def componentes_forecast27(mensal: pd.DataFrame, data_corte, h: int, base: str = "media", janela: int = 12,
                           churn_acumulado: bool = False, var_mercado: dict | None = None,
                           p: ParametrosRecorrencia = ParametrosRecorrencia()) -> pd.DataFrame:
    """Componentes da aba 'Projeção Receita' calculados dos dados no corte, prontos para regra_forecast27.

    base: 'media' (média mensal dos `janela` meses até o corte, por classe) ou 'mesmo_mes' (mesmo mês do ano anterior).
    churn: perda mensal média (constante por mês, como a planilha) ou acumulada (k × perda no k-ésimo mês à frente).
    novos/reativados = 0 (D3). var_mercado: {mês do calendário: %}; ausente = 0.
    """
    corte = pd.Timestamp(data_corte)
    mes_corte = inicio_mes(corte)
    m = mensal.assign(periodo=inicio_mes(mensal["periodo"]))
    cl = classes_no_corte(m, corte, p)
    rec = cl.loc[cl["classe"] == "recorrente", "cliente"]
    nrec = cl.loc[cl["classe"] == "nao_recorrente_ativo", "cliente"]
    perda = churn_mensal(m, corte, p=p)
    meses = pd.date_range(mes_corte + pd.offsets.MonthBegin(1), periods=h, freq="MS")
    var_mercado = var_mercado or {}
    return pd.DataFrame({
        "mes": meses,
        "h": range(1, h + 1),
        "recorrente_base": [_base_cliente(m, rec, mes_corte, t, base, janela) for t in meses],
        "nao_recorrente": [_base_cliente(m, nrec, mes_corte, t, base, janela) for t in meses],
        "novos": 0.0,
        "reativados": 0.0,
        "churn": [perda * (k if churn_acumulado else 1) for k in range(1, h + 1)],
        "var_mercado": [var_mercado.get(t.month, 0.0) for t in meses],
    })


def realizado_por_corte(mensal: pd.DataFrame, data_corte, meses: pd.DatetimeIndex,
                        p: ParametrosRecorrencia = ParametrosRecorrencia()) -> pd.DataFrame:
    """Realizado total e só dos clientes em escopo no corte (recorrente + não recorrente ativo), para cada mês."""
    m = mensal.assign(periodo=inicio_mes(mensal["periodo"]))
    cl = classes_no_corte(m, data_corte, p)
    esc = set(cl.loc[cl["classe"].isin(CLASSES_ESCOPO), "cliente"])
    fut = m[m["periodo"].isin(meses)]
    return pd.DataFrame({
        "mes": meses,
        "realizado_total": fut.groupby("periodo")["valor"].sum().reindex(meses, fill_value=0.0).values,
        "realizado_escopo": fut[fut["cliente"].isin(esc)].groupby("periodo")["valor"].sum()
        .reindex(meses, fill_value=0.0).values,
    })
