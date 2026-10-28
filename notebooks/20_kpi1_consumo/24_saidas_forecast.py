"""T29: gera as saídas reais do KPI 1 no contrato da T28 (forecast Real e Potencial, % Achieved, alertas, backtest).

Modelos (docs_fabric/16 §2): KPI 1 real = LightGBM global com quantis (p10/p50/p90, `ml_global.py`) nos níveis
cliente e equipamento; segmento = bottom-up do p50 dos clientes com a largura relativa do intervalo de um LightGBM
direto nas séries de segmento (`saidas.segmento_bottom_up`). Potencial = benchmark de similares da
`23_potencial.py` (rodar antes). Alertas = regras RN-05 (queda > 20% contra o mesmo mês do ano anterior) e
RN-06 (churn por equipamento, proxy de calendário: a tabela-base não tem horímetro nem compartimento).
Cobertura: holdout de 1 origem (corte − 7 meses, horizontes 1..6) com os baselines no mesmo harness.

Entrada: <dados>/base/ (T14), <dados>/base/bruto/{zoho,nomes_protheus}.parquet (rótulos), <dados>/potencial/.
Saída: <dados>/forecast/{forecast_consumo,pct_achieved,alertas,backtest_metricas}.parquet + relatorio.json, cada
saída validada por `contrato.validar` (G4; G5 no backtest). Só leitura de arquivos locais; não acessa o Fabric.
Equipamento: modelo treinado numa amostra determinística (equipamento_id % ALS_MOD_TREINO == 0) e aplicado a
toda a frota ativa; o holdout do equipamento usa a amostra ALS_AMOSTRA_MOD (mesma regra da T15).
"""
from __future__ import annotations

import gc
import os
import sys
import time
from dataclasses import replace
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2] if "__file__" in globals() else Path.cwd()
sys.path.insert(0, str(RAIZ))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.backtest.comparacao import ids_ativos, rotular_segmento, tabela_comparativa  # noqa: E402
from src.backtest.harness import rolling_origin  # noqa: E402
from src.backtest.snapshot import versao_dados  # noqa: E402
from src.models.baselines import ingenuo_sazonal, media_movel  # noqa: E402
from src.models.ml_global import ParametrosML, ml_global, prever, treinar  # noqa: E402
from src.pipeline.fabric import pasta_dados, salvar_json  # noqa: E402
from src.serving import saidas  # noqa: E402
from src.serving.contrato import aprovado, validar  # noqa: E402

DADOS = pasta_dados(RAIZ)
SAIDA = DADOS / "forecast"
H = 6
MOD_TREINO = int(os.environ.get("ALS_MOD_TREINO", "50"))
MOD_HOLDOUT = int(os.environ.get("ALS_AMOSTRA_MOD", "100"))
HIST_SAIDA = {"segmento": 24, "cliente": 24, "equipamento": 6}   # meses de realizado gravados antes do corte
TREINO_DESDE = pd.Timestamp("2019-01-01")
LOTE = int(os.environ.get("ALS_LOTE", "20000"))   # séries por bloco na previsão (memória)
P = replace(ParametrosML(), lgbm={**ParametrosML().lgbm, "n_jobs": int(os.environ.get("ALS_N_JOBS", "4"))})
MODELO = "lgbm_quantil"
BASELINES = {"ingenuo_sazonal": ingenuo_sazonal, "media_movel_3": lambda t, h: media_movel(t, h, k=3),
             "media_movel_12": lambda t, h: media_movel(t, h, k=12)}

TEMPOS: dict[str, float] = {}


class cronometro:
    def __init__(self, nome):
        self.nome = nome

    def __enter__(self):
        self.t = time.perf_counter()

    def __exit__(self, *_):
        TEMPOS[self.nome] = round(time.perf_counter() - self.t, 1)
        print(f"[{self.nome}] {TEMPOS[self.nome]} s", flush=True)


def _meses(ate, n):
    return pd.Timestamp(ate) - pd.DateOffset(months=n)


def rotulos(dados: Path) -> pd.Series:
    """entidade → nome exibido (razão social do Zoho pela raiz do CNPJ ou id Zoho; nome do Protheus)."""
    z = pd.read_parquet(dados / "base" / "bruto" / "zoho.parquet")
    nome = z["razao_social"].fillna(z["conta"])
    raiz = z["cnpj"].astype("string").str.replace(r"\D", "", regex=True).str[:8]
    m = pd.concat([pd.Series(nome.to_numpy(), index=raiz.to_numpy()),
                   pd.Series(nome.to_numpy(), index=("zoho:" + z["zoho_id"].astype(str)).to_numpy())])
    pr = pd.read_parquet(dados / "base" / "bruto" / "nomes_protheus.parquet")
    m = pd.concat([m, pd.Series(pr["nome_cliente"].to_numpy(), index=("protheus:" + pr["cod_cliente"]).to_numpy())])
    m = m[m.index.notna() & m.notna()]
    return m[~m.index.duplicated()]


def series_cliente(dados: Path) -> tuple[pd.DataFrame, pd.Series]:
    cli = pd.read_parquet(dados / "base" / "base_cliente_mes.parquet", columns=["entidade", "periodo", "amostras",
                                                                                "segmento"])
    seg = (cli.dropna(subset=["segmento"]).sort_values("periodo").drop_duplicates("entidade", keep="last")
           .set_index("entidade")["segmento"])
    seg = pd.Series(rotular_segmento(seg).to_numpy(), index=seg.index.astype(str))
    s = pd.DataFrame({"id": cli["entidade"].astype(str), "periodo": cli["periodo"], "y": cli["amostras"].astype(float)})
    return s, seg


def com_segmento(s: pd.DataFrame, seg_de: pd.Series) -> pd.DataFrame:
    return s.assign(segmento=s["id"].map(seg_de).fillna("sem_segmento").astype(str))


def recorte_treino(s: pd.DataFrame, origem: pd.Timestamp, meses_ativo: int = 36) -> pd.DataFrame:
    """Treino ≤ origem desde TREINO_DESDE, só séries com consumo nos `meses_ativo` meses até a origem."""
    vivos = ids_ativos(s, origem, meses_ativo)
    return s[s["id"].isin(vivos) & (s["periodo"] >= TREINO_DESDE) & (s["periodo"] <= origem)]


def prever_nivel(treino: pd.DataFrame, alvo_hist: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Treina o LightGBM em `treino` e prevê H meses para as séries de `alvo_hist` (em lotes)."""
    modelos, x_cols = treinar(treino, H, P)
    return prever(modelos, x_cols, alvo_hist, H, P, lote=LOTE), int(treino["id"].nunique())


def holdout(serie: pd.DataFrame, origem: pd.Timestamp, nivel: str) -> pd.DataFrame:
    """1 origem, h = 1..H: LightGBM + baselines no harness, com o mesmo recorte de treino da produção
    (séries com consumo nos 36 meses até a origem) e avaliado nos ids ativos (consumo nos 12 meses até a origem)."""
    base = serie[serie["id"].isin(ids_ativos(serie, origem, 36)) & (serie["periodo"] >= TREINO_DESDE)]
    prev = rolling_origin(base, {**BASELINES, MODELO: lambda t, h: ml_global(t, h, P)}, [origem], h=H)
    return prev[prev["id"].isin(ids_ativos(serie, origem))].assign(nivel=nivel)


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    nomes = rotulos(DADOS)
    s_cli, seg_de = series_cliente(DADOS)
    ate = s_cli["periodo"].max()
    corte = ate + pd.DateOffset(months=1)
    origem_ho = ate - pd.DateOffset(months=H)
    s_cli = com_segmento(s_cli, seg_de)
    ativos_cli = ids_ativos(s_cli, ate)
    versao = f"{MODELO}|dados:{versao_dados(s_cli[['id', 'periodo', 'y']])}"
    rel = {"data_corte": corte, "ultimo_mes": ate, "horizonte": H, "versao_modelo": versao,
           "parametros_lgbm": P.lgbm, "mod_treino_equipamento": MOD_TREINO, "mod_holdout_equipamento": MOD_HOLDOUT}

    # ---------------- cliente
    with cronometro("cliente_treino_previsao"):
        hist_cli = s_cli[s_cli["id"].isin(ativos_cli) & (s_cli["periodo"] > _meses(ate, 24))]
        prev_cli, n_treino_cli = prever_nivel(recorte_treino(s_cli, ate), hist_cli)
    # ---------------- segmento: direto (largura do intervalo) + bottom-up (p50)
    s_seg = (s_cli.groupby(["segmento", "periodo"], as_index=False)["y"].sum()
             .rename(columns={"segmento": "id"}).assign(segmento=lambda d: d["id"]))
    with cronometro("segmento_direto"):
        dir_seg = ml_global(s_seg[s_seg["periodo"] >= TREINO_DESDE], H, P)
    prev_seg = saidas.segmento_bottom_up(prev_cli, seg_de, dir_seg)

    # ---------------- equipamento
    with cronometro("equipamento_series"):
        eq = pd.read_parquet(DADOS / "base" / "base_equipamento_mes.parquet",
                             columns=["equipamento_id", "periodo", "amostras", "entidade"])
        eq = eq[eq["amostras"] > 0]
        dono = eq.sort_values("periodo").groupby("equipamento_id")["entidade"].last()
        coletas = pd.DataFrame({"id": eq["equipamento_id"].astype(str).to_numpy(), "periodo": eq["periodo"].to_numpy(),
                                "y": eq["amostras"].astype(float).to_numpy()})
        eq_ids = eq["equipamento_id"].to_numpy()
        del eq
        gc.collect()
        seg_eq = pd.Series(dono.astype(str).map(seg_de).fillna("sem_segmento").to_numpy(), index=dono.index.astype(str))
        ativos_eq = coletas.loc[coletas["periodo"] > _meses(ate, 12), "id"].unique()
        amostra_treino = coletas["id"].to_numpy()[eq_ids % MOD_TREINO == 0]
        vivos36 = coletas.loc[coletas["periodo"] > _meses(ate, 36), "id"].unique()
        treino_eq = saidas.grade_mensal(coletas[coletas["id"].isin(np.intersect1d(amostra_treino, vivos36))],
                                        _meses(ate, 35), ate)
        treino_eq = com_segmento(treino_eq, seg_eq)
        hist_eq = com_segmento(saidas.grade_mensal(coletas[coletas["id"].isin(ativos_eq)], _meses(ate, 13), ate),
                               seg_eq)
    with cronometro("equipamento_treino_previsao"):
        prev_eq, n_treino_eq = prever_nivel(treino_eq, hist_eq)
    rel["series"] = {"cliente_previstas": int(prev_cli["id"].nunique()), "cliente_treino": n_treino_cli,
                     "segmento_previstas": int(prev_seg["id"].nunique()),
                     "equipamento_previstas": int(prev_eq["id"].nunique()), "equipamento_treino": n_treino_eq}
    print(rel["series"], flush=True)

    # ---------------- holdout (cobertura e comparação com baselines)
    with cronometro("holdout"):
        ho_cli = holdout(s_cli, origem_ho, "cliente")
        amostra_ho = np.unique(coletas["id"].to_numpy()[eq_ids % MOD_HOLDOUT == 0])
        s_eq_ho = com_segmento(saidas.grade_mensal(coletas[coletas["id"].isin(amostra_ho)], _meses(ate, 47), ate),
                               seg_eq)
        ho_eq = holdout(s_eq_ho, origem_ho, "equipamento")
        # segmento: LightGBM = bottom-up dos clientes do holdout + largura do direto; baselines nas séries de segmento
        ho_seg_dir = ml_global(s_seg[(s_seg["periodo"] >= TREINO_DESDE) & (s_seg["periodo"] <= origem_ho)], H, P)
        bu = saidas.segmento_bottom_up(ho_cli[ho_cli["modelo"] == MODELO], seg_de, ho_seg_dir)
        real_seg = s_seg[["id", "periodo", "y", "segmento"]]
        ho_seg = rolling_origin(real_seg, BASELINES, [origem_ho], h=H)
        bu = bu.merge(real_seg, on=["id", "periodo"], how="inner").assign(modelo=MODELO, origem=origem_ho)
        bu["horizonte"] = (bu["periodo"].dt.year - origem_ho.year) * 12 + bu["periodo"].dt.month - origem_ho.month
        ho_seg = pd.concat([ho_seg, bu], ignore_index=True).assign(nivel="segmento")
        prev_ho = pd.concat([ho_cli, ho_eq, ho_seg], ignore_index=True)
        tab = tabela_comparativa(prev_ho, horizontes=None)
    backtest = saidas.backtest_metricas(tab, "consumo_real", origem_ho, versao)
    cob = tab[(tab["modelo"] == MODELO) & (tab["segmento"] == "TODOS")]
    rel["holdout"] = {"origem": origem_ho, "ids": {n: int(g["id"].nunique()) for n, g in prev_ho.groupby("nivel")},
                      "lgbm_todos": cob[["nivel", "horizonte", "n", "wape", "bias_pct", "cobertura"]].round(4)
                      .to_dict("records"),
                      "wape_medio_h1a6": tab[tab["segmento"] == "TODOS"].groupby(["nivel", "modelo"])["wape"].mean()
                      .round(4).reset_index().to_dict("records")}
    del ho_cli, ho_eq, ho_seg, prev_ho, s_eq_ho, treino_eq
    gc.collect()

    # ---------------- potencial (23_potencial.py)
    pot_cli = pd.read_parquet(DADOS / "potencial" / "potencial_cliente.parquet")
    linhas = pd.read_parquet(DADOS / "potencial" / "potencial_linhas.parquet")
    eq_at = pd.read_parquet(DADOS / "potencial" / "equipamentos_ativos.parquet")
    pot_eq = eq_at.merge(linhas[["entidade", "familia", "taxa_bench", "taxa_bench_p10", "taxa_bench_p90"]],
                         on=["entidade", "familia"], how="left")
    pot_eq = pd.DataFrame({"id": pot_eq["equipamento_id"].astype(str), "potencial": pot_eq["taxa_bench"],
                           "potencial_p10": pot_eq["taxa_bench_p10"], "potencial_p90": pot_eq["taxa_bench_p90"],
                           "realizado_12m": pot_eq["amostras_12m"].astype(float)})
    pc = pot_cli.rename(columns={"entidade": "id"})
    pot_seg = (pc.assign(segmento=pc["id"].map(seg_de).fillna("sem_segmento"))
               .groupby("segmento", as_index=False)[["potencial", "potencial_p10", "potencial_p90", "realizado_12m",
                                                     "n_equip"]].sum().rename(columns={"segmento": "id"}))

    # ---------------- atributos (nome, cliente dono, segmento)
    at_cli = pd.DataFrame({"entidade_nome": pd.Series(s_cli["id"].unique()).map(nomes).to_numpy(),
                           "cliente_id": s_cli["id"].unique(),
                           "segmento": pd.Series(s_cli["id"].unique()).map(seg_de).to_numpy()},
                          index=s_cli["id"].unique())
    segs = pd.Index(s_seg["id"].unique())
    at_seg = pd.DataFrame({"entidade_nome": segs, "cliente_id": None, "segmento": segs}, index=segs)
    at_eq = pd.DataFrame({"entidade_nome": None, "cliente_id": dono.astype(str).to_numpy(),
                          "segmento": seg_eq.reindex(dono.index.astype(str)).to_numpy()}, index=dono.index.astype(str))

    # ---------------- forecast_consumo
    with cronometro("montar_saidas"):
        partes = []
        for nivel, hist, prev, at, pot in (
                ("segmento", s_seg, prev_seg, at_seg, pot_seg),
                ("cliente", s_cli[s_cli["id"].isin(ativos_cli)], prev_cli, at_cli, pc),
                ("equipamento", hist_eq, prev_eq, at_eq, pot_eq)):
            h = hist[hist["periodo"] > _meses(ate, HIST_SAIDA[nivel])]
            partes.append(saidas.forecast_consumo(nivel, h, prev, corte, versao, at,
                                                  pot[["id", "potencial", "potencial_p10", "potencial_p90"]]))
        fc = pd.concat(partes, ignore_index=True)
        del partes, hist_eq
        gc.collect()
        pct = pd.concat([
            saidas.pct_achieved("segmento", pot_seg.rename(columns={"potencial": "potencial_12m"}), corte, at_seg),
            saidas.pct_achieved("cliente", pc.rename(columns={"potencial": "potencial_12m"}), corte, at_cli),
            saidas.pct_achieved("equipamento", pot_eq.rename(columns={"potencial": "potencial_12m"}), corte, at_eq),
        ], ignore_index=True)
        alertas = pd.concat([saidas.alertas_queda(s_cli, ate, at_cli), saidas.alertas_churn(coletas, corte, at_eq)],
                            ignore_index=True)

    resultados = {}
    for nome, df in (("forecast_consumo", fc), ("pct_achieved", pct), ("alertas", alertas),
                     ("backtest_metricas", backtest)):
        with cronometro(f"validar_gravar_{nome}"):
            res = validar(nome, df)
            df.to_parquet(SAIDA / f"{nome}.parquet", index=False)
        falhas = [r for r in res if not r["ok"]]
        resultados[nome] = {"linhas": int(len(df)), "g4_ok": aprovado(res), "checagens": len(res), "falhas": falhas}
        print(nome, len(df), "G4 ok" if aprovado(res) else "G4 FALHOU", falhas, flush=True)

    fut = fc[fc["periodo"] >= corte]
    rel["contagens"] = {
        "forecast_consumo_por_nivel": fc.groupby("nivel").agg(linhas=("periodo", "size"),
                                                              entidades=("entidade_id", "nunique")).to_dict("index"),
        "p50_horizonte_por_nivel": fut.groupby("nivel")["prev_p50"].sum().round(1).to_dict(),
        "pct_achieved_por_nivel": pct.groupby("nivel")["pct_achieved"].agg(["size", "median"]).round(4)
        .to_dict("index"),
        "alertas_por_tipo": alertas["tipo"].value_counts().to_dict(),
    }
    rel["validacao"] = resultados
    rel["tempos_s"] = TEMPOS
    salvar_json(rel, SAIDA / "relatorio.json")
    print(rel["contagens"], TEMPOS, flush=True)


if __name__ == "__main__":
    main()
