"""Calculadora de amostras v8 (out/2022) reproduzida em Python: regra do potencial por família de equipamento.

Regra por família: amostras/ano = máquinas × Σ_compartimentos ⌊uso_ano / intervalo_compartimento⌋,
onde uso_ano = horas trabalhadas, ou km rodados quando horas ≤ 1 (caminhões).
Faturamento (dealer) = amostras × conversão × ticket.
"""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

TICKET_PADRAO = 1950.0
CONVERSAO_PADRAO = 0.05
ABAS_SETOR = {
    "CONST-MIN-Calc Real base prevt": "Construção/Mineração",
    "AGRO-Calc Real base preventiva": "Agro",
    "FLORESTA-Calc Real base prevent": "Florestal",
}
_ROTULOS = {
    "maquinas": ("TOTAL DE MÁQUINAS", "MÁQUINAS"),
    "horas": ("HORAS TRABALHADAS",),
    "meses": ("MESES TRABALHADOS",),
    "total": ("QUANTIDADE AMOSTRAS POR ANO",),
    "km": ("KM",),
}
_PARADA = ("PONTO DE COLETA", "TOTAL DE MÁQUINAS", "MÁQUINAS", "QUANTIDADE", "HORAS", "MESES", "KM")


def coletas_compartimento(uso_ano: float, intervalo: float) -> int:
    if not intervalo or intervalo <= 0 or uso_ano is None:
        return 0
    return math.floor(uso_ano / intervalo)


def amostras_ano(maquinas: float, uso_ano: float, intervalos: list[float]) -> float:
    return maquinas * sum(coletas_compartimento(uso_ano, i) for i in intervalos)


def amostras_3_por_compartimento(maquinas: float, n_compartimentos: int) -> float:
    return n_compartimentos * 3 * maquinas


def faturamento_dealer(amostras: float, conversao: float = CONVERSAO_PADRAO, ticket: float = TICKET_PADRAO) -> float:
    return amostras * conversao * ticket


def msc_amostras_ano(frota: float, horas_ano: float = 500, amostras_por_ciclo: float = 12, ciclo_h: float = 1000) -> float:
    """Aba MSC: amostras/ano = horas/ano ÷ ciclo × amostras por ciclo × frota."""
    return horas_ano / ciclo_h * amostras_por_ciclo * frota


def _num(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _rotulo(v) -> str:
    return " ".join(str(v).upper().split()) if v is not None else ""


def _uso(params: dict) -> float:
    horas = params.get("horas") or 0
    return horas if horas > 1 else (params.get("km") or 0)


def ler_calculadora(path: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retorna (blocos, compartimentos). Usa valores calculados da planilha só para validar a reprodução."""
    import openpyxl

    wv = openpyxl.load_workbook(path, data_only=True)
    blocos, comps = [], []
    for aba, setor in ABAS_SETOR.items():
        ws = wv[aba]
        ocorrencias: dict[int, int] = {}
        for row in ws.iter_rows():
            for cel in row:
                if _rotulo(cel.value) != "PONTO DE COLETA":
                    continue
                r, c = cel.row, cel.column
                variante_idx = ocorrencias.get(c, 0)
                ocorrencias[c] = variante_idx + 1
                params, linha_maquinas = {}, None
                for rr in range(r - 1, max(r - 9, 0), -1):
                    lab = _rotulo(ws.cell(rr, c).value)
                    for k, pref in _ROTULOS.items():
                        if k not in params and any(lab.startswith(p) for p in pref):
                            params[k] = _num(ws.cell(rr, c + 2).value)
                            if k == "maquinas":
                                linha_maquinas = rr
                familia = ws.cell(linha_maquinas - 1, c).value if linha_maquinas else None
                detalhe = ws.cell(linha_maquinas - 1, c + 1).value if linha_maquinas else None
                detalhe = None if _num(detalhe) is not None else detalhe
                uso = _uso(params)
                linhas = []
                for rr in range(r + 1, r + 16):
                    lab = _rotulo(ws.cell(rr, c).value)
                    if not lab:
                        continue
                    proximo = _rotulo(ws.cell(rr + 1, c).value)
                    if (any(lab.startswith(p) for p in _PARADA) or lab == _rotulo(familia)
                            or any(proximo.startswith(p) for p in _ROTULOS["maquinas"])):
                        break
                    intervalo = _num(ws.cell(rr, c + 1).value)
                    coletas_planilha = _num(ws.cell(rr, c + 2).value)
                    linhas.append((rr, str(ws.cell(rr, c).value).strip(), intervalo, coletas_planilha))
                # "3 amostra/comp.ano" fica na coluna do intervalo, logo após o bloco "com diesel"
                tres = None
                for rr in range(r + 1, r + 16):
                    if _rotulo(ws.cell(rr, c + 1).value).startswith("3 AMOSTRA"):
                        tres = _num(ws.cell(rr, c + 2).value)
                        break
                maquinas = params.get("maquinas") or 0
                calc = sum(coletas_compartimento(uso, i) if i else (cp or 0) for _, _, i, cp in linhas) * maquinas
                variante = ["sem_diesel", "com_diesel"][min(variante_idx, 1)]
                blocos.append({
                    "aba": aba, "setor": setor, "familia": str(familia).strip() if familia else None,
                    "detalhe": detalhe, "variante": variante, "maquinas": maquinas,
                    "horas_ano": params.get("horas"), "km_ano": params.get("km"), "meses_ano": params.get("meses"),
                    "n_compartimentos": len(linhas), "amostras_ano_planilha": params.get("total"),
                    "amostras_ano_python": calc, "amostras_3_por_comp_planilha": tres if variante == "com_diesel" else None,
                })
                for rr, nome, intervalo, cp in linhas:
                    comps.append({
                        "aba": aba, "setor": setor, "familia": blocos[-1]["familia"], "variante": variante,
                        "linha": rr, "compartimento": nome, "intervalo": intervalo, "coletas_planilha": cp,
                        "coletas_python": coletas_compartimento(uso, intervalo) if intervalo else cp,
                    })
    b = pd.DataFrame(blocos)
    b["reproduz"] = (b["amostras_ano_planilha"].fillna(-1) == b["amostras_ano_python"]) | (
        b["amostras_ano_planilha"].isna() & (b["amostras_ano_python"] == 0))
    return b, pd.DataFrame(comps)
