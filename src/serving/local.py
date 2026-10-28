"""T32: saídas do contrato (T28) calculadas localmente da base real (`data/base/base_cliente_mes.parquet`).

Enquanto o notebook de saídas (T29/T30) não roda no Fabric, a base da T14 (cliente = entidade da ponte S360 → Zoho,
mensal, com segmento) alimenta o mesmo baseline ingênuo sazonal de `src.pipeline.dev` nos níveis segmento e cliente.
Equipamento, potencial e churn de compartimento ficam de fora (dependem de dados que não estão na base).
Os parquet saem validados no G4 em `pasta` (fora do git).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.backtest.comparacao import rotular_segmento
from src.pipeline import dev
from src.serving.saidas import grade_mensal


def serie_da_base(base: pd.DataFrame, desde: pd.Timestamp, corte: pd.Timestamp) -> pd.DataFrame:
    """[nivel, entidade_id, entidade_nome, cliente_id, segmento, periodo, y] mensal contínuo (zeros) da 1ª coleta
    (ou `desde`) até o mês anterior ao corte, nos níveis segmento e cliente. `base`: [entidade, periodo, amostras, segmento]."""
    b = base.assign(entidade=base["entidade"].astype(str),
                    segmento=rotular_segmento(base["segmento"]))
    seg = b.groupby("entidade")["segmento"].agg(lambda s: s.value_counts().idxmax())
    g = grade_mensal(b.rename(columns={"entidade": "id", "amostras": "y"})[["id", "periodo", "y"]], desde,
                     corte - pd.DateOffset(months=1)).rename(columns={"id": "entidade_id"})
    cli = g.assign(nivel="cliente", entidade_nome=g["entidade_id"], cliente_id=g["entidade_id"],
                   segmento=g["entidade_id"].map(seg))
    por_seg = (cli.groupby(["segmento", "periodo"], as_index=False)["y"].sum()
               .assign(nivel="segmento", entidade_id=lambda x: x["segmento"], entidade_nome=lambda x: x["segmento"],
                       cliente_id=None))
    cols = ["nivel", "entidade_id", "entidade_nome", "cliente_id", "segmento", "periodo", "y"]
    return pd.concat([por_seg[cols], cli[cols]], ignore_index=True).astype({"y": float})


def gerar_da_base(caminho: Path, pasta: Path, h: int = 12, meses_historico: int = 36,
                  corte: pd.Timestamp | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Lê a base, gera forecast_consumo/pct_achieved/alertas no contrato, valida (G4) e grava em `pasta`."""
    base = pd.read_parquet(caminho, columns=["entidade", "periodo", "amostras", "segmento"])
    com_amostra = base[base["amostras"] > 0]        # a série de cada cliente parte da 1ª coleta
    corte = corte or (com_amostra["periodo"].max() + pd.DateOffset(months=1))
    serie = serie_da_base(com_amostra, corte - pd.DateOffset(months=meses_historico), corte)
    saidas = dev.gerar(serie, corte, h)
    rel = dev.gravar(saidas, pasta)
    if rel["reprovadas"]:
        raise ValueError(f"saídas reprovadas no G4: {rel['reprovadas']} (ver {pasta / 'relatorio_dev.json'})")
    return saidas["forecast_consumo"], saidas["alertas"]
