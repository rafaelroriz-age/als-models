import numpy as np
import pandas as pd

from src.features.base import (ParametrosBase, cobertura_ponderada, codigo_protheus_zoho, faturamento_mensal,
                               grade_mensal, limpar_amostras, mapa_zoho, mapear_protheus, mapear_s360, montar_base,
                               oportunidades_mensal, raiz_cnpj)
from src.gates.checks import avaliar_g1

ATE = pd.Timestamp("2026-09-01")


def _zoho():
    return pd.DataFrame({
        "zoho_id": ["z1", "z2", "z3", "z4"],
        "cnpj": ["02502844000166", "1417222000339", "123.456.789-01", None],
        "erp_id": ["192936", "900067", "A63989", None],
        "conta": ["RUMO - MALHA NORTE - SAO PAULO/SP - A19079", "MRS LOGISTICA - MATRIZ - A1952101",
                  "COSAN MOOVE - SP - A63989", "SEM CODIGO"],
        "segmento": ["Railway", "N/A", "Lubricants", None],
    })


def _clientes():
    return pd.DataFrame({"cliente_id": [1, 2, 3, 4, 5],
                         "id_cigam": ["192936", None, "A63989", "A70000", None],
                         "codigo_legado": ["192936", "900067", None, None, "X1"]})


def test_raiz_cnpj_restaura_zeros_e_rejeita_cpf():
    r = raiz_cnpj(pd.Series(["02502844000166", "1417222000339", "123.456.789-01", None, "00000000000000"]))
    assert r.tolist()[:2] == ["02502844", "01417222"]
    assert r.iloc[2:].isna().all()


def test_codigo_protheus_vem_do_erp_ou_do_sufixo_da_conta():
    z = _zoho()
    cod = codigo_protheus_zoho(z["erp_id"], z["conta"])
    assert cod.tolist()[:3] == ["A19079", "A19521", "A63989"]  # sufixo, sufixo com loja, erp_id
    assert pd.isna(cod.iloc[3])


def test_ponte_s360_e_protheus_caem_na_mesma_entidade():
    z = mapa_zoho(_zoho())
    assert z["segmento"].isna().iloc[1]                      # "N/A" vira nulo
    ms = mapear_s360(_clientes(), z).set_index("cliente_id")
    assert ms.loc[1, "entidade"] == "02502844" and ms.loc[1, "regra"] == "zoho_erp"
    assert ms.loc[2, "entidade"] == "01417222"               # pelo codigo_legado
    assert ms.loc[4, "entidade"] == "protheus:A70000" and ms.loc[4, "regra"] == "protheus_direto"
    assert ms.loc[5, "entidade"] == "s360:5" and ms.loc[5, "regra"] == "sem_ponte"
    mp = mapear_protheus(pd.Series(["A19079", " a19521", "A70000", "A99999"]), z, _clientes(),
                         ms.reset_index()).set_index("cod_cliente")
    assert mp.loc["A19079", "entidade"] == ms.loc[1, "entidade"]   # RUMO: S360 e Protheus juntos
    assert mp.loc["A19521", "entidade"] == ms.loc[2, "entidade"]
    assert mp.loc["A70000", "entidade"] == ms.loc[4, "entidade"]   # sem Zoho, mesmo código
    assert mp.loc["A99999", "regra"] == "sem_ponte"


def test_ponte_por_nome_so_quando_o_nome_aponta_para_uma_entidade():
    zz = _zoho().assign(razao_social=["Rumo Malha Paulista S.A.", "MRS LOGÍSTICA S/A", "Cosan Ltda", "MRS Logistica SA"])
    zz.loc[3, "cnpj"] = "99999999000199"          # mesmo nome que z2, outra raiz → ambíguo
    z = mapa_zoho(zz)
    assert z["nome"].tolist() == ["RUMO MALHA PAULISTA", "MRS LOGISTICA", "COSAN", "MRS LOGISTICA"]
    ms = mapear_s360(_clientes(), z)
    nomes = pd.Series(["RUMO MALHA PAULISTA SA", "Cosan LTDA.", "MRS Logística S/A"], index=["A00001", "A00002", "A00003"])
    mp = mapear_protheus(pd.Series(nomes.index), z, _clientes(), ms, nomes).set_index("cod_cliente")
    assert mp.loc["A00001", "entidade"] == "02502844" and mp.loc["A00001", "regra"] == "nome_zoho"
    assert mp.loc["A00002", "entidade"] == "zoho:z3"   # z3 sem CNPJ válido: entidade da própria conta
    assert mp.loc["A00003", "regra"] == "sem_ponte"   # "MRS LOGISTICA" aponta para duas raízes


def test_limpar_amostras_conta_cada_descarte_e_separa_avulsas():
    agg = pd.DataFrame({
        "cliente_id": [1, 1, 1, 1, np.nan, 9, 1, 1],
        "ano": [2026, 2026, 2026, np.nan, 2026, 2026, 2026, 2026],
        "mes": [8, 8, 9, np.nan, 8, 8, 10, 9],
        "status_data": ["coleta", "coleta", "entrada", "sem_data", "coleta", "coleta", "coleta", "fora_intervalo"],
        "avulsa": [0, 1, 0, 0, 0, 0, 0, 0],
        "n": [10, 3, 5, 7, 2, 4, 6, 1],
        "n_ids": [9, 3, 5, 7, 2, 4, 6, 1],
    })
    out, desc = limpar_amostras(agg, ATE, {1})
    assert desc == {"duplicadas": 1, "sem_data": 7, "fora_intervalo": 1, "sem_cliente": 6, "mes_incompleto": 6,
                    "avulsas": 3, "por_data_entrada": 5, "mantidas": 14}
    ago = out.set_index("periodo").loc["2026-08-01"]
    assert (ago["amostras"], ago["avulsas"]) == (9, 3)


def test_faturamento_exclui_cfop_de_remessa_e_separa_servico():
    nf = pd.DataFrame({"cod_cliente": ["A1"] * 4, "cfop": ["5933", "6102", "5922", "6554"], "ano": [2025] * 4,
                       "mes": [1] * 4, "total": [100.0, 50.0, 30.0, 20.0]})
    out, info = faturamento_mensal(nf, ParametrosBase())
    assert out[["faturamento", "faturamento_servico"]].iloc[0].tolist() == [150.0, 100.0]
    assert info == {"cfop_excluido_total": 50.0, "faturamento_total": 150.0}


def test_oportunidades_separa_abertas_ganhas_perdidas():
    deals = pd.DataFrame({"conta_id": ["z1"] * 3, "estagio": ["Qualify", "Closed Won", "Closed Lost"],
                          "ano": [2026] * 3, "mes": [3] * 3, "n": [2, 1, 4], "valor": [100.0, 40.0, 9.0],
                          "valor_ponderado": [20.0, 40.0, 0.0]})
    o = oportunidades_mensal(deals).iloc[0]
    assert (o["oport_abertas_n"], o["oport_abertas_valor_ponderado"], o["oport_ganhas_valor"], o["oport_perdidas_n"]) \
        == (2, 20.0, 40.0, 4)


def test_grade_mensal_continua_ate_o_corte():
    g = grade_mensal(pd.Series(pd.to_datetime(["2025-11-15", "2026-09-01", "2026-12-01"]), index=["a", "b", "c"]), ATE)
    assert g.groupby("entidade").size().to_dict() == {"a": 11, "b": 1}
    assert g["periodo"].max() == ATE


def test_montar_base_passa_no_g1_e_usa_nan_antes_da_fonte():
    am = pd.DataFrame({"entidade": ["e1", "e1", "e2"], "periodo": pd.to_datetime(["2024-01-01", "2024-03-01", "2026-08-01"]),
                       "amostras": [5, 2, 1], "avulsas": [1, 0, 0]})
    fat = pd.DataFrame({"entidade": ["e1", "e3"], "periodo": pd.to_datetime(["2025-01-01", "2026-09-01"]),
                        "faturamento": [10.0, 7.0], "faturamento_servico": [10.0, 0.0]})
    opp = pd.DataFrame({"entidade": ["e2"], "periodo": pd.to_datetime(["2026-01-01"]), "oport_ganhas_valor": [3.0]})
    base = montar_base(am, fat, opp, ATE, pd.DataFrame({"entidade": ["e1"], "segmento": ["Mining"]}))
    e1 = base[base["entidade"] == "e1"].set_index("periodo")
    assert len(e1) == 33 and e1.loc["2024-02-01", "amostras"] == 0
    assert np.isnan(e1.loc["2024-12-01", "faturamento"]) and e1.loc["2025-02-01", "faturamento"] == 0
    assert base.loc[base["entidade"] == "e3", "amostras"].tolist() == [0]
    assert base.loc[base["entidade"] == "e2", "tem_oportunidades"].all()
    assert all(r["ok"] for r in avaliar_g1(base, ["entidade", "periodo"], "amostras"))
    assert all(r["ok"] for r in avaliar_g1(base[base["periodo"] >= "2025-01-01"], ["entidade", "periodo"], "faturamento"))


def test_cobertura_ponderada_pelo_volume():
    mapa = pd.DataFrame({"k": ["a", "b", "c"], "regra": ["zoho", "sem_ponte", "s360"]})
    pesos = pd.DataFrame({"k": ["a", "b", "c", "d"], "v": [60.0, 30.0, 10.0, 0.0]})
    c = cobertura_ponderada(mapa, pesos, "k", "v")
    assert (c["chaves"], c["chaves_com_ponte"], c["pct_chaves"], c["pct_peso"]) == (4, 2, 50.0, 70.0)
