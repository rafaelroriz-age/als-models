import pandas as pd

from src.features.crosscheck import metricas, oportunidades_conhecidas, previsoes_corte, risco_dupla_contagem


def _deals():
    return pd.DataFrame({
        "entidade": ["A", "B", "C", "D", "E"],
        "estagio": ["Closed Won", "Follow-Up", "Closed Lost", "Closed Won", "Qualify"],
        "probabilidade": [100, 90, 100, 100, 20],
        "valor": [1000.0, 500.0, 300.0, 200.0, 900.0],
        "prazo_meses": [4, 1, 1, 1, 1],
        "data_criacao": pd.to_datetime(["2025-01-01"] * 3 + ["2025-09-01", "2025-01-01"]),
        "data_fechamento_prevista": pd.to_datetime(["2025-07-15"] * 5),
        "data_fechamento_real": pd.to_datetime(["2025-07-20", None, "2025-07-10", "2025-07-20", None]),
    })


def test_oportunidades_filtra_prob_perdida_e_criacao():
    o = oportunidades_conhecidas(_deals(), "2025-06-30", "2025-07-01").set_index("entidade")["opp"]
    # A (ganha depois do corte) e B (aberta >80) entram; C perdida, D criada depois, E prob 20 ficam fora
    assert o.to_dict() == {"A": 1000.0, "B": 500.0}


def test_oportunidades_fechada_antes_do_corte_sai_e_limiar_estrito():
    assert oportunidades_conhecidas(_deals(), "2025-07-31", "2025-07-01")["entidade"].tolist() == ["B"]
    d = _deals().assign(probabilidade=[80, 80, 80, 80, 80])
    assert oportunidades_conhecidas(d, "2025-06-30", "2025-07-01").empty
    # A, B e E (aberta, criada antes); C é perdida e D foi criada depois do corte
    assert len(oportunidades_conhecidas(d, "2025-06-30", "2025-07-01", estrito=False)) == 3


def test_oportunidades_rateio_pelo_prazo():
    r = oportunidades_conhecidas(_deals(), "2025-06-30", "2025-09-01", ratear=True).set_index("entidade")["opp"]
    assert r.to_dict() == {"A": 250.0}  # 1000/4 nos 4 meses de vigência (jul-out); B tem prazo 1


def _mensal():
    meses = pd.date_range("2024-07-01", "2025-06-01", freq="MS")
    return pd.DataFrame({"cliente": "A", "periodo": meses, "valor": 100.0})


def test_previsoes_variantes_ordenadas_e_sem_dupla_contagem_no_desconto():
    deals = pd.DataFrame({
        "entidade": ["A", "N"], "estagio": ["Follow-Up"] * 2, "probabilidade": [90, 90], "valor": [150.0, 70.0],
        "prazo_meses": [1, 1], "data_criacao": pd.to_datetime(["2025-01-01"] * 2),
        "data_fechamento_prevista": pd.to_datetime(["2025-07-10"] * 2), "data_fechamento_real": pd.NaT,
    })
    p = previsoes_corte(_mensal(), deals, "2025-06-30", 1).set_index("variante")
    # A já é recorrente/ativo (100/mês projetado); N é novo na base
    assert p.loc["soma", "previsto"] == p.loc["base", "previsto"] + 220.0
    assert p.loc["desconta_escopo", "previsto"] == p.loc["base", "previsto"] + 70.0
    assert p.loc["desconta_parcial", "previsto"] == p.loc["base", "previsto"] + 50.0 + 70.0
    assert p.loc["soma", "opp_em_escopo"] == 150.0


def test_metricas_e_risco():
    prev = pd.DataFrame({"corte": pd.Timestamp("2025-06-01"), "h": 1, "mes": pd.Timestamp("2025-07-01"),
                         "variante": ["base", "soma"], "previsto": [80.0, 130.0],
                         "opp_total": 50.0, "opp_em_escopo": 25.0, "opp_ja_projetada": 10.0})
    m = metricas(prev, pd.Series({pd.Timestamp("2025-07-01"): 100.0}))
    todos = m[m["h"].astype(str) == "todos"].set_index("variante")
    assert round(todos.loc["base", "wape"], 4) == 0.2 and round(todos.loc["soma", "vies"], 4) == 0.3
    r = risco_dupla_contagem(prev, pd.DataFrame({"faturamento_mes_fechamento": [0.0, 5.0]}))
    assert r["pct_em_escopo"] == 50.0 and r["pct_ja_projetada"] == 20.0 and r["pct_ganhas_com_faturamento_no_mes"] == 50.0
