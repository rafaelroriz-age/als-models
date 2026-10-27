import pytest

from conftest import CALCULADORA, exige
from src.features.calculadora import (amostras_3_por_compartimento, amostras_ano, coletas_compartimento,
                                      faturamento_dealer, ler_calculadora, msc_amostras_ano)


def test_retroescavadeira_1000h():
    assert amostras_ano(1, 1000, [250, 1000, 500, 500, 500, 500]) == 13


def test_frota_multiplica():
    assert amostras_ano(556, 2000, [250, 1000, 500, 500, 500]) == 556 * 22


def test_arredonda_para_baixo_e_ignora_intervalo_invalido():
    assert coletas_compartimento(999, 250) == 3
    assert coletas_compartimento(1000, 0) == 0
    assert coletas_compartimento(1000, None) == 0


def test_faturamento_dealer_padrao():
    assert faturamento_dealer(12279) == pytest.approx(12279 * 0.05 * 1950)


def test_msc_e_tres_por_compartimento():
    assert msc_amostras_ano(100) == 600
    assert amostras_3_por_compartimento(1, 7) == 21


@exige(CALCULADORA)
def test_reproduz_planilha():
    blocos, comps = ler_calculadora(CALCULADORA)
    assert len(blocos) == 50
    divergentes = blocos[~blocos["reproduz"]]
    # Únicos blocos que não batem: caminhões do agro "com diesel", com zeros digitados no lugar da fórmula.
    assert set(divergentes["familia"]) <= {"CAMINHÕES", "CAMINHÕES CANA"}
    assert set(divergentes["setor"]) == {"Agro"} and set(divergentes["variante"]) == {"com_diesel"}
    assert blocos["familia"].nunique() >= 20
