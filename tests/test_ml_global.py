import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")

from src.backtest.harness import resumir, rolling_origin
from src.models.baselines import media_movel
from src.models.ml_global import ml_global, montar_base, prever, treinar

ORIGENS = ["2024-12-01", "2025-06-01"]


def _sintetico(n_series=30, n=48, seed=0):
    """Séries sazonais de níveis diferentes: metade Poisson, metade com ruído multiplicativo de 15%."""
    rng = np.random.default_rng(seed)
    per = pd.date_range("2022-01-01", periods=n, freq="MS")
    partes = []
    for i in range(n_series):
        mu = rng.uniform(5, 200) * (1 + 0.3 * np.sin(2 * np.pi * np.arange(n) / 12 + rng.uniform(0, 2 * np.pi)))
        y = rng.poisson(mu) if i % 2 else np.maximum(0, mu * (1 + 0.15 * rng.standard_normal(n)))
        partes.append(pd.DataFrame({"id": f"s{i}", "periodo": per, "y": y.astype(float),
                                    "segmento": "A" if i % 3 else "B"}))
    return pd.concat(partes, ignore_index=True)


@pytest.fixture(scope="module")
def serie():
    return _sintetico()


@pytest.fixture(scope="module")
def backtest(serie):
    return rolling_origin(serie, {"ml": ml_global, "mm": media_movel}, origens=ORIGENS, h=3)


def test_interface_e_ordem_dos_quantis(serie):
    treino = serie[serie["periodo"] <= "2025-06-01"]
    prev = ml_global(treino, 3)
    assert list(prev.columns) == ["id", "periodo", "yhat", "yhat_lo", "yhat_hi"]
    assert len(prev) == 30 * 3
    assert set(prev["periodo"]) == set(pd.date_range("2025-07-01", periods=3, freq="MS"))
    assert (prev["yhat_lo"] <= prev["yhat"]).all() and (prev["yhat"] <= prev["yhat_hi"]).all()
    assert (prev["yhat_lo"] >= 0).all() and (prev["yhat_hi"] > prev["yhat_lo"]).mean() > 0.9


def test_cobertura_do_intervalo_e_acuracia(backtest):
    r = resumir(backtest).set_index("modelo")
    assert 0.6 <= r.loc["ml", "cobertura"] <= 0.95  # p10–p90: nominal 0,80
    assert r.loc["ml", "wape"] < r.loc["mm", "wape"]
    assert set(backtest.loc[backtest["modelo"] == "ml", "horizonte"]) == {1, 2, 3}


def test_treino_estritamente_ate_a_origem(serie):
    origem = pd.Timestamp("2024-12-01")
    base, fut = montar_base(serie[serie["periodo"] <= origem], 3)
    assert base["periodo_alvo"].max() <= origem and base["periodo"].max() <= origem
    assert (fut["periodo"] == origem + pd.DateOffset(months=1)).all()
    assert set(fut["periodo_alvo"]) == set(pd.date_range("2025-01-01", periods=3, freq="MS"))


def test_sem_vazamento_alterar_futuro_nao_muda_previsao(serie, backtest):
    futuro = serie["periodo"] > pd.Timestamp(ORIGENS[0])
    alterada = serie.copy()
    alterada.loc[futuro, "y"] = alterada.loc[futuro, "y"] * 10 + 1000
    prev = rolling_origin(alterada, {"ml": ml_global}, origens=ORIGENS[:1], h=3)
    orig = backtest[(backtest["modelo"] == "ml") & (backtest["origem"] == pd.Timestamp(ORIGENS[0]))]
    cols = ["id", "periodo", "yhat", "yhat_lo", "yhat_hi"]
    pd.testing.assert_frame_equal(prev[cols].reset_index(drop=True), orig[cols].reset_index(drop=True))


def test_treinar_e_prever_em_lotes_e_em_series_fora_do_treino(serie):
    treino = serie[serie["periodo"] <= "2025-06-01"]
    modelos, x_cols = treinar(treino, 3)
    ordem = ["id", "periodo"]
    # lotes com categorias de segmento diferentes do treino: o LightGBM remapeia pelas categorias do ajuste
    pd.testing.assert_frame_equal(ml_global(treino, 3).sort_values(ordem, ignore_index=True),
                                  prever(modelos, x_cols, treino, 3, lote=7).sort_values(ordem, ignore_index=True))
    nova = treino[treino["id"] == "s1"].tail(13).assign(id="nova")   # fora do treino, só 13 meses de histórico
    p = prever(modelos, x_cols, nova, 3)
    assert set(p["id"]) == {"nova"} and len(p) == 3 and (p["yhat_lo"] <= p["yhat"]).all()
