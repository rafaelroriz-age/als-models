import json

import numpy as np
import pandas as pd
import pytest

from scripts.fabric_guard import violacoes
from src.pipeline import dev
from src.serving.contrato import aprovado, validar

CORTE = pd.Timestamp("2026-10-01")
DESDE = CORTE - pd.DateOffset(months=36)


def entradas(seed=3):
    """3 clientes S360 (dois com a mesma raiz de CNPJ → mesma entidade), 4 equipamentos, 36 meses."""
    rng = np.random.default_rng(seed)
    meses = pd.date_range(DESDE, CORTE - pd.DateOffset(months=1), freq="MS")
    linhas = []
    for cli, eqs, nivel in ((1, (10, 11), 20), (2, (20,), 8), (3, (30,), 5)):
        for eq in eqs:
            for i, m in enumerate(meses):
                if cli == 3 and i < 30:      # cliente novo: só 6 meses de histórico
                    continue
                n = max(0, int(nivel + 4 * np.sin(2 * np.pi * m.month / 12) + rng.normal(0, 2)))
                if cli == 1 and m == meses[-1]:
                    n = 1                     # queda forte no último mês fechado
                if n:
                    linhas.append((cli, eq, m.year, m.month, n))
    amostras = pd.DataFrame(linhas, columns=["cliente_id", "equipamento_id", "ano", "mes", "amostras"])
    clientes = pd.DataFrame({"cliente_id": [1, 2, 3], "id_cigam": ["A1", "B2", None],
                             "codigo_legado": [None, None, None], "ativo": [1, 1, 1]})
    accounts = pd.DataFrame({"zoho_id": ["z1", "z2"], "cnpj": ["11.111.111/0001-11", "22.222.222/0001-22"],
                             "erp_id": ["A1", "B2"], "conta": [None, None],
                             "razao_social": ["Mineradora Alfa Ltda", "Transportes Beta SA"],
                             "segmento": ["Mineração", "Transporte"]})
    return amostras, clientes, accounts


@pytest.fixture(scope="module")
def serie():
    return dev.series_mensais(*entradas(), DESDE, CORTE)


def test_lakehouse_parametro_env_e_padrao(monkeypatch):
    monkeypatch.delenv("ALS_LAKEHOUSE", raising=False)
    assert dev.resolver_lakehouse() == "LakehouseOel"
    monkeypatch.setenv("ALS_LAKEHOUSE", "OutroLH")
    assert dev.resolver_lakehouse() == "OutroLH"
    assert dev.resolver_lakehouse("Lh_Param") == "Lh_Param"
    for ruim in ("x; DROP", "a.b", "`x`"):
        with pytest.raises(ValueError):
            dev.resolver_lakehouse(ruim)


def test_sql_fontes_qualifica_lakehouse_e_so_le():
    sql = dev.sql_fontes("LakehouseX")
    assert set(sql) == set(dev.FONTES) and all(k.startswith("v_als_src_") for k in sql)
    assert "FROM `LakehouseX`.bronze_s360.amostra" in sql["v_als_src_amostra"]
    assert "FROM `LakehouseX`.silver_zoho.accounts" in sql["v_als_src_zoho_accounts"]
    assert dev.sql_fontes("L", {"zoho": "outro_zoho"})["v_als_src_zoho_accounts"].endswith("`L`.outro_zoho.accounts")
    texto = "\n".join([*sql.values(), dev.sql_amostras_mes(DESDE, CORTE)])
    assert all(t.lstrip().upper().startswith("SELECT") for t in [*sql.values(), dev.sql_amostras_mes(DESDE, CORTE)])
    assert violacoes(texto) == []


def test_janela_corta_no_mes():
    assert dev.janela("2026-10-28", 12) == (pd.Timestamp("2025-10-01"), CORTE)


def test_series_niveis_ponte_e_grade(serie):
    assert set(serie["nivel"]) == {"segmento", "cliente", "equipamento"}
    cli = serie[serie["nivel"] == "cliente"]
    assert cli["entidade_id"].nunique() == 3 and "11111111" in set(cli["entidade_id"])
    assert serie["periodo"].max() == CORTE - pd.DateOffset(months=1)
    novo = cli[cli["entidade_id"] == "s360:3"]
    assert len(novo) == 6 and (novo["segmento"] == "sem_segmento").all()
    eq = serie[serie["nivel"] == "equipamento"]
    assert eq.groupby("periodo")["y"].sum().equals(cli.groupby("periodo")["y"].sum())
    seg = serie[serie["nivel"] == "segmento"].groupby("periodo")["y"].sum()
    assert seg.equals(cli.groupby("periodo")["y"].sum())


def test_saidas_passam_no_contrato(serie):
    saidas = dev.gerar(serie, CORTE, h=6)
    for nome, df in saidas.items():
        res = validar(nome, df)
        assert aprovado(res), [r for r in res if not r["ok"]]
    fc = saidas["forecast_consumo"]
    fut = fc[fc["periodo"] >= CORTE]
    assert fut["periodo"].nunique() == 6 and fut["realizado"].isna().all()
    assert (fc.loc[fc["periodo"] < CORTE, "prev_p50"].isna()).all()
    assert fc["versao_modelo"].nunique() == 1 and fc["versao_modelo"].iat[0].startswith(dev.MODELO + "+")


def test_forecast_ingenuo_sazonal_e_fallback(serie):
    fc = dev.forecast_consumo(serie, CORTE, h=3)
    alvo = fc[(fc["entidade_id"] == "22222222") & (fc["periodo"] == CORTE)]["prev_p50"].iat[0]
    base = serie[(serie["entidade_id"] == "22222222") & (serie["periodo"] == CORTE - pd.DateOffset(months=12))]
    assert alvo == base["y"].iat[0]
    novo = fc[(fc["entidade_id"] == "s360:3") & fc["prev_p50"].notna()]
    ultimo = serie[serie["entidade_id"] == "s360:3"].sort_values("periodo")["y"].iat[-1]
    assert (novo["prev_p50"] == ultimo).all() and (novo["prev_p10"] == novo["prev_p90"]).all()
    with pytest.raises(ValueError):
        dev.forecast_consumo(serie, CORTE, h=13)


def test_pct_achieved_sem_e_com_potencial(serie):
    sem = dev.pct_achieved(serie, CORTE)
    assert sem["pct_achieved"].isna().all() and (sem["realizado_12m"] > 0).all()
    assert sem.loc[sem["entidade_id"] == "11111111", "n_equip"].iat[0] == 2
    pot = sem[["nivel", "entidade_id"]].assign(potencial_12m=1000.0)
    com = dev.pct_achieved(serie, CORTE, pot)
    assert np.allclose(com["pct_achieved"], com["realizado_12m"] / 1000)
    assert aprovado(validar("pct_achieved", com))


def test_alerta_de_queda_no_ultimo_mes(serie):
    al = dev.alertas(serie, CORTE)
    assert list(al["entidade_id"]) == ["11111111"]
    assert al["variacao_pct"].iat[0] > 0.2 and al["periodo"].iat[0] == CORTE - pd.DateOffset(months=1)


def test_gravar_so_aprovadas(serie, tmp_path):
    saidas = dev.gerar(serie, CORTE, h=3)
    saidas["alertas"] = saidas["alertas"].iloc[0:0]   # vazia → reprovada no G4 (nao_vazia)
    rel = dev.gravar(saidas, tmp_path)
    assert rel["reprovadas"] == ["alertas"] and not (tmp_path / "alertas.parquet").exists()
    lido = pd.read_parquet(tmp_path / "forecast_consumo.parquet")
    assert aprovado(validar("forecast_consumo", lido))
    assert json.loads((tmp_path / "relatorio_dev.json").read_text(encoding="utf-8"))["reprovadas"] == ["alertas"]
