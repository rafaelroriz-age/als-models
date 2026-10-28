"""T16/T29: KPI 1 Potencial por benchmark de similares e % Achieved (D6, D10, RN-07) sobre a tabela-base da T14.

Entrada: <dados>/base/ (base_equipamento_mes, base_cliente_mes). Frota = equipamentos **ativos** (T05: coleta nos
12 meses até o corte; a flag `ativo` do S360 não está na tabela-base). Família do equipamento: opcional, em
<dados>/potencial/bruto/equipamento_familia.parquet [equipamento_id, familia]; sem esse arquivo todos os
equipamentos ficam na família `todas` e "similar" = segmento × porte (registrado no relatório).
Potencial anual = Σ família: n_equip × taxa de benchmark (quantil 0,75 dos similares, `potencial.py`);
potencial_p10/p90 = bootstrap de clientes do benchmark (incerteza por ter poucos similares no grupo).
Saída: <dados>/potencial/{potencial_cliente,potencial_linhas,distribuicao_segmento,sensibilidade}.parquet e
relatorio.json. Só leitura de arquivos locais; não acessa o Fabric.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2] if "__file__" in globals() else Path.cwd()
sys.path.insert(0, str(RAIZ))

import pandas as pd  # noqa: E402

from src.backtest.comparacao import rotular_segmento  # noqa: E402
from src.models.potencial import (ParametrosPotencial, distribuicao_por_segmento, pct_achieved,  # noqa: E402
                                  potencial_intervalo, sensibilidade, taxas_cliente)
from src.pipeline.fabric import pasta_dados, salvar_json  # noqa: E402

DADOS = pasta_dados(RAIZ)
SAIDA = DADOS / "potencial"
N_BOOT = int(os.environ.get("ALS_POTENCIAL_BOOT", "200"))
JANELA = 12   # meses: frota ativa e realizado (T05, D6)

VARIANTES = {
    "segmento×familia×porte q75 (padrão)": ParametrosPotencial(),
    "segmento×familia q75": ParametrosPotencial(dimensoes=("segmento", "familia")),
    "familia×porte q75": ParametrosPotencial(dimensoes=("familia", "porte")),
    "segmento×familia×porte q50": ParametrosPotencial(quantil=0.5),
    "segmento×familia×porte q90": ParametrosPotencial(quantil=0.9),
    "segmento×familia×porte min10": ParametrosPotencial(min_clientes=10),
}


def entradas(dados: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Timestamp, str]:
    """(frota, realizado, segmentos, equipamentos_ativos, corte, fonte_familia) na janela de 12 meses."""
    eq = pd.read_parquet(dados / "base" / "base_equipamento_mes.parquet")
    ate = eq["periodo"].max()
    corte = ate + pd.DateOffset(months=1)
    jan = eq[(eq["periodo"] > ate - pd.DateOffset(months=JANELA)) & (eq["amostras"] > 0)]
    dono = jan.sort_values("periodo").groupby("equipamento_id")["entidade"].last()
    ativos = jan.groupby("equipamento_id", as_index=False)["amostras"].sum().rename(columns={"amostras": "amostras_12m"})
    ativos["entidade"] = ativos["equipamento_id"].map(dono).astype(str)
    fam_path = dados / "potencial" / "bruto" / "equipamento_familia.parquet"
    if fam_path.exists():
        fam = pd.read_parquet(fam_path).set_index("equipamento_id")["familia"]
        ativos["familia"] = ativos["equipamento_id"].map(fam).fillna("sem_familia").astype(str)
        fonte = str(fam_path.name)
    else:
        ativos["familia"] = "todas"
        fonte = "ausente: familia = 'todas' (similar = segmento × porte)"
    frota = ativos.groupby(["entidade", "familia"], as_index=False).agg(n_equip=("equipamento_id", "nunique"))
    real = ativos.groupby(["entidade", "familia"], as_index=False)["amostras_12m"].sum()
    cli = pd.read_parquet(dados / "base" / "base_cliente_mes.parquet", columns=["entidade", "periodo", "segmento"])
    seg = (cli.dropna(subset=["segmento"]).sort_values("periodo").drop_duplicates("entidade", keep="last")
           [["entidade", "segmento"]])
    seg["segmento"] = rotular_segmento(seg["segmento"])
    return frota, real, seg, ativos, corte, fonte


def main() -> None:
    t0 = time.perf_counter()
    SAIDA.mkdir(parents=True, exist_ok=True)
    frota, real, seg, ativos, corte, fonte = entradas(DADOS)
    p = ParametrosPotencial()
    taxas = taxas_cliente(frota, real, seg, p)
    cli, linhas = potencial_intervalo(taxas, p, n_boot=N_BOOT)
    resumo = (linhas.groupby("entidade").agg(segmento=("segmento", "first"), porte=("porte", "first"),
                                             n_equip=("n_equip", "sum"), realizado_12m=("amostras_12m", "sum"),
                                             nivel=("nivel", lambda s: s.value_counts().idxmax()))
              .reset_index())
    cli = resumo.merge(cli, on="entidade", how="left")
    cli["pct_achieved"] = pct_achieved(cli["realizado_12m"], cli["potencial"])
    dist = distribuicao_por_segmento(cli)
    sens = sensibilidade(frota, real, seg, VARIANTES)

    cli.to_parquet(SAIDA / "potencial_cliente.parquet", index=False)
    linhas.to_parquet(SAIDA / "potencial_linhas.parquet", index=False)
    ativos[["equipamento_id", "entidade", "familia", "amostras_12m"]].to_parquet(
        SAIDA / "equipamentos_ativos.parquet", index=False)
    dist.reset_index().to_parquet(SAIDA / "distribuicao_segmento.parquet", index=False)
    sens.to_parquet(SAIDA / "sensibilidade.parquet", index=False)

    pct = cli["pct_achieved"].dropna()
    rel = {
        "data_corte": corte, "janela_meses": JANELA, "familia": fonte, "n_boot": N_BOOT,
        "parametros": {"dimensoes": list(p.dimensoes), "quantil": p.quantil, "min_clientes": p.min_clientes,
                       "faixas_porte": list(p.faixas_porte)},
        "clientes": int(len(cli)), "equipamentos_ativos": int(len(ativos)),
        "realizado_12m": float(cli["realizado_12m"].sum()), "potencial_total": float(cli["potencial"].sum()),
        "potencial_p10_total": float(cli["potencial_p10"].sum()),
        "potencial_p90_total": float(cli["potencial_p90"].sum()),
        "pct_achieved": {"mediana": float(pct.median()), "p25": float(pct.quantile(.25)),
                         "p75": float(pct.quantile(.75)), "acima_100": float((pct > 1).mean())},
        "nivel_similaridade": cli["nivel"].value_counts().to_dict(),
        "distribuicao_segmento": dist.round(3).reset_index().to_dict("records"),
        "sensibilidade": sens.round(4).to_dict("records"),
        "tempo_s": round(time.perf_counter() - t0, 1),
    }
    salvar_json(rel, SAIDA / "relatorio.json")
    print({k: rel[k] for k in ("clientes", "equipamentos_ativos", "potencial_total", "pct_achieved", "tempo_s")})
    print(dist.head(15).round(3).to_string())
    print(sens.round(3).to_string())


if __name__ == "__main__":
    main()
