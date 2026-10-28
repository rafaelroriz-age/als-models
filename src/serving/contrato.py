"""Contrato das saídas do projeto (T28): pré-consultas `v_als_*`, arquivos em `Files/als_oilmodel/saida/`,
colunas, tipos, chaves e validação ligada aos gates G4 (modelo → saída) e G5 (saída → consumo).

Regra da Fase 5b (docs_fabric/09 §0): nenhuma tabela permanente. Cada saída existe como (a) temp view Spark
`v_als_*` na sessão do notebook e (b) um parquet em `Files/als_oilmodel/saida/`, que o dashboard (a) e o
semântico (b, modo Import) consomem. Os nomes `fct_*` do doc 09 §1 são o alvo de produção (T36) e os `als_*`
do SQL da T20 são as entradas de cada consulta: ver o mapa em docs_fabric/10 §3.3.

Pandas puro, roda igual local e no Fabric. `validar(nome, df)` devolve `list[dict]` no formato dos gates
(`gate, checagem, alvo, ok, detalhe`).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from src.gates.checks import Resultado

PASTA_SAIDA = "Files/als_oilmodel/saida"
NIVEIS_CONSUMO = ("segmento", "cliente", "equipamento")
NIVEIS_VENDAS = ("total", "segmento", "cliente")
GRANULARIDADES = ("mes", "semana")
TIPOS_ALERTA = ("queda", "churn")
COBERTURA_DECLARADA = 0.80      # intervalo p10–p90
TOLERANCIA_COBERTURA = 0.10     # G5: cobertura empírica dentro de ±10 pp da declarada


@dataclass(frozen=True)
class Coluna:
    nome: str
    tipo: str                    # str | int | float | date | bool
    anulavel: bool = False
    descricao: str = ""
    dominio: tuple[str, ...] | None = None


@dataclass(frozen=True)
class Contrato:
    nome: str
    pre_consulta: str
    arquivo: str
    colunas: tuple[Coluna, ...]
    chave: tuple[str, ...]
    granularidade: str
    corte: str
    nao_negativas: tuple[str, ...] = ()
    # trios (p10, p50, p90) que precisam respeitar p10 <= p50 <= p90 (linhas com os três preenchidos)
    quantis: tuple[tuple[str, str, str], ...] = ()
    # colunas que só podem estar preenchidas em período passado (<) ou futuro (>=) da data de corte
    so_passado: tuple[str, ...] = ()
    so_futuro: tuple[str, ...] = ()
    coluna_periodo: str = "periodo"
    corte_unico: bool = True

    @property
    def caminho(self) -> str:
        return f"{PASTA_SAIDA}/{self.arquivo}"

    def nomes(self) -> list[str]:
        return [c.nome for c in self.colunas]


def _c(nome, tipo, anulavel=False, descricao="", dominio=None) -> Coluna:
    return Coluna(nome, tipo, anulavel, descricao, dominio)


_IDENT = (
    _c("nivel", "str", dominio=NIVEIS_CONSUMO, descricao="segmento | cliente | equipamento"),
    _c("entidade_id", "str", descricao="id no nível (raiz do CNPJ no cliente; id do equipamento)"),
    _c("entidade_nome", "str", descricao="rótulo exibido"),
    _c("cliente_id", "str", True, "cliente dono (vazio no nível segmento)"),
    _c("segmento", "str", descricao="segmento do cliente"),
)

FORECAST_CONSUMO = Contrato(
    nome="forecast_consumo",
    pre_consulta="v_als_forecast_consumo",
    arquivo="forecast_consumo.parquet",
    colunas=_IDENT + (
        _c("granularidade", "str", dominio=GRANULARIDADES),
        _c("periodo", "date", descricao="1º dia do mês ou segunda-feira da semana"),
        _c("realizado", "float", True, "amostras coletadas (vazio em período futuro)"),
        _c("prev_p10", "float", True, "forecast Real, percentil 10 (vazio em período passado)"),
        _c("prev_p50", "float", True, "forecast Real, mediana"),
        _c("prev_p90", "float", True, "forecast Real, percentil 90"),
        _c("potencial", "float", True, "potencial do período, valor central (benchmark T16)"),
        _c("potencial_p10", "float", True, "potencial, percentil 10 (incerteza do benchmark)"),
        _c("potencial_p90", "float", True, "potencial, percentil 90"),
        _c("data_corte", "date", descricao="data de corte do forecast"),
        _c("versao_modelo", "str", descricao="modelo + hash dos dados (snapshot.versao_dados)"),
    ),
    chave=("nivel", "entidade_id", "granularidade", "periodo", "data_corte"),
    granularidade="entidade × mês (ou semana) × data de corte; histórico + horizonte",
    corte="uma data_corte por arquivo (a última rodada); histórico de rodadas fica no snapshot",
    nao_negativas=("realizado", "prev_p10", "prev_p50", "prev_p90", "potencial", "potencial_p10", "potencial_p90"),
    quantis=(("prev_p10", "prev_p50", "prev_p90"), ("potencial_p10", "potencial", "potencial_p90")),
    so_passado=("realizado",),
    so_futuro=("prev_p10", "prev_p50", "prev_p90"),
)

PCT_ACHIEVED = Contrato(
    nome="pct_achieved",
    pre_consulta="v_als_pct_achieved",
    arquivo="pct_achieved.parquet",
    colunas=(
        _c("nivel", "str", dominio=NIVEIS_CONSUMO),
        _c("entidade_id", "str"),
        _c("entidade_nome", "str"),
        _c("segmento", "str"),
        _c("porte", "str", True, "faixa de porte por nº de equipamentos (potencial.porte)"),
        _c("n_equip", "int", True),
        _c("data_corte", "date"),
        _c("realizado_12m", "float", descricao="amostras dos 12 meses até o corte"),
        _c("potencial_12m", "float", True, "potencial anual (benchmark); nulo/zero → % vazio"),
        _c("pct_achieved", "float", True, "D6: realizado_12m ÷ potencial_12m (fração, pode passar de 1)"),
    ),
    chave=("nivel", "entidade_id", "data_corte"),
    granularidade="entidade × data de corte (janela de 12 meses)",
    corte="uma data_corte por arquivo",
    nao_negativas=("realizado_12m", "potencial_12m", "pct_achieved"),
)

ALERTAS = Contrato(
    nome="alertas",
    pre_consulta="v_als_alertas",
    arquivo="alertas.parquet",
    colunas=(
        _c("tipo", "str", dominio=TIPOS_ALERTA),
        _c("nivel", "str", dominio=("cliente", "equipamento"), descricao="cliente (queda) | equipamento (churn)"),
        _c("entidade_id", "str"),
        _c("entidade_nome", "str"),
        _c("cliente_id", "str", True),
        _c("segmento", "str"),
        _c("periodo", "date", descricao="mês do alerta (queda) ou mês de corte (churn)"),
        _c("valor_atual", "float", descricao="queda: amostras do mês; churn: horas sem coleta"),
        _c("valor_base", "float", descricao="queda: base de comparação; churn: intervalo esperado (h)"),
        _c("variacao_pct", "float", True, "queda: 1 − atual ÷ base (fração, > 0,20); churn: vazio"),
        _c("detalhe", "str", descricao="texto curto (base usada, compartimento)"),
    ),
    chave=("tipo", "entidade_id", "periodo", "detalhe"),
    granularidade="um alerta aberto por entidade × período (× compartimento no churn)",
    corte="mês fechado mais recente (queda) / mês de corte (churn)",
    nao_negativas=("valor_atual", "valor_base"),
    corte_unico=False,
)

FORECAST_VENDAS = Contrato(
    nome="forecast_vendas",
    pre_consulta="v_als_forecast_vendas",
    arquivo="forecast_vendas.parquet",
    colunas=(
        _c("nivel", "str", dominio=NIVEIS_VENDAS),
        _c("entidade_id", "str", descricao="'total' no nível total"),
        _c("data_corte", "date"),
        _c("periodo", "date", descricao="mês projetado (1º dia)"),
        _c("h", "int", descricao="horizonte em meses a partir do corte (1..H)"),
        _c("recorrente_base", "float", descricao="componente 1: base dos clientes recorrentes"),
        _c("nao_recorrente", "float", descricao="componente 2: clientes não recorrentes ativos"),
        _c("novos", "float", descricao="componente 3: fora do escopo (D3), 0"),
        _c("reativados", "float", descricao="componente 4: fora do escopo (D3), 0"),
        _c("churn", "float", descricao="componente 5: perda (valor positivo, subtraída no total)"),
        _c("var_mercado", "float", descricao="componente 6: variação de mercado (fração, pode ser negativa)"),
        _c("faturamento_p10", "float", True, "KPI 2: faturamento, percentil 10 (R$)"),
        _c("faturamento_p50", "float", True),
        _c("faturamento_p90", "float", True),
        _c("ebit_p10", "float", True, "KPI 2: EBIT como target separado, percentil 10 (R$)"),
        _c("ebit_p50", "float", True),
        _c("ebit_p90", "float", True),
        _c("versao_modelo", "str"),
    ),
    chave=("nivel", "entidade_id", "data_corte", "periodo"),
    granularidade="entidade × mês projetado × data de corte",
    corte="uma data_corte por arquivo (a última rodada)",
    nao_negativas=("recorrente_base", "nao_recorrente", "novos", "reativados", "churn", "faturamento_p10",
                   "faturamento_p50", "faturamento_p90"),
    quantis=(("faturamento_p10", "faturamento_p50", "faturamento_p90"), ("ebit_p10", "ebit_p50", "ebit_p90")),
)

BACKTEST_METRICAS = Contrato(
    nome="backtest_metricas",
    pre_consulta="v_als_backtest_metricas",
    arquivo="backtest_metricas.parquet",
    colunas=(
        _c("kpi", "str", dominio=("consumo_real", "consumo_potencial", "faturamento", "ebit")),
        _c("modelo", "str"),
        _c("nivel", "str", dominio=NIVEIS_CONSUMO + ("total",)),
        _c("segmento", "str", descricao="'todos' quando a métrica não é por segmento"),
        _c("horizonte", "int", descricao="meses à frente (1..H)"),
        _c("data_corte", "date", descricao="último corte avaliado no backtest"),
        _c("versao_modelo", "str"),
        _c("n", "int", descricao="pares previsto × realizado"),
        _c("wape", "float", True, "src.backtest.harness.metricas"),
        _c("mae", "float", True),
        _c("bias_pct", "float", True),
        _c("smape", "float", True),
        _c("cobertura", "float", True, "fração do realizado dentro de [p10, p90]; declarada = 0,80"),
    ),
    chave=("kpi", "modelo", "nivel", "segmento", "horizonte", "data_corte"),
    granularidade="modelo × nível × segmento × horizonte, agregando a janela rolling-origin",
    corte="data_corte = último corte do backtest; uma por arquivo",
    nao_negativas=("n", "wape", "mae", "smape"),
)

CONTRATOS: dict[str, Contrato] = {c.nome: c for c in (
    FORECAST_CONSUMO, PCT_ACHIEVED, ALERTAS, FORECAST_VENDAS, BACKTEST_METRICAS)}


# ---------------------------------------------------------------- validação
def _tipo_ok(s: pd.Series, tipo: str) -> bool:
    nn = s.dropna()
    if nn.empty:
        return True
    if tipo == "str":
        return bool(nn.map(lambda v: isinstance(v, str)).all())
    if tipo == "bool":
        return bool(nn.map(lambda v: isinstance(v, (bool, np.bool_))).all())
    if tipo == "int":
        return bool(pd.api.types.is_integer_dtype(nn) or
                    (pd.api.types.is_float_dtype(nn) and (nn == np.floor(nn)).all()))
    if tipo == "float":
        return bool(pd.api.types.is_numeric_dtype(nn) and not pd.api.types.is_bool_dtype(nn))
    if tipo == "date":
        if pd.api.types.is_datetime64_any_dtype(nn):
            return True
        return bool(pd.to_datetime(nn, errors="coerce", format="%Y-%m-%d").notna().all())
    raise ValueError(f"tipo desconhecido: {tipo}")


def _datas(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce")


def validar(nome: str, df: pd.DataFrame) -> list[dict]:
    """G4 (contrato da saída) para a saída `nome`; para `backtest_metricas` inclui também G5 (calibração)."""
    k = CONTRATOS[nome]
    out: list[Resultado] = []

    def reg(gate, checagem, alvo, ok, detalhe=""):
        out.append(Resultado(gate, checagem, f"{nome}.{alvo}" if alvo else nome, bool(ok), detalhe))

    falta = [c for c in k.nomes() if c not in df.columns]
    extra = [c for c in df.columns if c not in k.nomes()]
    reg("G4", "colunas_presentes", "", not falta, f"ausentes {falta}" if falta else f"{len(k.nomes())} colunas")
    reg("G4", "sem_colunas_extras", "", not extra, f"extras {extra}" if extra else "ok")
    if falta:
        return [asdict(r) for r in out]
    reg("G4", "nao_vazia", "", len(df) > 0, f"{len(df)} linhas")

    for c in k.colunas:
        s = df[c.nome]
        reg("G4", "tipo", c.nome, _tipo_ok(s, c.tipo), c.tipo)
        if not c.anulavel:
            n = int(s.isna().sum())
            reg("G4", "sem_nulos", c.nome, n == 0, f"{n} nulos")
        if c.dominio is not None:
            fora = sorted({str(v) for v in s.dropna().unique()} - set(c.dominio))
            reg("G4", "dominio", c.nome, not fora, f"fora do domínio {fora}" if fora else "ok")

    dup = int(df.duplicated(list(k.chave)).sum())
    reg("G4", "chave_unica", "+".join(k.chave), dup == 0, f"{dup} duplicadas")

    for c in k.nao_negativas:
        neg = int((df[c].dropna() < 0).sum())
        reg("G4", "nao_negativo", c, neg == 0, f"{neg} negativos")

    for lo, mid, hi in k.quantis:
        g = df[[lo, mid, hi]].dropna()
        ruim = int(((g[lo] > g[mid]) | (g[mid] > g[hi])).sum())
        reg("G4", "quantis_ordenados", f"{lo}<={mid}<={hi}", ruim == 0, f"{ruim} linhas fora de ordem")
        parcial = df[[lo, mid, hi]].notna().sum(axis=1)
        n_parcial = int(((parcial > 0) & (parcial < 3)).sum())
        reg("G4", "quantis_completos", f"{lo},{mid},{hi}", n_parcial == 0, f"{n_parcial} linhas com quantil faltando")

    if "data_corte" in k.nomes():
        corte = _datas(df["data_corte"])
        if k.corte_unico:
            reg("G4", "corte_unico", "data_corte", corte.nunique() == 1, f"{corte.nunique()} datas de corte")
        if (k.so_passado or k.so_futuro) and corte.nunique() == 1:
            per, c0 = _datas(df[k.coluna_periodo]), corte.iloc[0]
            for c in k.so_passado:
                n = int((df[c].notna() & (per >= c0)).sum())
                reg("G4", "so_periodo_passado", c, n == 0, f"{n} valores em período >= corte")
            for c in k.so_futuro:
                n = int((df[c].notna() & (per < c0)).sum())
                reg("G4", "so_periodo_futuro", c, n == 0, f"{n} valores em período < corte")
            if k.so_futuro:
                fut = per >= c0
                n = int((fut & df[k.so_futuro[1]].isna()).sum())
                reg("G4", "horizonte_completo", k.so_futuro[1], n == 0, f"{n} períodos futuros sem previsão")

    out.extend(_regras_especificas(nome, df))
    return [asdict(r) for r in out]


def _regras_especificas(nome: str, df: pd.DataFrame) -> list[Resultado]:
    out: list[Resultado] = []

    def reg(gate, checagem, alvo, ok, detalhe=""):
        out.append(Resultado(gate, checagem, f"{nome}.{alvo}", bool(ok), detalhe))

    if nome == "pct_achieved":
        calc = df["realizado_12m"] / df["potencial_12m"].where(df["potencial_12m"] > 0)
        ambos = df["pct_achieved"].notna() | calc.notna()
        dif = int((ambos & ~np.isclose(df["pct_achieved"], calc, rtol=1e-6, atol=1e-9, equal_nan=False)).sum())
        reg("G4", "pct_igual_realizado_sobre_potencial", "pct_achieved", dif == 0, f"{dif} linhas divergentes (D6)")
    elif nome == "alertas":
        q = df[df["tipo"] == "queda"]
        reg("G4", "queda_acima_de_20pct", "variacao_pct", bool((q["variacao_pct"] > 0.20).all()),
            f"{int((~(q['variacao_pct'] > 0.20)).sum())} quedas <= 20%")
        ch = df[df["tipo"] == "churn"]
        reg("G4", "churn_sem_variacao", "variacao_pct", bool(ch["variacao_pct"].isna().all()), "churn não tem variação")
        reg("G4", "churn_acima_do_intervalo", "valor_atual", bool((ch["valor_atual"] > ch["valor_base"]).all()),
            f"{int((~(ch['valor_atual'] > ch['valor_base'])).sum())} churns com horas <= intervalo")
    elif nome == "forecast_vendas":
        base = df["recorrente_base"] + df["nao_recorrente"] + df["novos"] + df["reativados"] - df["churn"]
        reg("G4", "total_sem_churn_negativo", "componentes", bool((base >= 0).all()),
            f"{int((base < 0).sum())} linhas com total negativo")
        reg("G4", "horizonte_a_partir_de_1", "h", bool((df["h"] >= 1).all()), "h >= 1")
        meses = _datas(df["periodo"])
        reg("G4", "periodo_inicio_de_mes", "periodo", bool((meses.dt.day == 1).all()), "1º dia do mês")
        reg("G4", "periodo_apos_corte", "periodo", bool((meses > _datas(df["data_corte"])).all()), "periodo > corte")
    elif nome == "backtest_metricas":
        com = df.dropna(subset=["cobertura"])
        fora = com[(com["cobertura"] < 0) | (com["cobertura"] > 1)]
        reg("G4", "cobertura_entre_0_e_1", "cobertura", fora.empty, f"{len(fora)} fora de [0,1]")
        desvio = (com["cobertura"] - COBERTURA_DECLARADA).abs()
        mal = int((desvio > TOLERANCIA_COBERTURA).sum())
        reg("G5", "calibracao_intervalo", "cobertura", mal == 0,
            f"{mal}/{len(com)} linhas a mais de {TOLERANCIA_COBERTURA:.0%} da declarada {COBERTURA_DECLARADA:.0%}")
    return out


def validar_todas(saidas: dict[str, pd.DataFrame]) -> list[dict]:
    """Valida cada saída presente em `saidas`; saída ausente do dicionário vira falha de G4."""
    out: list[dict] = []
    for nome in CONTRATOS:
        if nome in saidas:
            out.extend(validar(nome, saidas[nome]))
        else:
            out.append(asdict(Resultado("G4", "saida_presente", nome, False, "saída não gerada")))
    return out


def aprovado(resultados: list[dict], bloqueantes: tuple[str, ...] = ("G4",)) -> bool:
    """Publicação só segue se nenhuma checagem dos gates bloqueantes falhar (G5 é aviso por padrão)."""
    return all(r["ok"] for r in resultados if r["gate"] in bloqueantes)


def esquema_markdown() -> str:
    """Tabela markdown do contrato, para colar em docs_fabric/10 §3.3."""
    linhas = []
    for k in CONTRATOS.values():
        linhas.append(f"**{k.nome}** — `{k.pre_consulta}` → `{k.caminho}` · chave `{', '.join(k.chave)}`\n")
        linhas.append("| coluna | tipo | nulo | descrição |\n|---|---|---|---|")
        for c in k.colunas:
            linhas.append(f"| `{c.nome}` | {c.tipo} | {'sim' if c.anulavel else 'não'} | {c.descricao} |")
        linhas.append("")
    return "\n".join(linhas)
