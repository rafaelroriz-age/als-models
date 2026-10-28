import re
from pathlib import Path

import pytest

from src.serving.contrato import CONTRATOS
from src.serving.semantico import gerar as gs

DEF = gs.PASTA_MODELO / "definition"
TIPOS = {"str": "string", "int": "int64", "float": "double", "date": "dateTime", "bool": "boolean"}


def _nome(texto):
    texto = texto.strip()
    return texto[1:-1].replace("''", "'") if texto.startswith("'") else texto


def ler_tabela(texto):
    """Parser mínimo de TMDL por indentação: colunas (propriedades), medidas (DAX) e partições."""
    tab = {"colunas": {}, "medidas": {}, "particoes": {}}
    atual, corpo = None, None
    for linha in texto.splitlines():
        if not linha.strip() or linha.lstrip().startswith("///"):
            continue
        nivel = len(linha) - len(linha.lstrip("\t"))
        conteudo = linha.strip()
        if nivel == 0:
            tab["nome"] = _nome(conteudo.removeprefix("table "))
        elif nivel == 1:
            corpo = None
            m = re.match(r"(column|measure|partition) ('(?:[^']|'')+'|\S+)(?: = ?(.*))?$", conteudo)
            if not m:
                atual = None
                continue
            tipo, nome, resto = m.group(1), _nome(m.group(2)), (m.group(3) or "")
            if tipo == "column":
                atual = tab["colunas"].setdefault(nome, {})
            elif tipo == "measure":
                atual = tab["medidas"].setdefault(nome, {"dax": resto})
                corpo = "dax"
            else:
                atual = tab["particoes"].setdefault(nome, {"tipo": resto, "fonte": ""})
        elif nivel == 2 and atual is not None:
            corpo = None
            chave, _, valor = conteudo.partition(":")
            atual[chave.strip()] = valor.strip() or True
            if chave.strip() == "source =":
                corpo = "fonte"
        elif atual is not None and corpo:
            atual[corpo] = (atual.get(corpo) or "") + "\n" + conteudo
        elif atual is not None and nivel == 3:          # partição entity (DirectLake)
            chave, _, valor = conteudo.partition(":")
            atual[chave.strip()] = valor.strip()
    return tab


def ler_modelo(pasta):
    tabelas = {}
    for p in sorted((pasta / "tables").glob("*.tmdl")):
        t = ler_tabela(p.read_text(encoding="utf-8"))
        tabelas[t["nome"]] = t
    rels = re.findall(r"^relationship (\S+)\n\tfromColumn: (\w+)\.(\w+)\n\ttoColumn: (\w+)\.(\w+)",
                      (pasta / "relationships.tmdl").read_text(encoding="utf-8"), re.M)
    expr = (pasta / "expressions.tmdl").read_text(encoding="utf-8")
    return tabelas, rels, expr


@pytest.fixture(scope="module")
def modelo():
    return ler_modelo(DEF)


def test_tabelas_do_contrato_com_colunas_e_tipos(modelo):
    tabelas, _, _ = modelo
    for nome, k in CONTRATOS.items():
        assert nome in tabelas, nome
        cols = tabelas[nome]["colunas"]
        for c in k.colunas:
            assert c.nome in cols, f"{nome}.{c.nome}"
            assert cols[c.nome]["dataType"] == TIPOS[c.tipo], f"{nome}.{c.nome}"
            assert cols[c.nome]["sourceColumn"] == c.nome
        extras = set(cols) - set(k.nomes())
        assert extras == {c.nome for c in gs.DERIVADAS[nome]}, nome
        assert all(cols[e].get("isHidden") for e in extras)


def test_sem_tabela_fora_do_contrato_alem_de_dimensoes_e_medidas(modelo):
    tabelas, _, _ = modelo
    esperado = set(CONTRATOS) | {d.nome for d in gs.DIMENSOES} | {"Medidas"}
    assert set(tabelas) == esperado
    refs = re.findall(r"^ref table (\S+)", (DEF / "model.tmdl").read_text(encoding="utf-8"), re.M)
    assert set(map(_nome, refs)) == esperado


def test_colunas_de_fato_nao_somam_implicitamente(modelo):
    tabelas, _, _ = modelo
    assert "discourageImplicitMeasures" in (DEF / "model.tmdl").read_text(encoding="utf-8")
    for nome in CONTRATOS:
        assert all(c["summarizeBy"] == "none" for c in tabelas[nome]["colunas"].values()), nome


def test_import_le_parquet_da_saida_parametrizado(modelo):
    tabelas, _, expr = modelo
    for nome, k in CONTRATOS.items():
        part = tabelas[nome]["particoes"][nome]
        assert part["tipo"] == "m" and part["mode"] == "import"
        assert part["fonte"].strip() == f"base_{nome}"
        bloco = expr.split(f"expression base_{nome} =", 1)[1].split("\nexpression ", 1)[0]
        assert f'LerSaida("{k.arquivo}")' in bloco
        for c in k.colunas:
            assert f'"{c.nome}"' in bloco, f"{nome}.{c.nome} fora do SelectColumns"
    for p in ("Workspace", "Lakehouse", "PastaSaida"):
        assert re.search(rf"^expression {p} = \".*\" meta \[IsParameterQuery=true", expr, re.M), p
    assert '"Files/als_oilmodel/saida"' in expr
    assert re.search(r"OneLake & \"/\" & Workspace & \"/\" & Lakehouse & \"/\" & PastaSaida", expr)


def test_sem_credenciais_nem_endpoint():
    texto = "\n".join(p.read_text(encoding="utf-8") for p in gs.PASTA_MODELO.rglob("*") if p.is_file())
    assert not re.search(r"datawarehouse\.fabric\.microsoft\.com|pbidedicated|secret|password|senha|token",
                         texto, re.I)
    assert not re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", texto, re.I)
    for p in ("Workspace", "Lakehouse"):
        valor = re.search(rf'^expression {p} = "([^"]*)"', texto, re.M).group(1)
        assert valor.startswith("<") and valor.endswith(">"), p


def test_relacionamentos_ligam_colunas_existentes_sem_ambiguidade(modelo):
    tabelas, rels, _ = modelo
    assert len(rels) == len(gs.RELACOES)
    dims = {d.nome: d.chave for d in gs.DIMENSOES}
    pares = set()
    for _, t1, c1, t2, c2 in rels:
        assert c1 in tabelas[t1]["colunas"], f"{t1}.{c1}"
        assert c2 in tabelas[t2]["colunas"], f"{t2}.{c2}"
        assert t1 in CONTRATOS and dims.get(t2) == c2, "só fato → chave da dimensão"
        assert (t1, t2) not in pares, f"dois caminhos {t1} → {t2}"
        pares.add((t1, t2))
    ligadas = {(t1, t2) for t1, t2 in pares}
    for fato in ("forecast_consumo", "alertas"):
        assert {(fato, d) for d in ("dim_entidade", "dim_cliente", "dim_segmento", "dim_periodo")} <= ligadas
    assert {("pct_achieved", d) for d in ("dim_entidade", "dim_cliente", "dim_segmento")} <= ligadas


def test_dimensoes_tem_chave_e_calendario(modelo):
    tabelas, _, _ = modelo
    for d in gs.DIMENSOES:
        assert tabelas[d.nome]["colunas"][d.chave].get("isKey"), d.nome
    assert "dataCategory: Time" in (DEF / "tables" / "dim_periodo.tmdl").read_text(encoding="utf-8")


def test_medidas_referenciam_colunas_e_medidas_existentes(modelo):
    tabelas, _, _ = modelo
    medidas = tabelas["Medidas"]["medidas"]
    assert len(medidas) == len(gs.MEDIDAS)
    for nome, m in medidas.items():
        dax = m["dax"]
        assert dax.count("(") == dax.count(")"), nome
        for tq, tb, col in re.findall(r"(?:'([^']+)'|\b([A-Za-z_]\w*))\[([^\]]+)\]", dax):
            tabela = tq or tb
            assert tabela in tabelas and col in tabelas[tabela]["colunas"], f"{nome}: {tabela}[{col}]"
        for ref in re.findall(r"(?<![\w'\]])\[([^\]]+)\]", dax):
            assert ref in medidas, f"{nome}: [{ref}]"
        variaveis = set(re.findall(r"\bVAR\s+(\w+)", dax))
        for tabela in re.findall(r"\b(?:ISFILTERED|COUNTROWS|FILTER|CALCULATETABLE)\s*\(\s*([A-Za-z_]\w*)\s*[,)]", dax):
            assert tabela in tabelas or tabela in variaveis, f"{nome}: {tabela}"


def test_medidas_pedidas_existem(modelo):
    medidas = modelo[0]["Medidas"]["medidas"]
    for nome in ("Consumo realizado", "Consumo previsto p50", "Consumo Real", "Consumo potencial",
                 "% Achieved", "Consumo previsto p10", "Consumo previsto p90", "Potencial p10", "Potencial p90",
                 "Alertas de queda", "Alertas de churn"):
        assert nome in medidas, nome
    # D6: razão das somas de realizado_12m e potencial_12m, só com potencial > 0
    dax = medidas["% Achieved"]["dax"]
    assert "pct_achieved[realizado_12m]" in dax and "pct_achieved[potencial_12m] > 0" in dax
    assert "DIVIDE" in dax and "pct_achieved[pct_achieved]" not in dax
    # quantis não somam: p10/p90 só com uma linha no contexto
    for nome in ("Consumo previsto p10", "Consumo previsto p90", "Potencial p10", "Potencial p90"):
        assert "COUNTROWS ( _linhas ) = 1" in medidas[nome]["dax"], nome


def test_definicao_versionada_igual_ao_gerador():
    for rel, texto in gs.arquivos("import").items():
        p = gs.PASTA_MODELO / rel
        assert p.exists(), rel
        assert p.read_text(encoding="utf-8") == texto, f"{rel} desatualizado: rode python -m src.serving.semantico.gerar"


def test_variante_directlake(tmp_path):
    gs.gravar(tmp_path, "directlake")
    tabelas, rels, expr = ler_modelo(tmp_path / "definition")
    assert "expression DatabaseQuery" in expr and "LerSaida" not in expr
    for nome, t in tabelas.items():
        if nome == "Medidas":
            continue
        part = t["particoes"][nome]
        assert part["tipo"] == "entity" and part["mode"] == "directLake"
        assert part["entityName"] == gs.PREFIXO_DEV + nome
    for nome, k in CONTRATOS.items():
        assert set(k.nomes()) <= set(tabelas[nome]["colunas"])
    assert len(rels) == len(gs.RELACOES)
    with pytest.raises(ValueError):
        gs.arquivos("outro")
