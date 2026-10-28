"""T32: pré-consultas SQL sobre as temp views `v_als_*` das saídas do contrato (T28).

SQL em dialeto comum a Spark SQL e T-SQL (SELECT/JOIN/GROUP BY/CASE/subconsulta escalar, sem LIMIT/TOP, sem
funções de data, sem `;` final). Os nomes das views são configuráveis: `prefixo` troca o `v_als_` (ex.: `fct_`
quando a produção criar Delta, T36) e `nomes` sobrescreve uma view específica. Só leem; nada cria ou altera objeto.
"""
from __future__ import annotations

from src.serving.contrato import ALERTAS, FORECAST_CONSUMO, PCT_ACHIEVED, CONTRATOS

PREFIXO_PADRAO = "v_als_"
_PREFIXO_CONTRATO = "v_als_"


def nomes_views(prefixo: str = PREFIXO_PADRAO, nomes: dict[str, str] | None = None) -> dict[str, str]:
    """saída do contrato → nome da view. `nomes` ({saida: nome completo}) vence o prefixo."""
    out = {n: prefixo + k.pre_consulta.removeprefix(_PREFIXO_CONTRATO) for n, k in CONTRATOS.items()}
    desconhecidas = set(nomes or {}) - set(out)
    if desconhecidas:
        raise ValueError(f"saídas desconhecidas: {sorted(desconhecidas)}")
    return {**out, **(nomes or {})}


def _lista(colunas) -> str:
    return ", ".join(colunas)


def consultas(prefixo: str = PREFIXO_PADRAO, nomes: dict[str, str] | None = None) -> dict[str, str]:
    """nome da consulta → SQL. Uma consulta por tabela do dashboard mais o resumo por entidade."""
    v = nomes_views(prefixo, nomes)
    fc, al, pa = v["forecast_consumo"], v["alertas"], v["pct_achieved"]
    return {
        # 1) tabela do dashboard: já vem no formato largo do contrato (realizado, p10/p50/p90, potencial)
        "dashboard_forecast": (
            f"SELECT {_lista(FORECAST_CONSUMO.nomes())}\n"
            f"FROM {fc}\n"
            f"WHERE data_corte = (SELECT MAX(data_corte) FROM {fc})\n"
            f"ORDER BY nivel, entidade_id, granularidade, periodo"),
        # 2) alertas abertos (queda RN-05, churn RN-06)
        "dashboard_alertas": (
            f"SELECT {_lista(ALERTAS.nomes())}\n"
            f"FROM {al}\n"
            f"ORDER BY tipo, entidade_id, periodo"),
        # 3) resumo por entidade: % Achieved (12 meses) + previsão acumulada do horizonte mensal
        "resumo_entidade": (
            "SELECT a.nivel, a.entidade_id, a.entidade_nome, a.segmento, a.n_equip,\n"
            "       a.realizado_12m, a.potencial_12m, a.pct_achieved,\n"
            "       f.prev_p10_horizonte, f.prev_p50_horizonte, f.prev_p90_horizonte, f.meses_horizonte\n"
            f"FROM {pa} a\n"
            "LEFT JOIN (\n"
            "    SELECT nivel, entidade_id,\n"
            "           SUM(prev_p10) AS prev_p10_horizonte, SUM(prev_p50) AS prev_p50_horizonte,\n"
            "           SUM(prev_p90) AS prev_p90_horizonte, COUNT(prev_p50) AS meses_horizonte\n"
            f"    FROM {fc}\n"
            f"    WHERE granularidade = 'mes' AND data_corte = (SELECT MAX(data_corte) FROM {fc})\n"
            "      AND prev_p50 IS NOT NULL\n"
            "    GROUP BY nivel, entidade_id\n"
            ") f ON f.nivel = a.nivel AND f.entidade_id = a.entidade_id\n"
            "ORDER BY a.nivel, a.entidade_id"),
        # 4) consumo mensal por segmento (realizado × previsto p50), base de gráficos agregados
        "consumo_segmento_mes": (
            "SELECT segmento, periodo, SUM(realizado) AS realizado, SUM(prev_p50) AS prev_p50\n"
            f"FROM {fc}\n"
            f"WHERE nivel = 'cliente' AND granularidade = 'mes' AND data_corte = (SELECT MAX(data_corte) FROM {fc})\n"
            "GROUP BY segmento, periodo\n"
            "ORDER BY segmento, periodo"),
    }
