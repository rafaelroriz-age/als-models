import pandas as pd
import pytest

from src.features.classificacao import (
    CLASSES, ParametrosClassificacao, arvore_interpretavel, classificar, concordancia_status, pontos_piramide)

REF = pd.Timestamp("2026-08-10")


def _df(linhas):
    cols = ["Last Date Sales", "Last Date Sample", "Recorrencia Fat", "Faturamento 12 meses",
            "Equipments Tested This FY", "Annual Sample Potential"]
    d = pd.DataFrame(linhas, columns=cols)
    for c in ["Last Date Sales", "Last Date Sample"]:
        d[c] = pd.to_datetime(d[c])
    return d


def test_classes_basicas():
    d = _df([
        ("2026-08-01", None, 10, 50_000, 30, 1000),          # recorrente
        ("2026-06-01", None, 2, 20_000, None, None),          # não recorrente ativo (faturamento)
        ("2026-06-01", None, 1, 500, 2, 50),                  # menor atividade
        ("2025-01-01", "2025-02-01", 0, 90_000, 50, 5000),    # churn (>180 dias), mesmo com pirâmide alta
        (None, None, 0, 0, None, None),                       # nunca teve atividade -> churn
    ])
    r = classificar(d, REF)
    assert list(r["classe"]) == ["recorrente", "nao_recorrente_ativo", "menor_atividade", "churn", "churn"]
    assert set(r["classe"].cat.categories) == set(CLASSES)


def test_recencia_usa_maior_data_entre_venda_e_amostra():
    d = _df([("2025-01-01", "2026-08-05", 0, 0, None, None)])
    assert classificar(d, REF)["dias_sem_atividade"].iloc[0] == 5


def test_limite_de_180_dias_e_inclusivo():
    d = _df([("2026-02-11", None, 0, 0, None, None), ("2026-02-10", None, 0, 0, None, None)])
    r = classificar(d, REF)  # 180 e 181 dias
    assert list(r["classe"].astype(str)) == ["menor_atividade", "churn"]


def test_pontos_piramide_e_parametros():
    d = _df([("2026-08-01", None, 1, 10_000, 10, 500), ("2026-08-01", None, 1, 9_999, 9, 499)])
    assert list(pontos_piramide(d)) == [3, 0]
    p = ParametrosClassificacao(min_pontos=3)
    assert list(classificar(d, REF, p)["classe"].astype(str)) == ["nao_recorrente_ativo", "menor_atividade"]


def test_concordancia_status():
    classe = pd.Series(["recorrente", "churn", "churn", "menor_atividade"])
    manual = pd.Series(["Active", "Churn", "Active", "Churn"])
    r = concordancia_status(classe, manual)
    assert r["concordancia"] == 0.5 and r["divergentes"] == 2
    assert r["regra_churn_manual_ativo"] == 1 and r["regra_ativo_manual_churn"] == 1


def test_arvore_reproduz_alvo_simples():
    pytest.importorskip("sklearn")
    n = 200
    d = _df([("2026-08-01" if i % 2 else "2024-01-01", None, 1, 100, 1, 1) for i in range(n)])
    alvo = pd.Series(["Active" if i % 2 else "Churn" for i in range(n)])
    r = arvore_interpretavel(d, REF, alvo, profundidade=2)
    assert r["acuracia_cv"] == 1.0 and "dias_sem_atividade" in r["regras"]
