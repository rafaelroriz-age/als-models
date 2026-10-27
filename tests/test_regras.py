import numpy as np
import pandas as pd
import pytest

from src.features.regras import (classificar_clientes, completar_meses, marcar_avulsas, pct_achieved,
                                 receita_churn, status_real)

CORTE = pd.Timestamp("2026-08-31")


def _mensal(cliente, meses, valor=1000.0, ultima=None):
    df = pd.DataFrame({"cliente": cliente, "periodo": pd.to_datetime(meses), "valor": valor})
    df["ultima_data"] = df["periodo"] + pd.offsets.MonthEnd(0)
    if ultima is not None:
        df.loc[df["periodo"].idxmax(), "ultima_data"] = pd.Timestamp(ultima)
    return df


def _classe(df, corte=CORTE):
    return classificar_clientes(df, corte).set_index("cliente")["classe"]


def test_recorrente_exatamente_6_meses_e_90_dias():
    meses = pd.date_range("2026-03-01", periods=6, freq="MS")  # mar..ago
    df = _mensal("A", meses, ultima=CORTE - pd.Timedelta(days=90))
    assert _classe(df)["A"] == "recorrente"


def test_seis_meses_mas_91_dias_nao_e_recorrente():
    meses = pd.date_range("2025-11-01", periods=6, freq="MS")  # nov..abr
    df = _mensal("A", meses, ultima="2026-06-01")  # 91 dias antes do corte
    assert _classe(df)["A"] == "nao_recorrente_ativo"


def test_cinco_meses_nao_e_recorrente():
    df = _mensal("A", pd.date_range("2026-04-01", periods=5, freq="MS"))
    df = pd.concat([df, _mensal("A", ["2024-01-01"])])
    assert _classe(df)["A"] == "nao_recorrente_ativo"


def test_valor_ate_1_real_nao_conta_mes():
    meses = pd.date_range("2026-03-01", periods=6, freq="MS")
    df = _mensal("A", meses)
    df.loc[0, "valor"] = 1.0
    df = pd.concat([df, _mensal("A", ["2024-01-01"])])
    assert _classe(df)["A"] == "nao_recorrente_ativo"


def test_churn_mais_de_6_meses_sem_comprar():
    df = _mensal("A", pd.date_range("2025-01-01", periods=12, freq="MS"), ultima="2025-12-15")
    assert _classe(df)["A"] == "churn"


def test_novo_e_reativado():
    novo = _mensal("N", ["2026-07-01"])
    reat = _mensal("R", ["2024-01-01", "2026-08-01"])
    c = _classe(pd.concat([novo, reat]))
    assert c["N"] == "novo" and c["R"] == "reativado"


def test_status_real_limites():
    ref = pd.Timestamp("2026-08-10")
    venda = pd.Series(pd.to_datetime(["2026-05-12", "2026-05-11", "2026-02-11", "2026-02-10", None]))
    amostra = pd.Series(pd.to_datetime([None, None, None, None, None]))
    assert status_real(venda, amostra, ref).tolist() == ["Active", "Inactive", "Inactive", "Churn", "Churn"]


def test_status_real_usa_amostra_mais_recente():
    venda = pd.Series(pd.to_datetime(["2025-01-01"]))
    amostra = pd.Series(pd.to_datetime(["2026-08-01"]))
    assert status_real(venda, amostra, "2026-08-10").iloc[0] == "Active"


def test_receita_churn_media_6_meses_com_zeros():
    df = _mensal("A", ["2025-07-01", "2025-09-01", "2025-12-01"], valor=600.0)
    out = receita_churn(df, pd.DataFrame({"cliente": ["A"], "ultima_compra": [pd.Timestamp("2025-12-20")]}))
    # janela jul..dez (6 meses, inclusive): 3 × 600 ÷ 6, meses sem compra contam como zero
    assert out.set_index("cliente").loc["A", "receita_churn_mensal"] == pytest.approx(300.0)
    out = receita_churn(df, pd.DataFrame({"cliente": ["A"], "ultima_compra": [pd.Timestamp("2026-01-10")]}))
    assert out.set_index("cliente").loc["A", "receita_churn_mensal"] == pytest.approx(200.0)  # ago..jan


def test_pct_achieved():
    r = pct_achieved(pd.Series([50, 10, 5]), pd.Series([100, 0, np.nan]))
    assert r.iloc[0] == 0.5 and np.isnan(r.iloc[1]) and np.isnan(r.iloc[2])


def test_completar_meses_preenche_buracos():
    df = _mensal("A", ["2026-01-01", "2026-04-01"])
    out = completar_meses(df[["cliente", "periodo", "valor"]])
    assert len(out) == 4 and out["valor"].tolist() == [1000, 0, 0, 1000]


def test_marcar_avulsas():
    out = marcar_avulsas(pd.DataFrame({"compartimento_id": [1, None]}))
    assert out["avulsa"].tolist() == [False, True]
