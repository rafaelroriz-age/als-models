import numpy as np
import pandas as pd
import pytest

from src.models.potencial import ParametrosPotencial, benchmark, potencial_intervalo, taxas_cliente
from src.serving import saidas
from src.serving.contrato import aprovado, validar

CORTE = pd.Timestamp("2026-10-01")


@pytest.fixture
def atributos():
    return pd.DataFrame({"entidade_nome": ["Cliente A", "Cliente B", None],
                         "cliente_id": [None, None, "a"], "segmento": ["Mining", None, "Mining"]},
                        index=pd.Index(["a", "b", "e1"]))


def _hist(ids, ate="2026-09-01", n=24, v=10.0):
    per = pd.date_range(end=ate, periods=n, freq="MS")
    return pd.DataFrame([(i, p, v) for i in ids for p in per], columns=["id", "periodo", "y"])


def _prev(ids, h=6, p50=10.0):
    per = pd.date_range(CORTE, periods=h, freq="MS")
    return pd.DataFrame([(i, p, p50, p50 * 0.5, p50 * 1.5) for i in ids for p in per],
                        columns=["id", "periodo", "yhat", "yhat_lo", "yhat_hi"])


def test_grade_mensal_completa_com_zero_so_depois_do_primeiro_mes():
    df = pd.DataFrame({"id": ["x", "x", "y"], "periodo": pd.to_datetime(["2026-01-15", "2026-04-01", "2026-03-01"]),
                       "y": [1.0, 2.0, 5.0]})
    g = saidas.grade_mensal(df, "2026-02-01", "2026-05-01")
    gx, gy = g[g["id"] == "x"], g[g["id"] == "y"]
    assert gx["periodo"].min() == pd.Timestamp("2026-02-01") and gx["y"].tolist() == [0, 0, 2, 0]
    assert gy["periodo"].min() == pd.Timestamp("2026-03-01") and gy["y"].tolist() == [5, 0, 0]


def test_forecast_consumo_no_contrato(atributos):
    pot = pd.DataFrame({"id": ["a", "b"], "potencial": [240.0, 120.0], "potencial_p10": [120.0, 60.0],
                        "potencial_p90": [360.0, 240.0]})
    fc = saidas.forecast_consumo("cliente", _hist(["a", "b"]), _prev(["a", "b"]), CORTE, "lgbm|abc", atributos, pot)
    res = validar("forecast_consumo", fc)
    assert aprovado(res), [r for r in res if not r["ok"]]
    assert len(fc) == 2 * (24 + 6)
    a = fc[fc["entidade_id"] == "a"]
    assert a["potencial"].eq(20.0).all() and (a["entidade_nome"] == "Cliente A").all()
    assert (fc.loc[fc["entidade_id"] == "b", "segmento"] == "sem_segmento").all()
    assert fc.loc[fc["periodo"] >= CORTE, "realizado"].isna().all()


def test_segmento_bottom_up_soma_p50_e_usa_largura_do_direto():
    prev = _prev(["a", "b"])
    seg_de = pd.Series({"a": "Mining", "b": "Mining"})
    direto = _prev(["Mining"], p50=40.0).assign(yhat_lo=30.0, yhat_hi=60.0)
    s = saidas.segmento_bottom_up(prev, seg_de, direto)
    assert s["yhat"].eq(20.0).all()
    assert s["yhat_lo"].eq(20.0 * 0.75).all() and s["yhat_hi"].eq(20.0 * 1.5).all()
    soma = saidas.segmento_bottom_up(prev, seg_de)
    assert soma["yhat_lo"].eq(10.0).all() and soma["yhat_hi"].eq(30.0).all()


def test_pct_achieved_d6(atributos):
    t = pd.DataFrame({"id": ["a", "b"], "realizado_12m": [50.0, 10.0], "potencial_12m": [100.0, 0.0],
                      "porte": ["1-5", None], "n_equip": [3, 1]})
    out = saidas.pct_achieved("cliente", t, CORTE, atributos)
    assert aprovado(validar("pct_achieved", out))
    assert out["pct_achieved"].iloc[0] == 0.5 and np.isnan(out["pct_achieved"].iloc[1])


def test_alertas_queda_e_churn_no_contrato(atributos):
    per = pd.date_range("2024-09-01", "2026-09-01", freq="MS")
    m = pd.DataFrame({"id": "a", "periodo": per, "y": 10.0})
    m.loc[m["periodo"] == "2026-09-01", "y"] = 7.9          # 21% abaixo de set/25: alerta
    m = pd.concat([m, m.assign(id="b", y=lambda d: np.where(d["periodo"] == "2026-09-01", 8.0, 10.0))])  # 20%: não
    q = saidas.alertas_queda(m, "2026-09-01", atributos)
    assert q["entidade_id"].tolist() == ["a"] and q["variacao_pct"].iloc[0] == pytest.approx(0.21)

    col = pd.DataFrame({"id": ["e1"] * 4 + ["e2"] * 4 + ["e3"] * 2,
                        "periodo": pd.to_datetime(["2026-03-01", "2026-04-01", "2026-05-01", "2026-06-01",
                                                   "2026-06-01", "2026-07-01", "2026-08-01", "2026-09-01",
                                                   "2026-01-01", "2026-02-01"]), "y": 1.0})
    ch = saidas.alertas_churn(col, CORTE, atributos)
    assert ch["entidade_id"].tolist() == ["e1"]                  # e2 em dia; e3 com poucas coletas
    assert ch["valor_base"].iloc[0] == pytest.approx(730.0) and ch["cliente_id"].iloc[0] == "a"
    alertas = pd.concat([q, ch], ignore_index=True)
    res = validar("alertas", alertas)
    assert aprovado(res), [r for r in res if not r["ok"]]


def test_backtest_metricas_no_contrato():
    tab = pd.DataFrame({"nivel": "cliente", "segmento": ["TODOS", "Mining"], "modelo": "lgbm", "horizonte": [1, 1],
                        "n": [10, 5], "wape": [0.2, 0.3], "mae": 1.0, "bias_pct": 0.0, "smape": 0.1,
                        "cobertura": [0.8, np.nan]})
    out = saidas.backtest_metricas(tab, "consumo_real", "2026-03-01", "lgbm|abc")
    assert aprovado(validar("backtest_metricas", out)) and out["segmento"].tolist() == ["todos", "Mining"]


def test_potencial_intervalo_contem_o_central():
    ents = [f"c{i}" for i in range(12)]
    frota = pd.DataFrame({"entidade": ents, "familia": "A", "n_equip": 10})
    real = pd.DataFrame({"entidade": ents, "familia": "A", "amostras_12m": np.arange(1, 13) * 10.0})
    seg = pd.DataFrame({"entidade": ents, "segmento": "cana"})
    p = ParametrosPotencial(min_clientes=5)
    t = taxas_cliente(frota, real, seg, p)
    cli, linhas = potencial_intervalo(t, p, n_boot=50)
    assert (cli["potencial_p10"] <= cli["potencial"]).all() and (cli["potencial"] <= cli["potencial_p90"]).all()
    assert (cli["potencial_p90"] > cli["potencial_p10"]).all()
    central = benchmark(t, p)["taxa_bench"].iloc[0] * 10
    assert cli["potencial"].iloc[0] == pytest.approx(central)
    assert {"taxa_bench_p10", "taxa_bench_p90"} <= set(linhas.columns)
