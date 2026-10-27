import numpy as np
import pandas as pd
import pytest

from src.models.hierarquia import (FOLHA, agregar, bottom_up, proporcoes_historicas, top_down,
                                   verificar_coerencia)

ATTR = pd.DataFrame([
    ("C1", "E1", "K1", "Escavadeira", "Mineração", "Mining"),
    ("C1", "E1", "K2", "Escavadeira", "Mineração", "Mining"),
    ("C1", "E2", "K3", "Caminhão", "Mineração", "Mining"),
    ("C2", "E3", "K4", "Trator", "Agro", "Agro"),
    ("C2", "E3", "K5", "Trator", "Agro", "Agro"),
    ("C3", "E4", "K6", "Caminhão", "Frota", "Transport"),
], columns=FOLHA + ["tipo_equipamento", "setor", "segmento"])


def _hist(meses=12, seed=0):
    rng = np.random.default_rng(seed)
    per = pd.date_range("2025-01-01", periods=meses, freq="MS")
    linhas = [(*f, p, float(rng.integers(0, 20))) for f in ATTR[FOLHA].itertuples(index=False) for p in per]
    return pd.DataFrame(linhas, columns=FOLHA + ["periodo", "y"])


def _prev_folha(h=3, seed=1):
    rng = np.random.default_rng(seed)
    per = pd.date_range("2026-01-01", periods=h, freq="MS")
    linhas = [(*f, p, float(rng.uniform(1, 30))) for f in ATTR[FOLHA].itertuples(index=False) for p in per]
    return pd.DataFrame(linhas, columns=FOLHA + ["periodo", "yhat"])


def test_bottom_up_niveis_somam():
    prev = _prev_folha()
    n = bottom_up(prev)
    assert verificar_coerencia(n)
    assert n["total"]["yhat"].sum() == pytest.approx(prev["yhat"].sum())
    c1 = n["cliente"].query("cliente == 'C1'").set_index("periodo")["yhat"]
    esperado = prev.query("cliente == 'C1'").groupby("periodo")["yhat"].sum()
    assert np.allclose(c1, esperado.reindex(c1.index))


def test_proporcoes_somam_um_por_cliente():
    p = proporcoes_historicas(_hist())
    assert np.allclose(p.groupby("cliente")["proporcao"].sum(), 1.0)
    p3 = proporcoes_historicas(_hist(), janela=3)
    assert np.allclose(p3.groupby("cliente")["proporcao"].sum(), 1.0)


def test_proporcao_cliente_sem_volume_divide_igual():
    h = _hist()
    h.loc[h["cliente"] == "C2", "y"] = 0.0
    p = proporcoes_historicas(h).query("cliente == 'C2'")
    assert np.allclose(p["proporcao"], 0.5)


def test_top_down_fecha_com_o_cliente():
    h = _hist()
    prev_cli = pd.DataFrame([(c, p, v) for c, v in [("C1", 100.0), ("C2", 40.0), ("C3", 7.0)]
                             for p in pd.date_range("2026-01-01", periods=3, freq="MS")],
                            columns=["cliente", "periodo", "yhat"])
    n = top_down(prev_cli, h)
    assert verificar_coerencia(n)
    for nivel in ("equipamento", "compartimento"):
        s = n[nivel].groupby(["cliente", "periodo"])["yhat"].sum().reset_index()
        m = s.merge(prev_cli, on=["cliente", "periodo"], suffixes=("", "_cli"))
        assert np.allclose(m["yhat"], m["yhat_cli"])


def test_top_down_cliente_sem_historico_falha():
    prev = pd.DataFrame({"cliente": ["X"], "periodo": [pd.Timestamp("2026-01-01")], "yhat": [1.0]})
    with pytest.raises(ValueError):
        top_down(prev, _hist())


def test_segmento_bate_com_soma_dos_clientes():
    prev = _prev_folha()
    cli = bottom_up(prev)["cliente"]
    seg = agregar(prev, ATTR, "segmento")
    mapa = ATTR.drop_duplicates("cliente").set_index("cliente")["segmento"]
    por_cli = cli.assign(segmento=cli["cliente"].map(mapa)).groupby(["segmento", "periodo"], as_index=False)["yhat"].sum()
    m = seg.merge(por_cli, on=["segmento", "periodo"], suffixes=("", "_cli"))
    assert len(m) == len(seg) == len(por_cli)
    assert np.allclose(m["yhat"], m["yhat_cli"])


@pytest.mark.parametrize("por", ["tipo_equipamento", "setor", "segmento", ["segmento", "tipo_equipamento"]])
def test_cortes_somam_o_total(por):
    prev = _prev_folha()
    a = agregar(prev, ATTR, por)
    assert np.allclose(a.groupby("periodo")["yhat"].sum(), prev.groupby("periodo")["yhat"].sum())


def test_agregar_rejeita_folha_sem_atributo():
    with pytest.raises(ValueError):
        agregar(_prev_folha(), ATTR.iloc[:-1], "segmento")
