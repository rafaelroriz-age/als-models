import numpy as np
import pandas as pd
import pytest

from src.backtest.snapshot import (convergencia, erro_por, gravar_snapshot, ler_snapshots, montar_snapshot,
                                   reconstruir, versao_dados)
from src.models.baselines import ingenuo_sazonal, media_movel


def _serie(n=30):
    per = pd.date_range("2023-01-01", periods=n, freq="MS")
    base = 100 + 10 * np.sin(np.arange(n) * 2 * np.pi / 12)
    return pd.concat([
        pd.DataFrame({"id": "a", "segmento": "ALS", "periodo": per, "y": base}),
        pd.DataFrame({"id": "b", "segmento": "LS", "periodo": per, "y": base * 2}),
    ], ignore_index=True)


def test_versao_dados_estavel_e_sensivel():
    s = _serie()
    assert versao_dados(s) == versao_dados(s.sample(frac=1, random_state=1))
    s2 = s.copy()
    s2.loc[0, "y"] += 1
    assert versao_dados(s) != versao_dados(s2)


def test_reconstrucao_nao_ve_o_futuro():
    s = _serie()
    vistos = []

    def espiao(treino, h):
        vistos.append(treino["periodo"].max())
        return media_movel(treino, h)

    snap = reconstruir(s, {"esp": espiao}, ["2025-03-15"], h=2)
    # em 15/mar/2025 o último mês fechado é fev/2025
    assert vistos == [pd.Timestamp("2025-02-01")]
    assert set(snap["horizonte"]) == {0, 1} or snap["periodo"].min() > pd.Timestamp("2025-02-01")
    assert snap["periodo"].min() == pd.Timestamp("2025-03-01")


def test_disponivel_em_atrasa_dados():
    s = _serie()
    s["disponivel_em"] = s["periodo"] + pd.DateOffset(months=2)  # chega com 2 meses de atraso
    vistos = []

    def espiao(treino, h):
        vistos.append(treino["periodo"].max())
        return media_movel(treino, h)

    reconstruir(s, {"esp": espiao}, ["2025-03-15"], h=1)
    assert vistos == [pd.Timestamp("2025-01-01")]


def test_snapshot_ida_e_volta(tmp_path):
    s = _serie()
    snap = reconstruir(s, {"sn": ingenuo_sazonal}, ["2025-01-31", "2025-02-28"], h=3, versao_modelo="v1")
    for c, g in snap.groupby("corte"):
        gravar_snapshot(g, tmp_path)
    lido = ler_snapshots(tmp_path)
    assert len(lido) == len(snap)
    assert set(lido["versao_modelo"]) == {"v1"}
    assert lido["versao_dados"].nunique() == 2
    with pytest.raises(ValueError):
        gravar_snapshot(snap, tmp_path)


def test_erro_por_mes_segmento_cliente():
    s = _serie()
    snap = reconstruir(s, {"sn": ingenuo_sazonal}, ["2024-12-31"], h=3)
    # série periódica: sazonal ingênuo perfeito
    for por in (["periodo"], ["segmento"], ["id"]):
        r = erro_por(snap, s, por)
        assert (r["wape"].abs() < 1e-9).all() and (r["mape"].abs() < 1e-9).all()
    assert len(erro_por(snap, s, ["periodo"])) == 3

    # viés conhecido: +10% em tudo
    ruim = snap.assign(yhat=snap["yhat"] * 1.1)
    r = erro_por(ruim, s, ["segmento"])
    assert r["wape"].tolist() == pytest.approx([0.1, 0.1])
    assert erro_por(ruim, s, ["periodo"], horizonte=1)["n"].tolist() == [2]


def test_convergencia_ao_longo_do_mes():
    s = _serie()
    alvo = pd.Timestamp("2025-03-01")
    real = s[s["periodo"] == alvo].set_index("id")["y"]
    snaps = []
    # quanto mais perto do fim do mês, menor o erro injetado
    for corte, ruido in [("2025-03-05", 0.30), ("2025-03-20", 0.10), ("2025-03-31", 0.0)]:
        prev = pd.DataFrame({"id": real.index, "periodo": alvo, "yhat": real.values * (1 + ruido)})
        snaps.append(montar_snapshot(prev, corte, "m", "v", "d"))
    conv = convergencia(pd.concat(snaps), s)
    assert conv["dias_para_fim"].tolist() == [0, 11, 26]
    assert conv["wape"].tolist() == pytest.approx([0.0, 0.10, 0.30])
    # corte posterior ao mês-alvo é descartado
    tarde = montar_snapshot(pd.DataFrame({"id": ["a"], "periodo": alvo, "yhat": [1.0]}), "2025-04-02", "m", "v", "d")
    assert len(convergencia(tarde, s)) == 0
