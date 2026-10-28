import numpy as np
import pandas as pd
import pytest

from src.serving import contrato as ct

CORTE = "2026-11-01"


def falhas(res):
    return {(r["checagem"], r["alvo"].split(".", 1)[-1]) for r in res if not r["ok"]}


def forecast():
    per = ["2026-09-01", "2026-10-01", "2026-11-01", "2026-12-01"]
    return pd.DataFrame({
        "nivel": "cliente", "entidade_id": "12345678", "entidade_nome": "Cli", "cliente_id": "12345678",
        "segmento": "Mineração", "granularidade": "mes", "periodo": pd.to_datetime(per),
        "realizado": [10.0, 12.0, np.nan, np.nan], "prev_p10": [np.nan, np.nan, 8.0, 9.0],
        "prev_p50": [np.nan, np.nan, 10.0, 11.0], "prev_p90": [np.nan, np.nan, 13.0, 14.0],
        "potencial": 20.0, "potencial_p10": 15.0, "potencial_p90": 25.0,
        "data_corte": pd.Timestamp(CORTE), "versao_modelo": "m1-abc",
    })


def pct():
    return pd.DataFrame({
        "nivel": ["cliente", "cliente"], "entidade_id": ["a", "b"], "entidade_nome": ["A", "B"],
        "segmento": "Agro", "porte": ["P", None], "n_equip": [3, np.nan], "data_corte": pd.Timestamp(CORTE),
        "realizado_12m": [50.0, 5.0], "potencial_12m": [100.0, 0.0], "pct_achieved": [0.5, np.nan],
    })


def alertas():
    return pd.DataFrame({
        "tipo": ["queda", "churn"], "nivel": ["cliente", "equipamento"], "entidade_id": ["a", "e1"],
        "entidade_nome": ["A", "E1"], "cliente_id": ["a", "a"], "segmento": "Agro",
        "periodo": pd.to_datetime(["2026-09-01", "2026-09-01"]), "valor_atual": [5.0, 600.0],
        "valor_base": [10.0, 500.0], "variacao_pct": [0.5, np.nan], "detalhe": ["base", "compartimento motor"],
    })


def vendas():
    return pd.DataFrame({
        "nivel": "total", "entidade_id": "total", "data_corte": pd.Timestamp(CORTE),
        "periodo": pd.to_datetime(["2026-12-01", "2027-01-01"]), "h": [1, 2],
        "recorrente_base": 100.0, "nao_recorrente": 20.0, "novos": 0.0, "reativados": 0.0, "churn": 5.0,
        "var_mercado": 0.0, "faturamento_p10": 90.0, "faturamento_p50": 115.0, "faturamento_p90": 130.0,
        "ebit_p10": np.nan, "ebit_p50": np.nan, "ebit_p90": np.nan, "versao_modelo": "m1",
    })


def backtest():
    return pd.DataFrame({
        "kpi": "consumo_real", "modelo": ["a", "b"], "nivel": "cliente", "segmento": "todos", "horizonte": 1,
        "data_corte": pd.Timestamp(CORTE), "versao_modelo": "v", "n": [100, 100], "wape": [0.2, 0.3],
        "mae": [1.0, 2.0], "bias_pct": [0.0, 0.1], "smape": [0.2, 0.3], "cobertura": [0.78, 0.85],
    })


FABRICAS = {"forecast_consumo": forecast, "pct_achieved": pct, "alertas": alertas,
            "forecast_vendas": vendas, "backtest_metricas": backtest}


@pytest.mark.parametrize("nome", list(FABRICAS))
def test_saida_valida_passa(nome):
    res = ct.validar(nome, FABRICAS[nome]())
    assert not falhas(res), falhas(res)


def test_todas_as_saidas_e_aprovado():
    res = ct.validar_todas({n: f() for n, f in FABRICAS.items()})
    assert ct.aprovado(res)
    assert {r["gate"] for r in res} == {"G4", "G5"}


def test_saida_ausente_bloqueia():
    res = ct.validar_todas({"forecast_consumo": forecast()})
    assert not ct.aprovado(res)


def test_contratos_tem_nomes_e_arquivos_unicos():
    assert len({c.pre_consulta for c in ct.CONTRATOS.values()}) == len(ct.CONTRATOS)
    assert all(c.pre_consulta.startswith("v_als_") for c in ct.CONTRATOS.values())
    assert all(c.caminho.startswith("Files/als_oilmodel/saida/") and c.arquivo.endswith(".parquet")
               for c in ct.CONTRATOS.values())
    for c in ct.CONTRATOS.values():
        assert set(c.chave) <= set(c.nomes())


def test_coluna_ausente_e_extra():
    df = forecast().drop(columns=["prev_p90"])
    assert ("colunas_presentes", "forecast_consumo") in falhas(ct.validar("forecast_consumo", df))
    df = forecast().assign(lixo=1)
    assert ("sem_colunas_extras", "forecast_consumo") in falhas(ct.validar("forecast_consumo", df))


def test_tipo_errado_e_nulo_em_coluna_obrigatoria():
    df = forecast().assign(entidade_id=123)
    assert ("tipo", "entidade_id") in falhas(ct.validar("forecast_consumo", df))
    df = forecast()
    df.loc[0, "segmento"] = None
    assert ("sem_nulos", "segmento") in falhas(ct.validar("forecast_consumo", df))


def test_dominio_invalido():
    df = forecast().assign(granularidade="dia")
    assert ("dominio", "granularidade") in falhas(ct.validar("forecast_consumo", df))


def test_chave_duplicada():
    df = pd.concat([forecast(), forecast().iloc[[0]]], ignore_index=True)
    assert any(c == "chave_unica" for c, _ in falhas(ct.validar("forecast_consumo", df)))


def test_quantis_fora_de_ordem_e_incompletos():
    df = forecast()
    df.loc[2, ["prev_p10", "prev_p90"]] = [12.0, 9.0]
    assert any(c == "quantis_ordenados" for c, _ in falhas(ct.validar("forecast_consumo", df)))
    df = forecast()
    df.loc[3, "prev_p90"] = np.nan
    assert any(c == "quantis_completos" for c, _ in falhas(ct.validar("forecast_consumo", df)))


def test_negativo_e_periodo_trocado():
    df = forecast()
    df.loc[0, "realizado"] = -1.0
    assert ("nao_negativo", "realizado") in falhas(ct.validar("forecast_consumo", df))
    df = forecast()
    df.loc[2, "realizado"] = 3.0           # realizado em período futuro
    assert ("so_periodo_passado", "realizado") in falhas(ct.validar("forecast_consumo", df))
    df = forecast()
    df.loc[0, ["prev_p10", "prev_p50", "prev_p90"]] = [1.0, 2.0, 3.0]   # previsão em período passado
    assert ("so_periodo_futuro", "prev_p10") in falhas(ct.validar("forecast_consumo", df))


def test_horizonte_incompleto_e_dois_cortes():
    df = forecast()
    df.loc[3, ["prev_p10", "prev_p50", "prev_p90"]] = np.nan
    assert ("horizonte_completo", "prev_p50") in falhas(ct.validar("forecast_consumo", df))
    df = forecast()
    df.loc[0, "data_corte"] = pd.Timestamp("2026-10-01")
    assert ("corte_unico", "data_corte") in falhas(ct.validar("forecast_consumo", df))


def test_datas_como_texto_iso_aceitas_e_lixo_rejeitado():
    assert not falhas(ct.validar("forecast_consumo", forecast().assign(
        periodo=lambda d: d["periodo"].dt.strftime("%Y-%m-%d"))))
    assert ("tipo", "periodo") in falhas(ct.validar("forecast_consumo", forecast().assign(periodo="ontem")))


def test_pct_achieved_deve_ser_realizado_sobre_potencial():
    df = pct()
    df.loc[0, "pct_achieved"] = 0.9
    assert ("pct_igual_realizado_sobre_potencial", "pct_achieved") in falhas(ct.validar("pct_achieved", df))


def test_alertas_regras():
    df = alertas()
    df.loc[0, "variacao_pct"] = 0.20      # 20,0% exatos não alertam
    assert ("queda_acima_de_20pct", "variacao_pct") in falhas(ct.validar("alertas", df))
    df = alertas()
    df.loc[1, "valor_atual"] = 400.0
    assert ("churn_acima_do_intervalo", "valor_atual") in falhas(ct.validar("alertas", df))
    df = alertas().assign(tipo=["queda", "outro"])
    assert ("dominio", "tipo") in falhas(ct.validar("alertas", df))


def test_vendas_total_negativo_e_periodo():
    df = vendas()
    df.loc[0, "churn"] = 500.0
    assert ("total_sem_churn_negativo", "componentes") in falhas(ct.validar("forecast_vendas", df))
    df = vendas()
    df.loc[0, "periodo"] = pd.Timestamp("2026-10-01")
    assert ("periodo_apos_corte", "periodo") in falhas(ct.validar("forecast_vendas", df))
    df = vendas()
    df.loc[0, ["ebit_p10", "ebit_p50", "ebit_p90"]] = [5.0, 3.0, 8.0]
    assert any(c == "quantis_ordenados" for c, _ in falhas(ct.validar("forecast_vendas", df)))


def test_g5_calibracao_avisa_sem_bloquear():
    df = backtest()
    df.loc[0, "cobertura"] = 0.40
    res = ct.validar("backtest_metricas", df)
    assert ("calibracao_intervalo", "cobertura") in falhas(res)
    assert ct.aprovado(res)                       # G5 é aviso
    assert not ct.aprovado(res, bloqueantes=("G4", "G5"))


def test_esquema_markdown_lista_todas_as_saidas():
    md = ct.esquema_markdown()
    for c in ct.CONTRATOS.values():
        assert c.pre_consulta in md and c.caminho in md
