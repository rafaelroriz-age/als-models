import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src.features.series import SEM_HISTORICO, ParametrosSeries, gerar_features


def _sintetico(n=30, seed=0):
    rng = np.random.default_rng(seed)
    meses = pd.date_range("2024-01-01", periods=n, freq="MS")
    linhas = []
    for ent, seg, ini in [("A", "Cana", 0), ("B", "Industria", 4), ("C", "Cana", 10)]:
        for m in meses[ini:]:
            linhas.append({"entidade": ent, "periodo": m + pd.Timedelta(days=9), "valor": float(rng.integers(2, 50)),
                           "segmento": seg})
    return pd.DataFrame(linhas)


def _linha(f, ent, mes):
    return f[(f["entidade"] == ent) & (f["periodo"] == pd.Timestamp(mes))].iloc[0]


def test_lags_e_medias_moveis_valores_conhecidos():
    df = pd.DataFrame({"entidade": "A", "periodo": pd.date_range("2025-01-01", periods=14, freq="MS"),
                       "valor": np.arange(1.0, 15.0)})
    f = gerar_features(df, p=ParametrosSeries(incluir_status=False))
    r = _linha(f, "A", "2026-02-01")  # valor 14; anteriores: 13, 12, 11 ... 2
    assert (r["lag_1"], r["lag_2"], r["lag_3"], r["lag_12"]) == (13, 12, 11, 2)
    assert r["mm_3"] == pytest.approx((13 + 12 + 11) / 3)
    assert r["mm_12"] == pytest.approx(np.mean(range(2, 14)))
    assert r["tendencia_6"] == pytest.approx(1.0)  # série linear de inclinação 1
    assert np.isnan(_linha(f, "A", "2025-01-01")["lag_1"])


def test_janela_completa_parametrizavel():
    df = pd.DataFrame({"entidade": "A", "periodo": pd.date_range("2025-01-01", periods=5, freq="MS"),
                       "valor": [10.0, 20, 30, 40, 50]})
    cheia = gerar_features(df, p=ParametrosSeries(incluir_status=False))
    parcial = gerar_features(df, p=ParametrosSeries(incluir_status=False, janela_completa=False))
    assert np.isnan(_linha(cheia, "A", "2025-03-01")["mm_3"])          # só 2 meses anteriores
    assert _linha(parcial, "A", "2025-03-01")["mm_3"] == pytest.approx(15.0)


def test_sazonalidade_segmento_e_meses_sem_registro_zerados():
    df = pd.DataFrame({"entidade": "A", "periodo": pd.to_datetime(["2025-01-15", "2025-04-02"]),
                       "valor": [5.0, 7.0], "segmento": ["Cana", "Cana"]})
    f = gerar_features(df, p=ParametrosSeries(incluir_status=False))
    assert len(f) == 4 and list(f["valor"]) == [5, 0, 0, 7]
    assert (f["segmento"] == "Cana").all()
    r = _linha(f, "A", "2025-03-01")
    assert (r["mes_sin"], r["mes_cos"]) == (pytest.approx(1.0), pytest.approx(0.0, abs=1e-12))


def test_status_usa_regras_e_marca_sem_historico():
    meses = pd.date_range("2025-01-01", periods=12, freq="MS")
    df = pd.DataFrame({"entidade": "A", "periodo": meses, "valor": 1000.0})
    f = gerar_features(df, ate="2026-06-01")
    assert _linha(f, "A", "2025-01-01")["status"] == SEM_HISTORICO
    assert _linha(f, "A", "2026-01-01")["status"] == "recorrente"      # 12 compras seguidas até dez/2025
    assert _linha(f, "A", "2026-06-01")["status"] == "nao_recorrente_ativo"  # última compra em dez, 151 dias antes


def test_status_desligavel_e_parametrizavel():
    df = _sintetico()
    assert "status" not in gerar_features(df, p=ParametrosSeries(incluir_status=False)).columns
    assert "status" in gerar_features(df).columns


def test_vazamento_alterar_valor_futuro_nao_muda_feature_do_mes():
    df = _sintetico()
    base = gerar_features(df)
    alvo = pd.Timestamp("2025-06-01")
    cols = [c for c in base.columns if c not in ("valor",)]

    mexido = df.copy()
    mexido.loc[(mexido["entidade"] == "A") & (inicio := mexido["periodo"].dt.to_period("M").dt.to_timestamp()
                                               ).eq(alvo), "valor"] += 1e6
    novo = gerar_features(mexido)
    ate_alvo = base["periodo"] <= alvo
    # features de todos os meses ≤ alvo (inclusive o próprio mês alterado, que é só o alvo) não mudam
    assert_frame_equal(base.loc[ate_alvo, cols], novo.loc[ate_alvo, cols])
    # mas o futuro enxerga a mudança
    assert not base.loc[~ate_alvo, ["lag_1", "mm_3"]].equals(novo.loc[~ate_alvo, ["lag_1", "mm_3"]])


def test_vazamento_cortar_historico_antes_do_mes_reproduz_a_feature():
    df = _sintetico()
    alvo = pd.Timestamp("2025-06-01")
    cheio = gerar_features(df)
    corte = df[df["periodo"] < alvo]
    truncado = gerar_features(corte, ate=alvo)  # sem nenhum dado de alvo em diante
    cols = [c for c in cheio.columns if c != "valor"]
    a = cheio[cheio["periodo"] == alvo].set_index("entidade")[cols[1:]].sort_index()
    b = truncado[truncado["periodo"] == alvo].set_index("entidade")[cols[1:]].sort_index()
    assert_frame_equal(a.drop(columns="periodo"), b.drop(columns="periodo"))
