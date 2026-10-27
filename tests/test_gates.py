import pandas as pd
import pytest

from src.gates.checks import (CHAVES_OBRIGATORIAS, avaliar_g0, avaliar_g1, avaliar_g1_limpo,
                              cobertura_join)

HOJE = pd.Timestamp("2026-10-27")


def perfis_validos():
    return [
        {"tabela": t, "n_linhas": 100, "nulos_pct": {c: 0.0 for c in lim}, "datas": {}}
        for t, lim in CHAVES_OBRIGATORIAS.items()
    ]


def falhas(res):
    return {(r["checagem"], r["alvo"]) for r in res if not r["ok"]}


# ---------- G0 ----------
def test_g0_valido():
    p = perfis_validos()
    p[0]["datas"] = {"data_coleta": ("2020-01-01", "2026-10-01")}
    assert falhas(avaliar_g0(p, HOJE)) == set()


def test_g0_tabela_ausente():
    p = perfis_validos()[1:]
    assert ("tabela_acessivel", "bronze_s360.amostra") in falhas(avaliar_g0(p, HOJE))


def test_g0_tabela_vazia():
    p = perfis_validos()
    p[0]["n_linhas"] = 0
    assert ("nao_vazia", "bronze_s360.amostra") in falhas(avaliar_g0(p, HOJE))


def test_g0_nulos_acima_do_limite():
    p = perfis_validos()
    p[0]["nulos_pct"]["id"] = 0.1  # limite 0.0
    f = falhas(avaliar_g0(p, HOJE))
    assert ("nulos<= 0.0%", "bronze_s360.amostra.id") in f


def test_g0_coluna_sem_perfil_de_nulos():
    p = perfis_validos()
    del p[0]["nulos_pct"]["cliente_id"]
    assert ("nulos<= 1.0%", "bronze_s360.amostra.cliente_id") in falhas(avaliar_g0(p, HOJE))


@pytest.mark.parametrize("intervalo", [("2005-01-01", "2026-01-01"), ("2020-01-01", "2027-06-01"), (None, None)])
def test_g0_datas_implausiveis(intervalo):
    p = perfis_validos()
    p[0]["datas"] = {"data_coleta": intervalo}
    assert ("datas_plausiveis", "bronze_s360.amostra.data_coleta") in falhas(avaliar_g0(p, HOJE))


# ---------- G1: tabela-base entidade × mês ----------
def base_valida():
    meses = pd.period_range("2025-01", "2025-06", freq="M").to_timestamp()
    return pd.DataFrame([(e, m, 5.0) for e in ("A", "B") for m in meses], columns=["entidade", "periodo", "qtd"])


def test_g1_valido():
    assert falhas(avaliar_g1(base_valida(), ["entidade", "periodo"], "qtd")) == set()


def test_g1_chave_duplicada():
    b = pd.concat([base_valida(), base_valida().iloc[[0]]], ignore_index=True)
    assert ("chave_unica", "entidade+periodo") in falhas(avaliar_g1(b, ["entidade", "periodo"], "qtd"))


def test_g1_negativo():
    b = base_valida()
    b.loc[0, "qtd"] = -1
    assert ("nao_negativo", "qtd") in falhas(avaliar_g1(b, ["entidade", "periodo"], "qtd"))


def test_g1_nulo():
    b = base_valida()
    b.loc[0, "qtd"] = None
    assert ("sem_nulos", "qtd") in falhas(avaliar_g1(b, ["entidade", "periodo"], "qtd"))


def test_g1_mes_faltando():
    b = base_valida()
    b = b[~((b.entidade == "A") & (b.periodo == "2025-03-01"))]
    assert ("meses_continuos", "entidade") in falhas(avaliar_g1(b, ["entidade", "periodo"], "qtd"))


# ---------- G1: tabela limpa (chaves, duplicatas, datas) ----------
def limpa_valida():
    return pd.DataFrame({
        "id": [1, 2, 3],
        "cliente_id": [10, 10, 11],
        "data_coleta": pd.to_datetime(["2024-01-05", "2024-02-05", "2025-03-01"]),
    })


def rodar_limpo(df):
    return avaliar_g1_limpo(df, ["id", "cliente_id"], ["id"], ["data_coleta"], hoje=HOJE)


def test_g1_limpo_valido():
    assert falhas(rodar_limpo(limpa_valida())) == set()


def test_g1_limpo_nulo_em_chave():
    d = limpa_valida()
    d.loc[1, "cliente_id"] = None
    assert ("chave_sem_nulos", "cliente_id") in falhas(rodar_limpo(d))


def test_g1_limpo_duplicata():
    d = pd.concat([limpa_valida(), limpa_valida().iloc[[0]]], ignore_index=True)
    assert ("sem_duplicatas", "id") in falhas(rodar_limpo(d))


@pytest.mark.parametrize("data", ["2009-12-31", "2026-10-29"])
def test_g1_limpo_data_fora_do_intervalo(data):
    d = limpa_valida()
    d.loc[0, "data_coleta"] = pd.Timestamp(data)
    assert ("datas_no_intervalo", "data_coleta") in falhas(rodar_limpo(d))


def test_g1_limpo_coluna_ausente():
    d = limpa_valida().drop(columns=["cliente_id", "data_coleta"])
    assert {("chave_sem_nulos", "cliente_id"), ("datas_no_intervalo", "data_coleta")} <= falhas(rodar_limpo(d))


def test_g1_limpo_data_no_limite_passa():
    d = limpa_valida()
    d.loc[0, "data_coleta"] = pd.Timestamp("2010-01-01")
    assert falhas(rodar_limpo(d)) == set()


# ---------- G1: cobertura de join ----------
def test_cobertura_join_valida():
    esq = pd.DataFrame({"cnpj": ["1", "2", "3", "4", None]})
    dir_ = pd.DataFrame({"cnpj": ["1", "2", "3", "4", "9"]})
    r = cobertura_join(esq, dir_, "cnpj", 90)
    assert r[0]["ok"] and "100.0%" in r[0]["detalhe"]


def test_cobertura_join_abaixo_do_minimo():
    esq = pd.DataFrame({"cnpj": ["1", "2", "3", "4"]})
    dir_ = pd.DataFrame({"cnpj": ["1", "2"]})
    r = cobertura_join(esq, dir_, "cnpj", 90)
    assert not r[0]["ok"] and "50.0%" in r[0]["detalhe"]


def test_cobertura_join_esquerda_vazia_e_coluna_ausente():
    assert not cobertura_join(pd.DataFrame({"k": []}), pd.DataFrame({"k": [1]}), "k")[0]["ok"]
    assert not cobertura_join(pd.DataFrame({"x": [1]}), pd.DataFrame({"k": [1]}), "k")[0]["ok"]
