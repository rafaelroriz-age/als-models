import pandas as pd

from src.pipeline.chaves import chave_erp, chave_grupo, raiz_cnpj, taxa_casamento


def test_chave_erp():
    assert chave_erp(" a123 ") == "A123"
    assert chave_erp("  ") is None and chave_erp(None) is None


def test_chave_grupo():
    assert chave_grupo("191295") == "A19129"
    assert chave_grupo("a19129") == "A19129" and chave_grupo("C76174666") == "C76174666" and chave_grupo("") is None


def test_raiz_cnpj():
    assert raiz_cnpj("12.345.678/0001-90") == "12345678"
    assert raiz_cnpj("2345678000190") == "02345678"  # zero à esquerda perdido
    assert raiz_cnpj("123") is None and raiz_cnpj("00000000000000") is None and raiz_cnpj(None) is None


def test_taxa_casamento():
    o = pd.Series(["A", "B", "C", None, "A"])
    d = pd.Series(["A", "C", None])
    r = taxa_casamento(o, d, pd.Series([1, 1, 2, 5, 1]))
    assert r == {"n_chaves": 3, "n_casam": 2, "pct": 66.67, "pct_peso": 80.0}
