"""Dashboard HTML estático do forecast de consumo (protótipo H3a, T20).

Um arquivo HTML sem backend a partir de duas tabelas (CSV/parquet) com o contrato de `COLUNAS_FORECAST` e
`COLUNAS_ALERTAS`. Sem a saída do T15 em `data/`, `gerar_sintetico` produz dados sintéticos e o HTML os
marca com um aviso fixo. As consultas T-SQL que geram as mesmas tabelas no Fabric estão em `sql/`.

Uso: python -m src.serving.dashboard [--forecast f.csv --alertas a.csv] [--saida dashboard.html]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.features.alertas import ParametrosChurnCompartimento, alertar_queda, compartimento_churn

# Contrato: uma linha por nível × entidade × granularidade × período.
COLUNAS_FORECAST = {
    "nivel": "segmento | cliente | equipamento",
    "entidade_id": "id da entidade no nível",
    "entidade_nome": "rótulo exibido",
    "cliente_id": "cliente dono (vazio no nível segmento)",
    "segmento": "segmento do cliente",
    "granularidade": "mes | semana",
    "periodo": "1º dia do mês ou segunda-feira da semana (YYYY-MM-DD)",
    "realizado": "amostras coletadas (vazio em período futuro)",
    "prev_p10": "forecast Real, percentil 10 (vazio em período passado)",
    "prev_p50": "forecast Real, mediana",
    "prev_p90": "forecast Real, percentil 90",
    "potencial": "amostras potenciais do período (benchmark, T16)",
    "data_corte": "data de corte do forecast",
    "versao_modelo": "identificador do modelo/dados",
}
# Uma linha por alerta aberto.
COLUNAS_ALERTAS = {
    "tipo": "queda | churn",
    "nivel": "cliente (queda) | equipamento (churn de compartimento)",
    "entidade_id": "id da entidade",
    "entidade_nome": "rótulo exibido",
    "cliente_id": "cliente dono",
    "segmento": "segmento",
    "periodo": "mês do alerta (queda) ou mês de corte (churn)",
    "valor_atual": "queda: amostras do mês; churn: horas sem coleta",
    "valor_base": "queda: base de comparação; churn: intervalo esperado (h)",
    "variacao_pct": "queda: 1 − atual ÷ base (fração); churn: vazio",
    "detalhe": "texto curto (base usada, compartimento)",
}
SEGMENTOS = ["Mineração", "Construção", "Agro"]
MESES_HIST = 22      # histórico sintético: jan/25 .. out/26
MESES_PREV = 6       # nov/26 .. abr/27
CORTE = pd.Timestamp("2026-11-01")
_VALORES = ["realizado", "prev_p10", "prev_p50", "prev_p90", "potencial"]


def _validar(df: pd.DataFrame, colunas: dict, nome: str) -> None:
    falta = [c for c in colunas if c not in df.columns]
    if falta:
        raise ValueError(f"{nome}: colunas ausentes {falta}")


def _serie(rng, gran, nivel, ent_id, nome, c, ideal, real, pot, meses) -> pd.DataFrame:
    if gran == "mes":
        per, fator = meses, 1.0
        idx = np.arange(len(per))
    else:  # semanas: 26 passadas + 26 futuras em torno do corte; mês dividido por 4,345
        per = pd.date_range(CORTE - pd.Timedelta(weeks=26), periods=52, freq="W-MON")
        fator = 1 / 4.345
        idx = np.clip(meses.searchsorted(per.to_period("M").to_timestamp()), 0, len(meses) - 1)
    passado = per < CORTE
    realizado = np.where(passado, rng.poisson(np.maximum(real[idx] * fator, 0)), np.nan)
    p50 = np.where(~passado, ideal[idx] * fator, np.nan)
    ampl = (0.18 if gran == "mes" else 0.35) * (1 + np.arange(len(per)) % 7 / 20)
    return pd.DataFrame({
        "nivel": nivel, "entidade_id": ent_id, "entidade_nome": nome, "cliente_id": c["id"], "segmento": c["segmento"],
        "granularidade": gran, "periodo": per.strftime("%Y-%m-%d"), "realizado": realizado,
        "prev_p10": np.round(p50 * (1 - 1.28 * ampl), 2), "prev_p50": np.round(p50, 2),
        "prev_p90": np.round(p50 * (1 + 1.28 * ampl), 2), "potencial": np.round(pot[idx] * fator, 2),
        "data_corte": CORTE.date().isoformat(), "versao_modelo": "sintetico-v0"})


def gerar_sintetico(seed: int = 7) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Dados SINTÉTICOS (não vêm do Fabric): 12 clientes, ~30 equipamentos, 3 segmentos."""
    rng = np.random.default_rng(seed)
    meses = pd.date_range("2025-01-01", periods=MESES_HIST + MESES_PREV, freq="MS")
    clientes = [{"id": f"C{i+1:02d}", "nome": f"Cliente {i+1:02d}", "segmento": SEGMENTOS[i % 3],
                 "nivel_mes": float(rng.integers(40, 260)), "n_eq": int(rng.integers(2, 4))} for i in range(12)]
    queda = {"C02": 0.55, "C07": 0.45}   # clientes em queda no fim do histórico (alimenta RN-05)
    linhas, eq_meta, mensal_cli = [], [], []
    for c in clientes:
        sazon = 1 + 0.15 * np.sin(2 * np.pi * (meses.month - 3) / 12)
        tend = np.where(meses >= pd.Timestamp("2026-06-01"), 1 - queda.get(c["id"], 0), 1.0)
        ideal = c["nivel_mes"] * sazon * tend
        real = rng.poisson(ideal).astype(float)
        pot_mes = np.full(len(meses), c["nivel_mes"] * 1.35)
        pesos = rng.dirichlet(np.ones(c["n_eq"]) * 3)
        mensal_cli.append(pd.DataFrame({"cliente": c["id"], "periodo": meses[:MESES_HIST], "valor": real[:MESES_HIST]}))
        niveis = [("cliente", c["id"], c["nome"], 1.0)] + [
            ("equipamento", f"{c['id']}-E{k+1}", f"{c['nome']} · EQ{k+1}", pesos[k]) for k in range(c["n_eq"])]
        for nivel, ent_id, nome, w in niveis:
            if nivel == "equipamento":
                eq_meta.append((ent_id, c["id"], nome))
            for gran in ("mes", "semana"):
                linhas.append(_serie(rng, gran, nivel, ent_id, nome, c, ideal * w, real * w, pot_mes * w, meses))
    forecast = pd.concat(linhas, ignore_index=True)
    seg = (forecast[forecast.nivel == "cliente"].groupby(["segmento", "granularidade", "periodo"], as_index=False)
           [_VALORES].sum(min_count=1))
    seg = seg.assign(nivel="segmento", entidade_id=seg.segmento, entidade_nome=seg.segmento, cliente_id="",
                     data_corte=CORTE.date().isoformat(), versao_modelo="sintetico-v0")
    forecast = pd.concat([forecast, seg[forecast.columns]], ignore_index=True)

    por_id = {c["id"]: c for c in clientes}
    q = alertar_queda(pd.concat(mensal_cli), base="ano_anterior")
    q = q[(q.periodo == meses[MESES_HIST - 1]) & q.alerta_queda]
    alertas = [{"tipo": "queda", "nivel": "cliente", "entidade_id": r.cliente, "entidade_nome": por_id[r.cliente]["nome"],
                "cliente_id": r.cliente, "segmento": por_id[r.cliente]["segmento"],
                "periodo": r.periodo.date().isoformat(), "valor_atual": r.valor, "valor_base": r.base_valor,
                "variacao_pct": r.queda, "detalhe": "base: mesmo mês do ano anterior"} for r in q.itertuples()]
    coletas = []
    for e, _, _ in eq_meta:
        for comp in ("motor", "hidraulico"):
            h = 10000 + int(rng.integers(0, 2000))
            coletas.append({"equipamento": e, "compartimento": comp, "horimetro": h, "intervalo_h": 250,
                            "horimetro_atual": h + int(rng.integers(0, 600))})
    ch = compartimento_churn(pd.DataFrame(coletas), ParametrosChurnCompartimento())
    info = {e: (c, n) for e, c, n in eq_meta}
    for r in ch[ch.compartimento_churn].itertuples():
        cid, nome = info[r.equipamento]
        alertas.append({"tipo": "churn", "nivel": "equipamento", "entidade_id": r.equipamento, "entidade_nome": nome,
                        "cliente_id": cid, "segmento": por_id[cid]["segmento"], "periodo": CORTE.date().isoformat(),
                        "valor_atual": r.horas_sem_coleta, "valor_base": r.intervalo_h, "variacao_pct": np.nan,
                        "detalhe": f"compartimento {r.compartimento}"})
    return forecast, pd.DataFrame(alertas, columns=list(COLUNAS_ALERTAS))


def _ler(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path, dtype={"cliente_id": str})


def _linhas(df: pd.DataFrame, colunas: dict) -> dict:
    df = df[list(colunas)]
    return {"cols": list(df.columns), "rows": df.astype(object).where(df.notna(), None).values.tolist()}


def montar_html(forecast: pd.DataFrame, alertas: pd.DataFrame, sintetico: bool) -> str:
    _validar(forecast, COLUNAS_FORECAST, "forecast")
    _validar(alertas, COLUNAS_ALERTAS, "alertas")
    dados = {"forecast": _linhas(forecast, COLUNAS_FORECAST), "alertas": _linhas(alertas, COLUNAS_ALERTAS),
             "sintetico": sintetico}
    modelo = (Path(__file__).parent / "dashboard.template.html").read_text(encoding="utf-8")
    return modelo.replace("__DADOS__", json.dumps(dados, ensure_ascii=False, default=float))


def main(argv=None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--forecast")
    ap.add_argument("--alertas")
    ap.add_argument("--saida", default="src/serving/exemplo/dashboard_sintetico.html")
    a = ap.parse_args(argv)
    if a.forecast and a.alertas:
        fc, al, sint = _ler(Path(a.forecast)), _ler(Path(a.alertas)), False
    else:
        fc, al, sint = *gerar_sintetico(), True
        Path("src/serving/exemplo").mkdir(parents=True, exist_ok=True)
        fc.to_csv("src/serving/exemplo/forecast_consumo_sintetico.csv", index=False)
        al.to_csv("src/serving/exemplo/alertas_sintetico.csv", index=False)
    out = Path(a.saida)
    out.write_text(montar_html(fc, al, sint), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(main())
