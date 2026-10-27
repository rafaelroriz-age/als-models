import numpy as np
import pandas as pd
import pytest

from src.models.potencial import (ParametrosPotencial, benchmark, distribuicao_por_segmento, pct_achieved, porte,
                                  potencial_cliente, sensibilidade, taxas_cliente)


@pytest.fixture
def dados():
    # 6 clientes de cana com 10 equipamentos da família A; taxas 1..6 amostras/equip/ano; 1 cliente de indústria
    ents = [f"c{i}" for i in range(1, 7)]
    frota = pd.DataFrame({"entidade": ents + ["i1"], "familia": ["A"] * 6 + ["B"], "n_equip": [10] * 6 + [3]})
    real = pd.DataFrame({"entidade": ents + ["i1"], "familia": ["A"] * 6 + ["B"],
                         "amostras_12m": [10.0, 20, 30, 40, 50, 60, 6]})
    seg = pd.DataFrame({"entidade": ents + ["i1"], "segmento": ["cana"] * 6 + ["industria"]})
    return frota, real, seg


def test_porte_faixas():
    assert list(porte(pd.Series([1, 5, 6, 20, 21, 101]))) == ["1-5", "1-5", "6-20", "6-20", "21-100", ">100"]


def test_pct_achieved_d6():
    r = pct_achieved(pd.Series([50.0, 10, 5]), pd.Series([100.0, 0, np.nan]))
    assert r.iloc[0] == 0.5 and r.iloc[1:].isna().all()


def test_benchmark_quantil_do_grupo(dados):
    b = benchmark(taxas_cliente(*dados), ParametrosPotencial(quantil=0.75, min_clientes=5))
    cana = b[b["segmento"] == "cana"]
    assert (cana["nivel"] == "segmento×familia×porte").all()
    assert cana["taxa_bench"].iloc[0] == pytest.approx(np.quantile([1, 2, 3, 4, 5, 6], 0.75))


def test_fallback_grupo_pequeno_vai_ao_global(dados):
    b = benchmark(taxas_cliente(*dados), ParametrosPotencial(min_clientes=5))
    ind = b[b["entidade"] == "i1"].iloc[0]
    assert ind["nivel"] == "global"
    assert ind["taxa_bench"] == pytest.approx(np.quantile([1, 2, 3, 4, 5, 6, 2], 0.75))


def test_potencial_e_achieved_por_cliente(dados):
    c = potencial_cliente(*dados).set_index("entidade")
    q = np.quantile([1, 2, 3, 4, 5, 6], 0.75)
    assert c.loc["c1", "potencial"] == pytest.approx(10 * q)
    assert c.loc["c1", "pct_achieved"] == pytest.approx(10 / (10 * q))
    assert c.loc["c6", "pct_achieved"] > 1   # acima do benchmark p75


def test_cliente_sem_coleta_tem_achieved_zero(dados):
    frota, real, seg = dados
    frota = pd.concat([frota, pd.DataFrame({"entidade": ["c7"], "familia": ["A"], "n_equip": [10]})])
    seg = pd.concat([seg, pd.DataFrame({"entidade": ["c7"], "segmento": ["cana"]})])
    c = potencial_cliente(frota, real, seg).set_index("entidade")
    assert c.loc["c7", "realizado_12m"] == 0 and c.loc["c7", "pct_achieved"] == 0
    assert c.loc["c7", "potencial"] > 0


def test_distribuicao_e_sensibilidade(dados):
    d = distribuicao_por_segmento(potencial_cliente(*dados))
    assert d.loc["cana", "clientes"] == 6
    s = sensibilidade(*dados, {"seg×fam×porte": ParametrosPotencial(),
                               "seg": ParametrosPotencial(dimensoes=("segmento",)),
                               "p50": ParametrosPotencial(quantil=0.5)})
    assert s.loc[0, "spearman_vs_base"] == pytest.approx(1.0)
    assert s.loc[2, "potencial_total"] < s.loc[0, "potencial_total"]
