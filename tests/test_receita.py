import pandas as pd
import pytest

from src.features.receita import (componentes_forecast27, correlacao_defasada, decompor_receita,
                                  realizado_por_corte, receita_por_amostra, receita_por_tipo, tipo_cfop)
from src.models.baselines import regra_forecast27

CORTE = pd.Timestamp("2026-08-31")
MESES = pd.date_range("2025-09-01", "2026-08-01", freq="MS")


def _mensal():
    rec = pd.DataFrame({"cliente": "R", "periodo": MESES, "valor": 1200.0})           # 12 meses: recorrente
    nrec = pd.DataFrame({"cliente": "N", "periodo": MESES[[3, 11]], "valor": 600.0})   # 2 meses: não recorrente
    churn = pd.DataFrame({"cliente": "C", "periodo": MESES[:3], "valor": 300.0})       # parou em nov/25
    return pd.concat([rec, nrec, churn], ignore_index=True)


def test_tipo_cfop_pelos_tres_ultimos_digitos():
    t = tipo_cfop(pd.Series(["5933", "6102", "5949", "933"]))
    assert t.tolist() == ["analise", "kit", "outros", "analise"]


def test_receita_por_tipo_exclui_cfop_e_mapeia_entidade():
    fat = pd.DataFrame({"cod_cliente": ["A", "A", "A", "B"], "cfop": ["5933", "5102", "5922", "5933"],
                        "ano": 2026, "mes": 1, "total": ["100", "50", "999", "10"]})
    mapa = pd.DataFrame({"cod_cliente": ["A"], "entidade": ["E1"]})
    r = receita_por_tipo(fat, mapa, excluir=("922",)).set_index("entidade")
    assert r.loc["E1", ["analise", "kit", "total"]].tolist() == [100, 50, 150]


def test_receita_por_amostra_razao_das_somas_e_mediana():
    df = pd.DataFrame({"entidade": ["a", "a", "b", "c"], "seg": "x", "amostras": [10, 10, 5, 0],
                       "faturamento": [100, 300, 500, 50]})
    r = receita_por_amostra(df, por=["seg"]).iloc[0]
    assert r["receita_por_amostra"] == pytest.approx(900 / 25)
    assert r["mediana_por_entidade"] == pytest.approx((20 + 100) / 2) and r["entidades"] == 2


def test_correlacao_defasada_acha_o_lag():
    per = pd.date_range("2025-01-01", periods=12, freq="MS")
    x = pd.Series([1, 5, 2, 8, 3, 9, 1, 7, 4, 6, 2, 5], dtype=float)
    df = pd.DataFrame({"periodo": per, "kit": x, "amostras": x.shift(2).fillna(0)})
    c = correlacao_defasada(df, "kit", "amostras", lags=(0, 2)).set_index("lag")
    assert c.loc[2, "pearson"] == pytest.approx(1.0) and c.loc[0, "pearson"] < 0.9


def test_correlacao_centrada_por_entidade_tira_efeito_tamanho():
    per = pd.date_range("2025-01-01", periods=4, freq="MS")
    df = pd.concat([pd.DataFrame({"e": e, "periodo": per, "x": [1, 2, 3, 4], "y": [k + v for v in (1, 2, 3, 4)]})
                    for e, k in (("a", 0), ("b", 1000))])
    c = correlacao_defasada(df, "x", "y", lags=(0,), por="e", centrar=True)
    assert c.loc[0, "pearson"] == pytest.approx(1.0)


def test_decompor_receita_por_classe():
    d = decompor_receita(_mensal(), CORTE).set_index("classe")
    assert d.loc["recorrente", "receita_12m"] == 14400 and d.loc["nao_recorrente_ativo", "receita_12m"] == 1200
    assert d.loc["churn", "clientes"] == 1 and not d.loc["churn", "em_escopo"]
    assert d["pct_receita"].sum() == pytest.approx(1.0)


def test_componentes_forecast27_media_e_d3():
    c = componentes_forecast27(_mensal(), CORTE, h=3, var_mercado={9: -0.03})
    assert c["recorrente_base"].tolist() == [1200.0] * 3 and c["nao_recorrente"].iloc[0] == pytest.approx(100.0)
    assert (c["novos"] == 0).all() and (c["reativados"] == 0).all()
    assert c["var_mercado"].tolist() == [-0.03, 0.0, 0.0]
    # C (última compra nov/25) e N (dez/25, volta em ago/26) entram em churn: 900/6 + 600/6 em 12 meses
    assert c["churn"].iloc[0] == pytest.approx(250 / 12)
    acum = componentes_forecast27(_mensal(), CORTE, h=3, churn_acumulado=True)
    assert acum["churn"].iloc[2] == pytest.approx(3 * 250 / 12)
    r = regra_forecast27(c)
    assert r["total"].iloc[1] == pytest.approx(1300 - 250 / 12)


def test_componentes_mesmo_mes_do_ano_anterior():
    c = componentes_forecast27(_mensal(), CORTE, h=1, base="mesmo_mes")
    assert c["recorrente_base"].iloc[0] == 1200.0 and c["nao_recorrente"].iloc[0] == 0.0


def test_realizado_em_escopo_ignora_novos():
    m = _mensal()
    fut = pd.DataFrame({"cliente": ["R", "NOVO"], "periodo": pd.to_datetime(["2026-09-01"] * 2), "valor": [1000, 500]})
    r = realizado_por_corte(pd.concat([m, fut]), CORTE, pd.DatetimeIndex(["2026-09-01"])).iloc[0]
    assert r["realizado_total"] == 1500 and r["realizado_escopo"] == 1000
