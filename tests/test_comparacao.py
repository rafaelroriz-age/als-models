import numpy as np
import pandas as pd

from src.backtest.comparacao import TODOS, avaliar_g3, ids_ativos, resumo_g3, rotular_segmento, tabela_comparativa
from src.backtest.harness import rolling_origin
from src.models.baselines import ingenuo_sazonal, media_movel


def _serie():
    per = pd.date_range("2020-01-01", periods=48, freq="MS")
    rng = np.random.default_rng(0)
    partes = []
    for i, seg in [("a", "Mining"), ("b", "Mining"), ("c", None), ("morto", "-")]:
        y = 10 + 5 * np.sin(2 * np.pi * per.month.to_numpy() / 12) + rng.normal(0, 0.5, len(per))
        if i == "morto":
            y[:] = 0
        partes.append(pd.DataFrame({"id": i, "periodo": per, "y": y, "segmento": seg}))
    s = pd.concat(partes, ignore_index=True)
    s["segmento"] = rotular_segmento(s["segmento"])
    return s


def _oraculo(serie):
    def f(treino, h):
        fut = pd.DataFrame({"id": treino["id"].unique()}).merge(
            pd.DataFrame({"periodo": pd.date_range(treino["periodo"].max() + pd.offsets.MonthBegin(1), periods=h,
                                                   freq="MS")}), how="cross")
        out = fut.merge(serie[["id", "periodo", "y"]], on=["id", "periodo"], how="left").rename(columns={"y": "yhat"})
        return out.assign(yhat_lo=out["yhat"] - 1, yhat_hi=out["yhat"] + 1)
    return f


def test_rotular_segmento():
    s = rotular_segmento(pd.Series(["Mining", None, "-", " ", "--", "Consumer products."], dtype="object"))
    assert s.tolist() == ["Mining", "sem_segmento", "sem_segmento", "sem_segmento", "sem_segmento",
                          "Consumer products"]


def test_ids_ativos_so_olha_ate_a_data():
    s = _serie()
    assert set(ids_ativos(s, "2021-12-01")) == {"a", "b", "c"}


def test_g3_oraculo_bate_baselines_e_tem_cobertura():
    s = _serie()
    modelos = {"ingenuo_sazonal": ingenuo_sazonal, "media_movel_3": lambda t, h: media_movel(t, h, k=3),
               "oraculo": _oraculo(s)}
    prev = rolling_origin(s, modelos, pd.date_range("2022-06-01", periods=3, freq="2MS"), h=6).assign(nivel="cliente")
    tab = tabela_comparativa(prev)
    assert set(tab["horizonte"]) == {1, 3, 6}
    assert {TODOS, "Mining", "sem_segmento"} <= set(tab["segmento"])
    assert tab.loc[tab["modelo"] == "oraculo", "cobertura"].eq(1).all()
    assert tab.loc[tab["modelo"] != "oraculo", "cobertura"].isna().all()
    g3 = avaliar_g3(tab)
    assert set(g3["modelo"]) == {"oraculo"} and g3["bate"].all()
    r = resumo_g3(g3)
    assert r["passa_g3"].all() and (r["horizontes"] == 3).all()


def test_g3_candidato_pior_nao_passa():
    tab = pd.DataFrame({"nivel": "cliente", "segmento": TODOS, "horizonte": [1, 1, 3, 3],
                        "modelo": ["ingenuo_sazonal", "x", "ingenuo_sazonal", "x"],
                        "wape": [0.2, 0.1, 0.2, 0.3], "bias_pct": 0.0, "cobertura": np.nan})
    r = resumo_g3(avaliar_g3(tab))
    assert r.loc[0, "horizontes_ganhos"] == 1 and not r.loc[0, "passa_g3"]
