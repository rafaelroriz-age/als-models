import numpy as np
import pandas as pd
import pytest

pytest.importorskip("statsmodels")

from src.backtest.harness import rolling_origin
from src.models import estatisticos as est
from src.models.baselines import media_movel


def _serie(valores, id_="A", inicio="2022-01-01"):
    p = pd.date_range(inicio, periods=len(valores), freq="MS")
    return pd.DataFrame({"id": id_, "periodo": p, "y": np.asarray(valores, dtype=float)})


def _sazonal(n=36):
    t = np.arange(n)
    return 100 + 20 * np.sin(2 * np.pi * t / 12) + 0.5 * t


def _intermitente(n=36):
    y = np.zeros(n)
    y[::4] = [5, 8, 6, 7, 9, 5, 6, 8, 7][: len(y[::4])]
    return y


def _base():
    return pd.concat([_serie(_sazonal(), "sazonal"), _serie(_intermitente(), "interm"),
                      _serie([10, 12, 11, 13, 12], "curta")], ignore_index=True)


@pytest.mark.parametrize("nome", list(est.MODELOS))
def test_interface_e_nao_negativo(nome):
    prev = est.MODELOS[nome](_base(), 3)
    assert list(prev.columns) == ["id", "periodo", "yhat"]
    assert len(prev) == 3 * 3
    assert prev["yhat"].notna().all() and (prev["yhat"] >= 0).all()
    assert prev.groupby("id")["periodo"].min().eq(pd.Timestamp("2025-01-01")).loc[["sazonal", "interm"]].all()


def test_modelos_rodam_no_rolling_origin():
    serie = pd.concat([_serie(_sazonal(), "sazonal"), _serie(_intermitente(), "interm")], ignore_index=True)
    prev = rolling_origin(serie, {**est.MODELOS, "mm": media_movel}, ["2024-06-01", "2024-09-01"], h=3, min_treino=12)
    assert set(prev["modelo"]) == {*est.MODELOS, "mm"}
    assert prev["yhat"].notna().all()
    # 2 origens × 2 ids × 3 horizontes por modelo
    assert (prev.groupby("modelo").size() == 12).all()


def test_ets_e_theta_seguem_a_sazonalidade():
    serie = _serie(_sazonal(), "s")
    treino = serie.iloc[:-6]
    real = serie["y"].iloc[-6:].to_numpy()
    erro_mm = np.abs(media_movel(treino, 6)["yhat"].to_numpy() - real).mean()
    for f in (est.ets, est.theta):
        assert np.abs(f(treino, 6)["yhat"].to_numpy() - real).mean() < erro_mm


def test_intermitentes_entre_zero_e_pico():
    y = _intermitente()
    for f in (est.croston, est.sba, est.tsb):
        yhat = f(_serie(y), 3)["yhat"]
        assert 0 < yhat.iloc[0] < y.max()
    sba = est.sba(_serie(y), 1)["yhat"].iloc[0]
    assert sba < est.croston(_serie(y), 1)["yhat"].iloc[0]


def test_serie_zerada_preve_zero():
    for f in (est.croston, est.sba, est.tsb):
        assert (f(_serie(np.zeros(12)), 3)["yhat"] == 0).all()


def test_serie_curta_degrada_para_fallback_sem_erro():
    curta = _serie([10, 12, 11, 13, 12], "curta")
    esperado = media_movel(curta, 3)["yhat"].to_numpy()
    for f in (est.ets, est.theta):
        prev = f(curta, 3)
        np.testing.assert_allclose(prev["yhat"], esperado)
    um_ponto = _serie([7.0], "um")
    for f in est.MODELOS.values():
        assert f(um_ponto, 2)["yhat"].notna().all()


def test_falha_do_ajuste_degrada_para_fallback(monkeypatch):
    def quebra(*a, **k):
        raise RuntimeError("não convergiu")

    monkeypatch.setattr(est, "_ets", quebra)
    serie = _serie(_sazonal(), "s")
    np.testing.assert_allclose(est.ets(serie, 3)["yhat"], media_movel(serie, 3)["yhat"])
