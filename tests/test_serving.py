import json
import re
from pathlib import Path

import pytest

from src.serving.dashboard import COLUNAS_ALERTAS, COLUNAS_FORECAST, gerar_sintetico, main, montar_html


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


def test_sql_cobre_as_colunas_do_contrato():
    sql = (Path(__file__).parent.parent / "src/serving/sql/01_forecast_consumo.sql").read_text(encoding="utf-8")
    for col in list(COLUNAS_FORECAST) + list(COLUNAS_ALERTAS):
        assert re.search(rf"\b{col}\b", sql), col
