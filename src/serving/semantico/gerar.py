"""Gera a definição TMDL do modelo semântico (entrega b, D13/D14) a partir do contrato das saídas (T28).

Uma fonte só: as tabelas fato são as de `src.serving.contrato.CONTRATOS`, com as mesmas colunas e tipos.
Modo `import` (padrão, versionado em `als_oilmodel.SemanticModel/`): Power Query lê os parquet de
`Files/als_oilmodel/saida/` no OneLake, parametrizado por workspace e lakehouse (sem ids no repositório).
Modo `directlake`: gera a variante sobre tabelas Delta `als_dev_*` (só se o Caio autorizar, T26); grava fora
do git por padrão porque exige o endpoint SQL do lakehouse.

    python -m src.serving.semantico.gerar                     # regrava a definição Import versionada
    python -m src.serving.semantico.gerar --modo directlake   # variante em data/semantico_directlake/
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from src.serving.contrato import CONTRATOS, PASTA_SAIDA

AQUI = Path(__file__).resolve().parent
PASTA_MODELO = AQUI / "als_oilmodel.SemanticModel"
RAIZ = AQUI.parents[2]
PREFIXO_DEV = "als_dev_"            # tabelas Delta descartáveis (T26), só no modo directlake

TIPO_TMDL = {"str": "string", "int": "int64", "float": "double", "date": "dateTime", "bool": "boolean"}
TIPO_M = {"str": "type text", "int": "Int64.Type", "float": "type number", "date": "type date",
          "bool": "type logical"}
FORMATO = {"date": "yyyy-mm-dd", "int": "0", "float": "#,##0.00"}

T = "\t"


@dataclass(frozen=True)
class Col:
    nome: str
    tipo: str
    descricao: str = ""
    formula_m: str | None = None       # coluna derivada no Power Query (não existe no parquet)


# Colunas derivadas: chaves de uma coluna só para os relacionamentos (o Power BI não relaciona chave composta).
_ENT = Col("entidade_chave", "str", "derivada: nivel|entidade_id, liga a dim_entidade",
           '[nivel] & "|" & [entidade_id]')
_CLI_DONO = Col("cliente_chave", "str", "derivada: o próprio id no nível cliente, senão cliente_id",
                'if [nivel] = "cliente" then [entidade_id] else [cliente_id]')
_CLI_SO = Col("cliente_chave", "str", "derivada: entidade_id no nível cliente, senão vazio",
              'if [nivel] = "cliente" then [entidade_id] else null')
DERIVADAS: dict[str, tuple[Col, ...]] = {
    "forecast_consumo": (_ENT, _CLI_DONO),
    "pct_achieved": (_ENT, _CLI_SO),
    "alertas": (_ENT, _CLI_DONO),
    "forecast_vendas": (_CLI_SO, Col("segmento_chave", "str", "derivada: entidade_id no nível segmento, senão vazio",
                                     'if [nivel] = "segmento" then [entidade_id] else null')),
    "backtest_metricas": (),
}


@dataclass(frozen=True)
class Dim:
    nome: str
    chave: str
    colunas: tuple[Col, ...]
    m: str
    descricao: str
    data: bool = False


DIMENSOES = (
    Dim("dim_entidade", "entidade_chave", (
        Col("entidade_chave", "str", "nivel|entidade_id"),
        Col("nivel", "str", "segmento | cliente | equipamento"),
        Col("entidade_id", "str"), Col("entidade_nome", "str"),
        Col("cliente_id", "str", "cliente dono (vazio no nível segmento)"), Col("segmento", "str")),
     """let
    campos = {"entidade_chave", "nivel", "entidade_id", "entidade_nome", "cliente_id", "segmento"},
    fc = Table.SelectColumns(base_forecast_consumo, campos),
    al = Table.SelectColumns(base_alertas, campos),
    pa = Table.SelectColumns(base_pct_achieved, List.RemoveItems(campos, {"cliente_id"})),
    todas = Table.Buffer(Table.Combine({fc, al, pa})),
    unicas = Table.Distinct(todas, {"entidade_chave"}),
    tipos = Table.TransformColumnTypes(unicas, {{"entidade_chave", type text}, {"nivel", type text}, {"entidade_id", type text}, {"entidade_nome", type text}, {"cliente_id", type text}, {"segmento", type text}})
in
    tipos""", "uma linha por nível × entidade presente em forecast_consumo, alertas ou pct_achieved"),
    Dim("dim_cliente", "cliente_id", (
        Col("cliente_id", "str", "raiz do CNPJ"), Col("cliente_nome", "str"), Col("segmento", "str")),
     """let
    nomeados = Table.Combine({
        Table.SelectColumns(Table.SelectRows(base_forecast_consumo, each [nivel] = "cliente"), {"entidade_id", "entidade_nome", "segmento"}),
        Table.SelectColumns(Table.SelectRows(base_pct_achieved, each [nivel] = "cliente"), {"entidade_id", "entidade_nome", "segmento"})}),
    renomeados = Table.RenameColumns(nomeados, {{"entidade_id", "cliente_id"}, {"entidade_nome", "cliente_nome"}}),
    donos = Table.Combine({
        Table.SelectColumns(base_forecast_consumo, {"cliente_chave", "segmento"}),
        Table.SelectColumns(base_alertas, {"cliente_chave", "segmento"}),
        Table.SelectColumns(base_forecast_vendas, {"cliente_chave"})}),
    sem_nome = Table.AddColumn(Table.RenameColumns(donos, {{"cliente_chave", "cliente_id"}}), "cliente_nome", each [cliente_id], type text),
    todas = Table.Buffer(Table.Combine({renomeados, sem_nome})),
    validas = Table.SelectRows(todas, each [cliente_id] <> null and [cliente_id] <> ""),
    unicas = Table.Distinct(validas, {"cliente_id"}),
    tipos = Table.TransformColumnTypes(unicas, {{"cliente_id", type text}, {"cliente_nome", type text}, {"segmento", type text}})
in
    tipos""", "clientes com nome (linhas de nível cliente) e donos citados nas demais linhas"),
    Dim("dim_segmento", "segmento", (Col("segmento", "str"),),
     """let
    listas = List.Combine({base_forecast_consumo[segmento], base_pct_achieved[segmento], base_alertas[segmento], base_forecast_vendas[segmento_chave]}),
    unicos = List.Distinct(List.Select(listas, each _ <> null and _ <> "")),
    tabela = Table.FromList(unicos, Splitter.SplitByNothing(), type table [segmento = text])
in
    tabela""", "segmentos citados nas saídas"),
    Dim("dim_periodo", "data", (
        Col("data", "date"), Col("ano", "int"), Col("trimestre", "int"), Col("mes_num", "int"),
        Col("ano_mes", "str", "AAAA-MM"), Col("inicio_mes", "date"),
        Col("inicio_semana", "date", "segunda-feira da semana (mesma convenção do contrato)")),
     """let
    datas = List.Combine({base_forecast_consumo[periodo], base_alertas[periodo], base_forecast_vendas[periodo]}),
    ini = Date.StartOfMonth(List.Min(datas)),
    fim = Date.EndOfMonth(List.Max(datas)),
    dias = List.Dates(ini, Duration.Days(fim - ini) + 1, #duration(1, 0, 0, 0)),
    base = Table.FromList(dias, Splitter.SplitByNothing(), type table [data = date]),
    ano = Table.AddColumn(base, "ano", each Date.Year([data]), Int64.Type),
    tri = Table.AddColumn(ano, "trimestre", each Date.QuarterOfYear([data]), Int64.Type),
    mes = Table.AddColumn(tri, "mes_num", each Date.Month([data]), Int64.Type),
    rotulo = Table.AddColumn(mes, "ano_mes", each Date.ToText([data], "yyyy-MM"), type text),
    inicio_mes = Table.AddColumn(rotulo, "inicio_mes", each Date.StartOfMonth([data]), type date),
    inicio_semana = Table.AddColumn(inicio_mes, "inicio_semana", each Date.StartOfWeek([data], Day.Monday), type date)
in
    inicio_semana""", "calendário diário do 1º ao último mês das saídas; marcado como tabela de datas", data=True),
)

# (tabela, coluna) → (dimensão, coluna). Só fato → dimensão, sem ligação entre dimensões: nenhum caminho ambíguo.
RELACOES = (
    ("forecast_consumo", "entidade_chave", "dim_entidade", "entidade_chave"),
    ("forecast_consumo", "cliente_chave", "dim_cliente", "cliente_id"),
    ("forecast_consumo", "segmento", "dim_segmento", "segmento"),
    ("forecast_consumo", "periodo", "dim_periodo", "data"),
    ("pct_achieved", "entidade_chave", "dim_entidade", "entidade_chave"),
    ("pct_achieved", "cliente_chave", "dim_cliente", "cliente_id"),
    ("pct_achieved", "segmento", "dim_segmento", "segmento"),
    ("alertas", "entidade_chave", "dim_entidade", "entidade_chave"),
    ("alertas", "cliente_chave", "dim_cliente", "cliente_id"),
    ("alertas", "segmento", "dim_segmento", "segmento"),
    ("alertas", "periodo", "dim_periodo", "data"),
    ("forecast_vendas", "cliente_chave", "dim_cliente", "cliente_id"),
    ("forecast_vendas", "segmento_chave", "dim_segmento", "segmento"),
    ("forecast_vendas", "periodo", "dim_periodo", "data"),
)


# ---------------------------------------------------------------- medidas DAX
@dataclass(frozen=True)
class Medida:
    nome: str
    pasta: str
    formato: str
    descricao: str
    dax: str
    oculta: bool = False


def _soma_consumo(col: str) -> str:
    return f"""VAR _nivel = [Nível ativo]
VAR _gran = [Granularidade ativa]
RETURN
    CALCULATE (
        SUM ( forecast_consumo[{col}] ),
        KEEPFILTERS ( forecast_consumo[nivel] = _nivel ),
        KEEPFILTERS ( forecast_consumo[granularidade] = _gran )
    )"""


def _quantil_consumo(col: str) -> str:
    # quantis não somam: só existe valor quando o contexto cai em exatamente uma linha (entidade × período)
    return f"""VAR _nivel = [Nível ativo]
VAR _gran = [Granularidade ativa]
VAR _linhas =
    CALCULATETABLE (
        forecast_consumo,
        KEEPFILTERS ( forecast_consumo[nivel] = _nivel ),
        KEEPFILTERS ( forecast_consumo[granularidade] = _gran ),
        NOT ISBLANK ( forecast_consumo[{col}] )
    )
RETURN
    IF ( COUNTROWS ( _linhas ) = 1, MAXX ( _linhas, forecast_consumo[{col}] ) )"""


def _soma_vendas(col: str) -> str:
    return f"""VAR _nivel = [Nível vendas ativo]
RETURN
    CALCULATE ( SUM ( forecast_vendas[{col}] ), KEEPFILTERS ( forecast_vendas[nivel] = _nivel ) )"""


def _quantil_vendas(col: str) -> str:
    return f"""VAR _nivel = [Nível vendas ativo]
VAR _linhas =
    CALCULATETABLE (
        forecast_vendas,
        KEEPFILTERS ( forecast_vendas[nivel] = _nivel ),
        NOT ISBLANK ( forecast_vendas[{col}] )
    )
RETURN
    IF ( COUNTROWS ( _linhas ) = 1, MAXX ( _linhas, forecast_vendas[{col}] ) )"""


def _ponderada_backtest(col: str) -> str:
    return f"""VAR _t = FILTER ( backtest_metricas, NOT ISBLANK ( backtest_metricas[{col}] ) )
RETURN
    DIVIDE ( SUMX ( _t, backtest_metricas[{col}] * backtest_metricas[n] ), SUMX ( _t, backtest_metricas[n] ) )"""


def _conta_alerta(expr: str, tipo: str) -> str:
    return f'CALCULATE ( {expr}, KEEPFILTERS ( alertas[tipo] = "{tipo}" ) )'


_N, _P, _R = "#,##0", "0.0%", "R$ #,##0"
_Q = "fora do total: só tem valor com uma entidade e um período no contexto (quantis não somam)"
MEDIDAS = (
    Medida("Nível ativo", "Contexto", "", "nível de forecast_consumo/pct_achieved usado pelas medidas: o nível "
           "filtrado em dim_entidade; senão cliente se houver filtro de cliente; senão segmento", """VAR _n = SELECTEDVALUE ( dim_entidade[nivel] )
RETURN
    IF ( NOT ISBLANK ( _n ), _n, IF ( ISFILTERED ( dim_cliente ), "cliente", "segmento" ) )""", oculta=True),
    Medida("Granularidade ativa", "Contexto", "", "mes por padrão; semana se filtrada em forecast_consumo[granularidade]",
           'SELECTEDVALUE ( forecast_consumo[granularidade], "mes" )', oculta=True),
    Medida("Nível vendas ativo", "Contexto", "", "cliente se houver filtro de cliente; senão segmento se houver "
           "filtro de segmento; senão total", """IF (
    ISFILTERED ( dim_cliente ),
    "cliente",
    IF ( ISFILTERED ( dim_segmento ), "segmento", "total" )
)""", oculta=True),
    Medida("Consumo realizado", "Consumo Real", _N, "amostras coletadas (períodos antes do corte)",
           _soma_consumo("realizado")),
    Medida("Consumo previsto p50", "Consumo Real", _N, "forecast Real, mediana (períodos a partir do corte)",
           _soma_consumo("prev_p50")),
    Medida("Consumo Real", "Consumo Real", _N, "realizado no passado + p50 no futuro (as colunas não se sobrepõem, "
           "contrato T28)", "[Consumo realizado] + [Consumo previsto p50]"),
    Medida("Consumo previsto p10", "Intervalo p10-p90", _N, f"forecast Real, percentil 10; {_Q}",
           _quantil_consumo("prev_p10")),
    Medida("Consumo previsto p90", "Intervalo p10-p90", _N, f"forecast Real, percentil 90; {_Q}",
           _quantil_consumo("prev_p90")),
    Medida("Amplitude do intervalo", "Intervalo p10-p90", _N, "p90 − p10 do forecast Real",
           "[Consumo previsto p90] - [Consumo previsto p10]"),
    Medida("Consumo potencial", "Potencial", _N, "potencial do período, valor central (benchmark T16)",
           _soma_consumo("potencial")),
    Medida("Potencial p10", "Potencial", _N, f"potencial, percentil 10; {_Q}", _quantil_consumo("potencial_p10")),
    Medida("Potencial p90", "Potencial", _N, f"potencial, percentil 90; {_Q}", _quantil_consumo("potencial_p90")),
    Medida("Gap para o potencial", "Potencial", _N, "potencial − consumo Real no período",
           "[Consumo potencial] - [Consumo Real]"),
    Medida("Realizado 12m", "% Achieved", _N, "amostras dos 12 meses até o corte (pct_achieved)", """VAR _nivel = [Nível ativo]
RETURN
    CALCULATE ( SUM ( pct_achieved[realizado_12m] ), KEEPFILTERS ( pct_achieved[nivel] = _nivel ) )"""),
    Medida("Potencial 12m", "% Achieved", _N, "potencial anual (benchmark)", """VAR _nivel = [Nível ativo]
RETURN
    CALCULATE ( SUM ( pct_achieved[potencial_12m] ), KEEPFILTERS ( pct_achieved[nivel] = _nivel ) )"""),
    Medida("% Achieved", "% Achieved", _P, "D6: realizado 12m ÷ potencial anual, só entidades com potencial > 0; "
           "acima de uma entidade é a razão das somas (não a média dos %)", """VAR _nivel = [Nível ativo]
VAR _base =
    CALCULATETABLE (
        pct_achieved,
        KEEPFILTERS ( pct_achieved[nivel] = _nivel ),
        KEEPFILTERS ( pct_achieved[potencial_12m] > 0 )
    )
RETURN
    DIVIDE ( SUMX ( _base, pct_achieved[realizado_12m] ), SUMX ( _base, pct_achieved[potencial_12m] ) )"""),
    Medida("Alertas abertos", "Alertas", _N, "queda (RN-05) + churn de compartimento (RN-06)", "COUNTROWS ( alertas )"),
    Medida("Alertas de queda", "Alertas", _N, "queda > 20% contra a base (RN-05)",
           _conta_alerta("COUNTROWS ( alertas )", "queda")),
    Medida("Alertas de churn", "Alertas", _N, "compartimento sem coleta acima do intervalo esperado (RN-06)",
           _conta_alerta("COUNTROWS ( alertas )", "churn")),
    Medida("Queda média", "Alertas", _P, "média de variacao_pct dos alertas de queda",
           _conta_alerta("AVERAGE ( alertas[variacao_pct] )", "queda")),
    Medida("Clientes em queda", "Alertas", _N, "clientes distintos com alerta de queda",
           _conta_alerta("DISTINCTCOUNT ( alertas[entidade_id] )", "queda")),
    Medida("Equipamentos em churn", "Alertas", _N, "equipamentos distintos com alerta de churn",
           _conta_alerta("DISTINCTCOUNT ( alertas[entidade_id] )", "churn")),
    *(Medida(f"{rotulo} {q}", "Vendas (KPI 2)", _R, f"{rotulo}, {q}" + ("" if q == "p50" else f"; {_Q}"),
             (_soma_vendas if q == "p50" else _quantil_vendas)(f"{col}_{q}"))
      for rotulo, col in (("Faturamento", "faturamento"), ("EBIT", "ebit")) for q in ("p10", "p50", "p90")),
    Medida("WAPE (backtest)", "Backtest", _P, "WAPE ponderado pelo nº de pares", _ponderada_backtest("wape")),
    Medida("Viés (backtest)", "Backtest", _P, "bias_pct ponderado pelo nº de pares", _ponderada_backtest("bias_pct")),
    Medida("Cobertura p10-p90 (backtest)", "Backtest", _P, "fração do realizado dentro de [p10, p90]",
           _ponderada_backtest("cobertura")),
    Medida("Cobertura declarada", "Backtest", _P, "cobertura nominal do intervalo (contrato T28)", "0.8"),
)


# ---------------------------------------------------------------- TMDL
def _nome(n: str) -> str:
    return n if n.replace("_", "").isalnum() and n.isascii() and not n[0].isdigit() else "'" + n.replace("'", "''") + "'"


def _bloco(texto: str, nivel: int) -> list[str]:
    return [T * nivel + linha if linha else "" for linha in texto.splitlines()]


def _desc(texto: str, nivel: int) -> list[str]:
    return [T * nivel + "/// " + texto] if texto else []


def _coluna(c: Col, chave: bool = False) -> list[str]:
    out = _desc(c.descricao, 1) + [f"{T}column {_nome(c.nome)}", f"{T * 2}dataType: {TIPO_TMDL[c.tipo]}"]
    if c.tipo in FORMATO:
        out.append(f"{T * 2}formatString: {FORMATO[c.tipo]}")
    if chave:
        out.append(f"{T * 2}isKey")
    if c.formula_m or c.nome.endswith("_chave"):
        out.append(f"{T * 2}isHidden")
    out += [f"{T * 2}summarizeBy: none", f"{T * 2}sourceColumn: {c.nome}", "",
            f"{T * 2}annotation SummarizationSetBy = User", ""]
    return out


def _colunas_fato(nome: str) -> tuple[Col, ...]:
    k = CONTRATOS[nome]
    return tuple(Col(c.nome, c.tipo, c.descricao) for c in k.colunas) + DERIVADAS[nome]


def _particao(nome: str, modo: str, m: str | None = None, entidade: str | None = None) -> list[str]:
    if modo == "directlake":
        return [f"{T}partition {_nome(nome)} = entity", f"{T * 2}mode: directLake", f"{T * 2}source",
                f"{T * 3}entityName: {entidade}", f"{T * 3}schemaName: dbo", f"{T * 3}expressionSource: DatabaseQuery",
                ""]
    return [f"{T}partition {_nome(nome)} = m", f"{T * 2}mode: import", f"{T * 2}source ="] + _bloco(m, 4) + [""]


def tabela_fato(nome: str, modo: str = "import") -> str:
    k = CONTRATOS[nome]
    linhas = [f"/// {k.granularidade} · contrato T28 ({k.pre_consulta} → {k.caminho})", f"table {_nome(nome)}", ""]
    for c in _colunas_fato(nome):
        linhas += _coluna(c)
    linhas += _particao(nome, modo, f"base_{nome}", PREFIXO_DEV + nome)
    return "\n".join(linhas)


def tabela_dim(d: Dim, modo: str = "import") -> str:
    linhas = [f"/// {d.descricao}", f"table {_nome(d.nome)}"]
    if d.data:
        linhas.append(f"{T}dataCategory: Time")
    linhas.append("")
    for c in d.colunas:
        linhas += _coluna(c, chave=c.nome == d.chave)
    linhas += _particao(d.nome, modo, d.m, PREFIXO_DEV + d.nome)
    return "\n".join(linhas)


def tabela_medidas(modo: str = "import") -> str:
    linhas = ["/// medidas do modelo; colunas das fatos ficam com summarizeBy none para não somar níveis",
              "table Medidas", ""]
    for md in MEDIDAS:
        linhas += _desc(md.descricao, 1)
        if "\n" in md.dax:
            linhas += [f"{T}measure {_nome(md.nome)} ="] + _bloco(md.dax, 3)
        else:
            linhas.append(f"{T}measure {_nome(md.nome)} = {md.dax}")
        if md.formato:
            linhas.append(f"{T * 2}formatString: {md.formato}")
        linhas.append(f"{T * 2}displayFolder: {md.pasta}")
        if md.oculta:
            linhas.append(f"{T * 2}isHidden")
        linhas.append("")
    if modo == "directlake":
        # DirectLake não mistura partição M; tabela calculada que não lê tabelas DirectLake é aceita
        return "\n".join(linhas + [
            f"{T}column vazio", f"{T * 2}dataType: string", f"{T * 2}isHidden", f"{T * 2}isNameInferred",
            f"{T * 2}summarizeBy: none", f"{T * 2}sourceColumn: [vazio]", "",
            f"{T}partition Medidas = calculated", f"{T * 2}mode: import", f'{T * 2}source = ROW ( "vazio", "" )', ""])
    linhas += [f"{T}column vazio", f"{T * 2}dataType: string", f"{T * 2}isHidden", f"{T * 2}summarizeBy: none",
               f"{T * 2}sourceColumn: vazio", ""]
    linhas += [f"{T}partition Medidas = m", f"{T * 2}mode: import", f"{T * 2}source ="]
    linhas += _bloco('let\n    vazia = #table(type table [vazio = text], {})\nin\n    vazia', 4) + [""]
    return "\n".join(linhas)


def _base_m(nome: str) -> str:
    k = CONTRATOS[nome]
    lista = ", ".join(f'"{c.nome}"' for c in k.colunas)
    tipos = ", ".join(f'{{"{c.nome}", {TIPO_M[c.tipo]}}}' for c in k.colunas)
    passos = [f'    origem = LerSaida("{k.arquivo}")', f"    colunas = Table.SelectColumns(origem, {{{lista}}})",
              f"    tipos = Table.TransformColumnTypes(colunas, {{{tipos}}})"]
    anterior = "tipos"
    for c in DERIVADAS[nome]:
        passos.append(f'    {c.nome} = Table.AddColumn({anterior}, "{c.nome}", each {c.formula_m}, {TIPO_M[c.tipo]})')
        anterior = c.nome
    return "let\n" + ",\n".join(passos) + f"\nin\n    {anterior}"


_LER_SAIDA = """(arquivo as text) as table =>
let
    pasta = OneLake & "/" & Workspace & "/" & Lakehouse & "/" & PastaSaida,
    itens = AzureStorage.DataLake(pasta, [HierarchicalNavigation = false]),
    // arquivo único (pandas) ou pasta de partes (Spark): aceita os dois
    partes = Table.SelectRows(itens, each [Extension] = ".parquet" and
        ([Name] = arquivo or Text.Contains([Folder Path], "/" & arquivo & "/"))),
    tabela = Table.Combine(List.Transform(partes[Content], Parquet.Document))
in
    tabela"""

PARAMETROS = (
    ("OneLake", "https://onelake.dfs.fabric.microsoft.com", "host público do OneLake (DFS)"),
    ("Workspace", "<nome-ou-id-do-workspace>", "workspace do lakehouse; preencher no serviço, nunca no git"),
    ("Lakehouse", "<NomeDoLakehouse.Lakehouse-ou-id>", "lakehouse existente onde fica Files/als_oilmodel/ (D13)"),
    ("PastaSaida", PASTA_SAIDA, "pasta das saídas do contrato T28"),
)


def expressoes(modo: str = "import") -> str:
    if modo == "directlake":
        return "\n".join([
            "/// DirectLake sobre o endpoint SQL do lakehouse; preencher só na cópia local, fora do git",
            "expression DatabaseQuery =",
            *_bloco('let\n    database = Sql.Database("<endpoint-sql-do-lakehouse>", "<id-do-lakehouse>")\n'
                    "in\n    database", 2),
            "", f"{T}annotation PBI_IncludeFutureArtifacts = False", ""])
    linhas: list[str] = []
    for nome, valor, desc in PARAMETROS:
        linhas += [f"/// {desc}",
                   f'expression {nome} = "{valor}" meta [IsParameterQuery=true, Type="Text", '
                   f'IsParameterQueryRequired=true]', "", f"{T}annotation PBI_ResultType = Text", ""]
    linhas += ["/// lê um parquet de PastaSaida (arquivo único ou pasta de partes)", "expression LerSaida ="]
    linhas += _bloco(_LER_SAIDA, 2) + ["", f"{T}annotation PBI_ResultType = Function", ""]
    for nome in CONTRATOS:
        linhas += [f"/// {CONTRATOS[nome].caminho} tipado pelo contrato + chaves derivadas", f"expression base_{nome} ="]
        linhas += _bloco(_base_m(nome), 2) + ["", f"{T}annotation PBI_ResultType = Table", ""]
    return "\n".join(linhas)


def relacionamentos() -> str:
    linhas: list[str] = []
    for fato, col, dim, chave in RELACOES:
        linhas += [f"relationship {fato}_{col}__{dim}", f"{T}fromColumn: {fato}.{col}", f"{T}toColumn: {dim}.{chave}", ""]
    return "\n".join(linhas)


def modelo() -> str:
    tabelas = [*CONTRATOS, *(d.nome for d in DIMENSOES), "Medidas"]
    return "\n".join([
        "model Model", f"{T}culture: pt-BR", f"{T}defaultPowerBIDataSourceVersion: powerBI_V3",
        f"{T}discourageImplicitMeasures", f"{T}sourceQueryCulture: pt-BR", "",
        *(f"ref table {_nome(t)}" for t in tabelas), ""])


def arquivos(modo: str = "import") -> dict[str, str]:
    """Caminho relativo à pasta do modelo → conteúdo."""
    if modo not in ("import", "directlake"):
        raise ValueError(f"modo desconhecido: {modo}")
    out = {
        "definition.pbism": '{\n  "version": "4.0",\n  "settings": {}\n}\n',
        "definition/database.tmdl": f"database\n{T}compatibilityLevel: 1604\n",
        "definition/model.tmdl": modelo(),
        "definition/expressions.tmdl": expressoes(modo),
        "definition/relationships.tmdl": relacionamentos(),
        "definition/tables/Medidas.tmdl": tabela_medidas(modo),
    }
    for nome in CONTRATOS:
        out[f"definition/tables/{nome}.tmdl"] = tabela_fato(nome, modo)
    for d in DIMENSOES:
        out[f"definition/tables/{d.nome}.tmdl"] = tabela_dim(d, modo)
    return out


def gravar(destino: Path, modo: str = "import") -> list[Path]:
    escritos = []
    for rel, texto in arquivos(modo).items():
        p = destino / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(texto, encoding="utf-8", newline="\n")
        escritos.append(p)
    return escritos


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--modo", choices=("import", "directlake"), default="import")
    ap.add_argument("--saida", type=Path, help="pasta destino (padrão: versionada no Import, data/ no DirectLake)")
    a = ap.parse_args(argv)
    destino = a.saida or (PASTA_MODELO if a.modo == "import" else RAIZ / "data" / "semantico_directlake"
                          / PASTA_MODELO.name)
    for p in gravar(destino, a.modo):
        print(p)


if __name__ == "__main__":
    main()
