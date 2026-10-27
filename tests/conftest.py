import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

CALCULADORA = RAIZ / "Calculadora de amostras v8 - horimetros preventiva - out.2022.xlsx"
FORECAST27 = RAIZ / "Forecast 27.xlsx"
CUSTOMER_STATUS = RAIZ / "Customer Status Novo_Geral_Novas Carteiras 2026.xlsx"


def exige(path: Path):
    return pytest.mark.skipif(not path.exists(), reason=f"planilha ausente: {path.name}")
