"""KPI 2 (T18): oportunidades Zoho com probabilidade alta no forecast de faturamento, somadas ou descontadas (H1).

Variantes, todas sobre o Forecast 27 calculado dos dados no corte (src/features/receita.py):
- `base`: só o Forecast 27 (sem oportunidades);
- `soma`: base + oportunidades acima do limiar (como o Power BI atual);
- `desconta_escopo`: base + só as oportunidades de entidades fora do escopo (novos, reativados, churn); as de clientes
  recorrentes/ativos já estão na base e saem;
- `desconta_parcial`: base + oportunidade de cada entidade menos o que a base já projeta para ela (piso zero).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.receita import CLASSES_ESCOPO, classes_no_corte, componentes_forecast27
from src.features.regras import ParametrosRecorrencia, inicio_mes
from src.models.baselines import regra_forecast27

VARIANTES = ("base", "soma", "desconta_escopo", "desconta_parcial")


def oportunidades_conhecidas(deals: pd.DataFrame, corte, alvo, limiar: float = 80, estrito: bool = True,
                             ratear: bool = False) -> pd.DataFrame:
    """entidade → valor das oportunidades vivas no corte, com fechamento previsto no mês `alvo` e probabilidade > limiar.

    Vivas no corte: criadas até o corte, não perdidas e ainda não fechadas (ou fechadas depois do corte). Com
    `ratear`, o valor entra dividido pelo prazo em meses nos meses de vigência (contrato), senão inteiro no mês previsto.
    Entrada: entidade, estagio, probabilidade, valor, prazo_meses, data_criacao, data_fechamento_prevista, data_fechamento_real.
    """
    corte, alvo = pd.Timestamp(corte), inicio_mes(pd.Timestamp(alvo))
    d = deals.dropna(subset=["entidade", "data_fechamento_prevista"]).copy()
    prob = pd.to_numeric(d["probabilidade"], errors="coerce")
    d = d[(prob > limiar) if estrito else (prob >= limiar)]
    real = pd.to_datetime(d["data_fechamento_real"])
    vivo = (pd.to_datetime(d["data_criacao"]) <= corte + pd.Timedelta(days=1)) & d["estagio"].ne("Closed Lost") \
        & (real.isna() | (real > corte))
    d = d[vivo].copy()
    ini = inicio_mes(pd.to_datetime(d["data_fechamento_prevista"]))
    valor = pd.to_numeric(d["valor"], errors="coerce").fillna(0.0)
    if ratear:
        prazo = pd.to_numeric(d["prazo_meses"], errors="coerce").fillna(1).clip(lower=1)
        fim = pd.Series([i + pd.DateOffset(months=int(m) - 1) for i, m in zip(ini, prazo)], index=d.index)
        vig = (ini <= alvo) & (alvo <= fim)
        d, valor = d[vig], (valor / prazo)[vig]
    else:
        vig = ini == alvo
        d, valor = d[vig], valor[vig]
    return valor.groupby(d["entidade"]).sum().rename("opp").reset_index()


def previsoes_corte(mensal: pd.DataFrame, deals: pd.DataFrame, corte, h: int, limiar: float = 80, estrito: bool = True,
                    ratear: bool = False, p: ParametrosRecorrencia = ParametrosRecorrencia(),
                    cenarios: dict | None = None) -> pd.DataFrame:
    """Uma linha por mês-alvo (1..h) × variante, com a previsão total de faturamento.

    `cenarios` ({nome: kwargs de oportunidades_conhecidas}) reaproveita o Forecast 27 do corte e devolve a coluna `cenario`.
    """
    cen = cenarios or {"unico": dict(limiar=limiar, estrito=estrito, ratear=ratear)}
    corte = pd.Timestamp(corte)
    m = mensal[mensal["periodo"] <= corte]
    comp = componentes_forecast27(m, corte, h, p=p)
    total = regra_forecast27(comp)["total"].to_numpy()
    cl = classes_no_corte(m, corte, p).set_index("cliente")
    escopo = set(cl.index[cl["classe"].isin(CLASSES_ESCOPO)])
    mes_corte = inicio_mes(corte)
    ini = mes_corte - pd.DateOffset(months=p.janela_meses - 1)
    ult = m[(m["periodo"] >= ini) & (m["periodo"] <= mes_corte)]
    proj_ent = ult.groupby("cliente")["valor"].sum() / p.janela_meses  # o que a base projeta por entidade em escopo
    proj_ent = proj_ent[proj_ent.index.isin(escopo)]
    linhas = []
    for k, mes in enumerate(comp["mes"]):
        for cnome, kw in cen.items():
            o = oportunidades_conhecidas(deals, corte, mes, **kw)
            o["na_base"] = o["entidade"].isin(escopo)
            o["proj"] = o["entidade"].map(proj_ent).fillna(0.0)
            v = {"base": total[k], "soma": total[k] + o["opp"].sum(),
                 "desconta_escopo": total[k] + o.loc[~o["na_base"], "opp"].sum(),
                 "desconta_parcial": total[k] + (o["opp"] - o["proj"]).clip(lower=0).sum()}
            for nome in VARIANTES:
                linhas.append({"cenario": cnome, "corte": mes_corte, "h": k + 1, "mes": mes, "variante": nome,
                               "previsto": v[nome], "opp_total": o["opp"].sum(),
                               "opp_em_escopo": o.loc[o["na_base"], "opp"].sum(),
                               "opp_ja_projetada": float(np.minimum(o["opp"], o["proj"]).sum())})
    return pd.DataFrame(linhas)


def metricas(prev: pd.DataFrame, real: pd.Series) -> pd.DataFrame:
    """WAPE, viés (soma(prev − real)/soma(real)) e erro absoluto médio por variante e horizonte (`real` indexado por mês)."""
    d = prev.assign(real=prev["mes"].map(real))
    d["erro"] = d["previsto"] - d["real"]

    def agg(g):
        return pd.Series({"n": len(g), "wape": g["erro"].abs().sum() / g["real"].sum(),
                          "vies": g["erro"].sum() / g["real"].sum(), "mae": g["erro"].abs().mean()})

    por_h = d.groupby(["variante", "h"]).apply(agg).reset_index()
    geral = d.groupby("variante").apply(agg).reset_index().assign(h="todos")
    return pd.concat([por_h.astype({"h": object}), geral], ignore_index=True)


def risco_dupla_contagem(prev: pd.DataFrame, fat_ganhas: pd.DataFrame | None = None) -> dict:
    """Parte das oportunidades de entidades que a base já projeta e quanto dela a base já cobre em valor.

    `fat_ganhas`, se dado (entidade, valor_oportunidade, faturamento_mes_fechamento), mede quanto das oportunidades ganhas
    aparece como faturamento no mês de fechamento.
    """
    s = prev[prev["variante"] == "soma"]
    tot = float(s["opp_total"].sum())
    out = {"opp_total": round(tot, 2),
           "pct_em_escopo": round(100 * float(s["opp_em_escopo"].sum()) / tot, 2) if tot else None,
           "pct_ja_projetada": round(100 * float(s["opp_ja_projetada"].sum()) / tot, 2) if tot else None}
    if fat_ganhas is not None and len(fat_ganhas):
        out["ganhas_n"] = int(len(fat_ganhas))
        out["pct_ganhas_com_faturamento_no_mes"] = round(
            100 * float((fat_ganhas["faturamento_mes_fechamento"] > 0).mean()), 2)
    return out
