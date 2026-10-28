import json
import os
import re
from pathlib import Path

import pytest

from src.serving.consultas import consultas, nomes_views
from src.serving.contrato import ALERTAS, CONTRATOS, FORECAST_CONSUMO
from src.serving.dashboard import (COLUNAS_ALERTAS, COLUNAS_FORECAST, gerar_sintetico, main, montar_html,
                                   validar_contrato)


@pytest.fixture(scope="module")
def dados():
    return gerar_sintetico()


def test_contrato_de_colunas(dados):
    fc, al = dados
    assert list(fc.columns) == list(COLUNAS_FORECAST)
    assert list(al.columns) == list(COLUNAS_ALERTAS)
    assert set(fc.nivel) == {"segmento", "cliente", "equipamento"}
    assert set(fc.granularidade) == {"mes", "semana"}


def test_intervalo_ordenado_e_sem_vazamento(dados):
    fc, _ = dados
    prev = fc.dropna(subset=["prev_p50"])
    assert (prev.prev_p10 <= prev.prev_p50).all() and (prev.prev_p50 <= prev.prev_p90).all()
    # previsão só no futuro, realizado só no passado
    assert (prev.periodo >= "2026-11-01").all()
    assert (fc.dropna(subset=["realizado"]).periodo < "2026-11-01").all()


def test_segmento_soma_clientes(dados):
    fc, _ = dados
    m = fc[(fc.granularidade == "mes") & (fc.periodo == "2026-12-01")]
    seg = m[m.nivel == "segmento"].set_index("entidade_id").prev_p50
    cli = m[m.nivel == "cliente"].groupby("segmento").prev_p50.sum()
    assert seg.sub(cli).abs().max() < 1e-6


def test_alertas_queda_e_churn(dados):
    _, al = dados
    assert {"queda", "churn"} <= set(al.tipo)
    queda = al[al.tipo == "queda"]
    assert (queda.variacao_pct > 0.20).all() and {"C02", "C07"} <= set(queda.entidade_id)


def test_html_embute_dados_e_aviso(dados):
    fc, al = dados
    html = montar_html(fc, al, sintetico=True)
    m = re.search(r'<script id="dados" type="application/json">(.*?)</script>', html, re.S)
    obj = json.loads(m.group(1))
    assert obj["sintetico"] is True and len(obj["forecast"]["rows"]) == len(fc)
    assert "DADOS SINTÉTICOS" in html and "__DADOS__" not in html
    assert "http" not in re.sub(r"<script id=\"dados\".*?</script>", "", html, flags=re.S)  # sem recurso externo


def test_colunas_ausentes_falham(dados):
    fc, al = dados
    with pytest.raises(ValueError, match="colunas ausentes"):
        montar_html(fc.drop(columns=["prev_p90"]), al, False)


def test_cli_grava_arquivo(tmp_path, monkeypatch):
    monkeypatch.chdir(Path(__file__).parent.parent)
    saida = main(["--saida", str(tmp_path / "d.html")])
    assert saida.read_text(encoding="utf-8").startswith("<!doctype html>")


def test_colunas_vem_do_contrato():
    assert list(COLUNAS_FORECAST) == FORECAST_CONSUMO.nomes() and list(COLUNAS_ALERTAS) == ALERTAS.nomes()
    assert {"potencial_p10", "potencial_p90"} <= set(COLUNAS_FORECAST)


def test_sintetico_passa_no_contrato(dados):
    fc, al = dados
    assert validar_contrato({"forecast_consumo": fc, "alertas": al})


def test_dashboard_recusa_saida_reprovada(dados):
    fc, al = dados
    ruim = fc.assign(prev_p10=fc.prev_p90 + 1)
    with pytest.raises(ValueError, match="reprovadas no G4"):
        validar_contrato({"forecast_consumo": ruim, "alertas": al})


def test_alertas_vazio_e_valido(dados):
    fc, al = dados
    assert validar_contrato({"forecast_consumo": fc, "alertas": al.iloc[0:0]})


# ---------------------------------------------------------------- pré-consultas SQL
def test_nomes_e_prefixo_configuraveis():
    assert nomes_views()["forecast_consumo"] == "v_als_forecast_consumo"
    assert nomes_views("fct_")["pct_achieved"] == "fct_pct_achieved"
    assert nomes_views(nomes={"alertas": "meu_alerta"})["alertas"] == "meu_alerta"
    sql = consultas("x_", {"alertas": "meu_alerta"})
    assert "FROM x_forecast_consumo" in sql["dashboard_forecast"] and "FROM meu_alerta" in sql["dashboard_alertas"]
    assert "v_als_" not in "".join(sql.values())
    with pytest.raises(ValueError, match="desconhecidas"):
        nomes_views(nomes={"nada": "x"})


def test_sql_dialeto_comum_spark_tsql():
    for nome, sql in consultas().items():
        assert not re.search(r"\b(LIMIT|TOP|DATEADD|GETDATE|DATE_TRUNC|ILIKE|QUALIFY)\b", sql, re.I), nome
        assert "`" not in sql and "[" not in sql and not sql.rstrip().endswith(";"), nome


def test_arquivo_sql_em_dia():
    arq = (Path(__file__).parent.parent / "src/serving/sql/01_pre_consultas.sql").read_text(encoding="utf-8")
    for nome, sql in consultas().items():
        assert f"-- {nome}\n{sql};" in arq, nome


def _saidas_locais(tmp_path):
    """Saídas do contrato a partir de uma base mensal pequena (mesmo caminho do `--base`)."""
    import numpy as np
    import pandas as pd

    from src.serving.local import gerar_da_base
    rng = np.random.default_rng(3)
    meses = pd.date_range("2023-01-01", "2026-09-01", freq="MS")
    base = pd.concat([pd.DataFrame({"entidade": f"{i:08d}", "periodo": meses,
                                    "amostras": rng.poisson(8, len(meses)).astype(float), "segmento": seg})
                      for i, seg in enumerate(["Construction", "Grains", "Construction"])], ignore_index=True)
    base.loc[(base.entidade == "00000000") & (base.periodo == "2026-09-01"), "amostras"] = 1.0
    base.loc[(base.entidade == "00000000") & (base.periodo == "2025-09-01"), "amostras"] = 20.0
    arq = tmp_path / "base.parquet"
    base.to_parquet(arq)
    gerar_da_base(arq, tmp_path / "saida")
    return tmp_path / "saida"


def _duck(pasta):
    duckdb = pytest.importorskip("duckdb")
    con = duckdb.connect()
    for k in CONTRATOS.values():
        arq = pasta / k.arquivo
        if arq.exists():
            con.execute(f"CREATE TEMP VIEW {k.pre_consulta} AS SELECT * FROM read_parquet('{arq.as_posix()}')")
    return con


def _pasta_real():
    p = Path(os.environ.get("ALS_PASTA_DADOS", Path(__file__).parent.parent / "data")) / "serving"
    return p if (p / "forecast_consumo.parquet").exists() else None


@pytest.fixture(scope="module", params=["local", "real"])
def pasta(request, tmp_path_factory):
    if request.param == "real":
        p = _pasta_real()
        if p is None:
            pytest.skip("saídas reais não geradas (python -m src.serving.dashboard --base ...)")
        return p
    return _saidas_locais(tmp_path_factory.mktemp("saidas"))


def test_consultas_rodam_e_batem_com_o_parquet(pasta):
    import pandas as pd
    con = _duck(pasta)
    fc = pd.read_parquet(pasta / "forecast_consumo.parquet")
    q = consultas()
    d = con.execute(q["dashboard_forecast"]).df()
    assert list(d.columns) == FORECAST_CONSUMO.nomes() and len(d) == len(fc)
    assert d.prev_p50.sum() == pytest.approx(fc.prev_p50.sum())
    assert d.realizado.sum() == pytest.approx(fc.realizado.sum())
    a = con.execute(q["dashboard_alertas"]).df()
    assert list(a.columns) == ALERTAS.nomes() and len(a) == len(pd.read_parquet(pasta / "alertas.parquet"))
    r = con.execute(q["resumo_entidade"]).df()
    pa = pd.read_parquet(pasta / "pct_achieved.parquet")
    assert len(r) == len(pa) and r.realizado_12m.sum() == pytest.approx(pa.realizado_12m.sum())
    assert (r[r.nivel == "cliente"].meses_horizonte.dropna() == 12).all()   # horizonte completo por cliente
    s = con.execute(q["consumo_segmento_mes"]).df()
    cli = fc[(fc.nivel == "cliente") & (fc.granularidade == "mes")]
    assert s.realizado.sum() == pytest.approx(cli.realizado.sum())
    assert s.prev_p50.sum() == pytest.approx(cli.prev_p50.sum())


def test_consulta_com_prefixo_trocado(pasta):
    con = _duck(pasta)
    con.execute("CREATE TEMP VIEW fct_forecast_consumo AS SELECT * FROM v_als_forecast_consumo")
    n = con.execute(consultas("fct_", {"alertas": "v_als_alertas"})["dashboard_forecast"]).df()
    assert len(n) == con.execute("SELECT COUNT(*) FROM v_als_forecast_consumo").fetchone()[0]


def test_dashboard_das_saidas_do_parquet(pasta, tmp_path):
    saida = main(["--pasta", str(pasta), "--saida", str(tmp_path / "d.html")])
    html = saida.read_text(encoding="utf-8")
    obj = json.loads(re.search(r'<script id="dados" type="application/json">(.*?)</script>', html, re.S).group(1))
    assert obj["sintetico"] is False and len(obj["forecast"]["rows"]) > 0
    assert re.search(r"\d{4}-\d{2}-\d{2}", json.dumps(obj["forecast"]["rows"][0]))   # datas em ISO
