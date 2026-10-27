import numpy as np
import pandas as pd
import pytest

from src.features.alertas import ParametrosChurnCompartimento, alertar_queda, compartimento_churn


def _mensal(valores, inicio="2025-01-01", cliente="A"):
    """Uma linha por mês; valor None = mês sem coleta (linha ausente)."""
    meses = pd.date_range(inicio, periods=len(valores), freq="MS")
    df = pd.DataFrame({"cliente": cliente, "periodo": meses, "valor": valores})
    return df.dropna(subset=["valor"])


def _alerta_no_mes(df, mes):
    return df.set_index("periodo").loc[pd.Timestamp(mes)]


def _serie_ano_anterior(atual, base=1000.0):
    """13 meses: base no mês 0 (ano anterior), atual no mês 12."""
    return [base] + [None] * 11 + [atual]


# --- RN-05: queda > 20% -------------------------------------------------------------------------

def test_queda_exatamente_20_por_cento_nao_alerta():
    out = alertar_queda(_mensal(_serie_ano_anterior(800.0)))
    linha = _alerta_no_mes(out, "2026-01-01")
    assert linha["queda"] == pytest.approx(0.20)
    assert not linha["alerta_queda"]


def test_queda_de_20_1_por_cento_alerta():
    out = alertar_queda(_mensal(_serie_ano_anterior(798.99)))
    assert _alerta_no_mes(out, "2026-01-01")["alerta_queda"]


def test_queda_exatamente_20_com_base_nao_redonda_nao_alerta():
    # 1 - 0,8 em ponto flutuante vira 0,19999...; a tolerância evita alerta espúrio
    out = alertar_queda(_mensal(_serie_ano_anterior(2.4, base=3.0)))
    assert not _alerta_no_mes(out, "2026-01-01")["alerta_queda"]


def test_alta_nao_alerta():
    out = alertar_queda(_mensal(_serie_ano_anterior(1500.0)))
    linha = _alerta_no_mes(out, "2026-01-01")
    assert linha["queda"] < 0
    assert not linha["alerta_queda"]


def test_base_ano_anterior_sem_historico_nao_avalia():
    # série de 6 meses: não existe mês t-12, então não há queda nem alerta
    out = alertar_queda(_mensal([1000.0, 900.0, 800.0, 100.0, 50.0, 10.0]), base="ano_anterior")
    assert out["base_valor"].isna().all()
    assert not out["alerta_queda"].any()


def test_base_zero_ou_negativa_nao_gera_queda_infinita():
    out = alertar_queda(_mensal(_serie_ano_anterior(10.0, base=0.0)))
    linha = _alerta_no_mes(out, "2026-01-01")
    assert np.isnan(linha["queda"])
    assert not linha["alerta_queda"]


def test_mes_sem_coleta_no_mes_avaliado_nao_vira_queda_de_100():
    # 2026-01 sem linha na base: a série termina em 2025-12 e nenhum mês é tratado como zero
    out = alertar_queda(_mensal([1000.0] + [None] * 11 + [None]))
    assert out["periodo"].max() < pd.Timestamp("2026-01-01")
    assert not out["alerta_queda"].any()

    # mês sem coleta no meio da série: NaN, não zero, logo sem alerta de 100%
    out = alertar_queda(_mensal([1000.0] + [None] * 11 + [500.0, None, 600.0]))
    assert pd.isna(_alerta_no_mes(out, "2026-02-01")["valor"])
    assert not _alerta_no_mes(out, "2026-02-01")["alerta_queda"]


def test_mes_sem_coleta_na_base_deixa_base_nan():
    valores = [None, 1000.0] + [None] * 10 + [500.0]  # mês base (2025-01) sem coleta
    out = alertar_queda(_mensal(valores, inicio="2025-01-01"))
    linha = _alerta_no_mes(out, "2026-01-01")
    assert np.isnan(linha["base_valor"])
    assert not linha["alerta_queda"]


def test_serie_curta_mm3_precisa_de_3_meses_anteriores():
    out = alertar_queda(_mensal([1000.0, 1000.0, 1000.0, 100.0]), base="mm3")
    assert out["base_valor"].iloc[:3].isna().all()
    assert _alerta_no_mes(out, "2025-04-01")["base_valor"] == pytest.approx(1000.0)
    assert _alerta_no_mes(out, "2025-04-01")["alerta_queda"]


def test_mm3_usa_so_meses_anteriores_nao_o_proprio_mes():
    out = alertar_queda(_mensal([100.0, 100.0, 100.0, 1000.0]), base="mm3")
    # alta no mês 4 não entra na própria base: média dos 3 meses anteriores = 100
    assert _alerta_no_mes(out, "2025-04-01")["base_valor"] == pytest.approx(100.0)
    assert not _alerta_no_mes(out, "2025-04-01")["alerta_queda"]


def test_mm12_com_mes_sem_coleta_na_janela_nao_avalia():
    valores = [1000.0] * 5 + [None] + [1000.0] * 6 + [700.0]  # um mês vazio na janela de 12
    out = alertar_queda(_mensal(valores), base="mm12")
    assert np.isnan(_alerta_no_mes(out, "2026-01-01")["base_valor"])
    assert not _alerta_no_mes(out, "2026-01-01")["alerta_queda"]


def test_mm12_serie_completa_detecta_queda():
    valores = [1000.0] * 12 + [700.0]
    out = alertar_queda(_mensal(valores), base="mm12")
    assert _alerta_no_mes(out, "2026-01-01")["base_valor"] == pytest.approx(1000.0)
    assert _alerta_no_mes(out, "2026-01-01")["alerta_queda"]


def test_clientes_sao_avaliados_separadamente():
    a = _mensal(_serie_ano_anterior(500.0), cliente="A")
    b = _mensal(_serie_ano_anterior(1000.0), cliente="B")
    out = alertar_queda(pd.concat([a, b], ignore_index=True))
    por_cliente = out[out["periodo"] == pd.Timestamp("2026-01-01")].set_index("cliente")["alerta_queda"]
    assert por_cliente["A"] and not por_cliente["B"]


def test_base_invalida_levanta_erro():
    with pytest.raises(ValueError):
        alertar_queda(_mensal([1.0] * 13), base="mes_passado")


# --- RN-06: compartimento churn -----------------------------------------------------------------

def _coletas(horimetro, intervalo_h=250, horimetro_atual=1000):
    return pd.DataFrame({
        "equipamento": ["E1"], "compartimento": ["motor"], "horimetro": [horimetro],
        "intervalo_h": [intervalo_h], "horimetro_atual": [horimetro_atual],
    })


def test_churn_exatamente_no_intervalo_nao_marca():
    out = compartimento_churn(_coletas(horimetro=750, intervalo_h=250, horimetro_atual=1000))
    assert out["horas_sem_coleta"].iloc[0] == 250
    assert not out["compartimento_churn"].iloc[0]


def test_churn_acima_do_intervalo_marca():
    out = compartimento_churn(_coletas(horimetro=749, intervalo_h=250, horimetro_atual=1000))
    assert out["compartimento_churn"].iloc[0]


def test_churn_com_fator_configuravel():
    out = compartimento_churn(_coletas(horimetro=600, intervalo_h=250, horimetro_atual=1000),
                              ParametrosChurnCompartimento(fator=2.0))
    assert not out["compartimento_churn"].iloc[0]  # 400 h ≤ 2 × 250


def test_churn_sem_horimetro_atual_nao_avalia():
    out = compartimento_churn(_coletas(horimetro=100, horimetro_atual=np.nan))
    assert np.isnan(out["horas_sem_coleta"].iloc[0])
    assert not out["compartimento_churn"].iloc[0]


def test_churn_usa_ultima_coleta_do_compartimento():
    df = pd.DataFrame({
        "equipamento": ["E1", "E1"], "compartimento": ["motor", "motor"],
        "horimetro": [100.0, 900.0], "intervalo_h": [250, 250], "horimetro_atual": [1000.0, 1000.0],
    })
    out = compartimento_churn(df)
    assert out["horimetro"].iloc[0] == 900.0
    assert not out["compartimento_churn"].iloc[0]
