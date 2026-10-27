import numpy as np
import pandas as pd
import pytest

from conftest import FORECAST27, exige
from src.backtest.harness import agregar_total, metricas, resumir, rolling_origin
from src.gates.checks import avaliar_g0, avaliar_g1
from src.models.baselines import ingenuo_sazonal, ler_forecast27, media_movel, regra_forecast27


def _serie(n=36, ids=("a", "b")):
    per = pd.date_range("2023-01-01", periods=n, freq="MS")
    return pd.concat([pd.DataFrame({"id": i, "periodo": per, "y": 100 + 10 * np.sin(np.arange(n) * 2 * np.pi / 12)})
                      for i in ids], ignore_index=True)


def test_ingenuo_sazonal_perfeito_em_serie_periodica():
    s = _serie()
    prev = rolling_origin(s, {"sn": ingenuo_sazonal}, origens=["2024-12-01", "2025-03-01"], h=3)
    assert set(prev["horizonte"]) == {1, 2, 3}
    assert resumir(prev).loc[0, "wape"] == pytest.approx(0, abs=1e-9)


def test_media_movel_e_agregado():
    s = _serie()
    prev = rolling_origin(s, {"mm": media_movel}, origens=["2024-12-01"], h=2)
    tot = agregar_total(prev)
    assert len(tot) == 2 and (tot["id"] == "TOTAL").all()


def test_metricas_conhecidas():
    m = metricas(pd.Series([100, 100]), pd.Series([110, 80]), pd.Series([105, 90]), pd.Series([120, 120]))
    assert m["wape"] == pytest.approx(0.15) and m["bias_pct"] == pytest.approx(-0.05) and m["cobertura"] == 0.5


def test_min_treino_descarta_series_curtas():
    s = _serie(n=10)
    assert rolling_origin(s, {"sn": ingenuo_sazonal}, origens=["2023-08-01"], h=1, min_treino=12).empty


@exige(FORECAST27)
def test_replica_forecast27():
    f = ler_forecast27(FORECAST27)
    r = regra_forecast27(f)
    dif = (r["total_ajustado"] - r["total_ajustado_planilha"]).round(2)
    assert (dif.iloc[:6] == 0).all()
    # Março: a planilha soma de novo metade dos novos de setembro (C8 = … + E2/2)
    assert r["recorrente_planilha"].iloc[6] - r["recorrente"].iloc[6] == pytest.approx(f["novos"].iloc[0] / 2)


def test_gates():
    perfis = [{"tabela": "bronze_s360.amostra", "n_linhas": 10, "nulos_pct": {"id": 0, "cliente_id": 0, "data_coleta": 50},
               "datas": {"data_coleta": ["2015-01-01", "2026-01-01"]}}]
    r = pd.DataFrame(avaliar_g0(perfis, hoje=pd.Timestamp("2026-10-27")))
    assert not r.loc[r["alvo"] == "bronze_s360.amostra.data_coleta", "ok"].iloc[0]
    assert not r.loc[r["alvo"] == "silver_zoho.accounts", "ok"].iloc[0]
    base = pd.DataFrame({"cliente": ["a", "a", "a"], "periodo": pd.to_datetime(["2026-01-01", "2026-03-01", "2026-03-01"]),
                         "valor": [1, 2, -1]})
    g1 = pd.DataFrame(avaliar_g1(base, ["cliente", "periodo"], "valor")).set_index("checagem")["ok"]
    assert not g1["chave_unica"] and not g1["nao_negativo"] and not g1["meses_continuos"]
