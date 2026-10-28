"""T16: KPI 1 Potencial por benchmark de clientes similares e % Achieved (D6, D10, RN-07).

Potencial anual do cliente = Σ por família (tipo) de equipamento: frota conhecida da família × taxa de benchmark,
onde a taxa de benchmark é o quantil `quantil` das taxas (amostras/equipamento/ano) dos clientes similares.
"Similar" = mesmo grupo nas `dimensoes` (padrão: segmento × família × porte da frota). Grupo com menos de
`min_clientes` cai para o próximo nível da hierarquia, removendo a última dimensão até o global.
% Achieved (D6) = amostras realizadas nos 12 meses ÷ potencial anual.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ParametrosPotencial:
    dimensoes: tuple[str, ...] = ("segmento", "familia", "porte")
    quantil: float = 0.75
    min_clientes: int = 5
    faixas_porte: tuple[int, ...] = (5, 20, 100)   # nº de equipamentos ativos do cliente: 1–5, 6–20, 21–100, >100


def porte(n_equip: pd.Series, faixas: tuple[int, ...] = ParametrosPotencial.faixas_porte) -> pd.Series:
    """Faixa de porte pelo nº total de equipamentos da frota do cliente."""
    bordas = [0, *faixas, np.inf]
    rotulos = [f"{a + 1}-{b}" if np.isfinite(b) else f">{a}" for a, b in zip(bordas[:-1], bordas[1:])]
    return pd.cut(n_equip, bordas, labels=rotulos, right=True).astype(str)


def taxas_cliente(frota: pd.DataFrame, realizado: pd.DataFrame, segmentos: pd.DataFrame,
                  p: ParametrosPotencial = ParametrosPotencial()) -> pd.DataFrame:
    """Uma linha por entidade × família com n_equip, amostras_12m, taxa e os atributos de similaridade.

    frota: entidade, familia, n_equip. realizado: entidade, familia, amostras_12m. segmentos: entidade, segmento.
    """
    t = frota.merge(realizado, on=["entidade", "familia"], how="left").fillna({"amostras_12m": 0.0})
    t = t[t["n_equip"] > 0].copy()
    t["taxa"] = t["amostras_12m"] / t["n_equip"]
    seg = segmentos.drop_duplicates("entidade").set_index("entidade")["segmento"]
    t["segmento"] = t["entidade"].map(seg).fillna("sem_segmento").astype(str)
    t["porte"] = t["entidade"].map(porte(t.groupby("entidade")["n_equip"].sum(), p.faixas_porte))
    return t


def benchmark(taxas: pd.DataFrame, p: ParametrosPotencial = ParametrosPotencial(),
              ref: pd.DataFrame | None = None) -> pd.DataFrame:
    """Taxa de benchmark por linha de `taxas`, com o nível de similaridade usado (fallback hierárquico).

    Só clientes que coletaram na família (taxa > 0) entram no benchmark, para não puxá-lo para zero.
    `ref` (padrão: a própria `taxas`) é a população de similares; o bootstrap passa uma reamostra dela.
    """
    ref = taxas if ref is None else ref
    ref = ref[ref["taxa"] > 0]
    out = taxas.copy()
    out["taxa_bench"] = np.nan
    out["nivel"] = pd.NA
    for k in range(len(p.dimensoes), -1, -1):
        dims = list(p.dimensoes[:k])
        if dims:
            g = ref.groupby(dims)
            q = g["taxa"].quantile(p.quantil).rename("q")
            n = g["entidade"].nunique().rename("n")
            stats = pd.concat([q, n], axis=1).reset_index()
            m = out[dims].merge(stats, on=dims, how="left").set_index(out.index)
        else:
            m = pd.DataFrame({"q": ref["taxa"].quantile(p.quantil) if len(ref) else np.nan,
                              "n": ref["entidade"].nunique()}, index=out.index)
        livre = out["taxa_bench"].isna() & (m["n"] >= p.min_clientes if dims else True)
        out.loc[livre, "taxa_bench"] = m.loc[livre, "q"]
        out.loc[livre, "nivel"] = "×".join(dims) or "global"
    return out


def benchmark_bootstrap(taxas: pd.DataFrame, p: ParametrosPotencial = ParametrosPotencial(), n_boot: int = 200,
                        seed: int = 0) -> np.ndarray:
    """Matriz linhas de `taxas` × `n_boot` com a taxa de benchmark recalculada sobre reamostras de clientes.

    Cada reamostra sorteia entidades com reposição (todas as famílias da entidade juntas) e refaz `benchmark`
    com ela como população de similares: mede a incerteza do benchmark por ter poucos similares no grupo.
    """
    rng = np.random.default_rng(seed)
    ents = taxas["entidade"].unique()
    linhas = {e: np.flatnonzero(taxas["entidade"].to_numpy() == e) for e in ents}
    out = np.full((len(taxas), n_boot), np.nan)
    for b in range(n_boot):
        idx = np.concatenate([linhas[e] for e in rng.choice(ents, size=len(ents), replace=True)])
        out[:, b] = benchmark(taxas, p, ref=taxas.iloc[idx])["taxa_bench"].to_numpy()
    return out


def potencial_intervalo(taxas: pd.DataFrame, p: ParametrosPotencial = ParametrosPotencial(), n_boot: int = 200,
                        quantis: tuple[float, float] = (0.1, 0.9), seed: int = 0
                        ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(por entidade, por linha): potencial central (benchmark) e p10/p90 pelo bootstrap de `benchmark_bootstrap`.

    Por entidade: potencial, potencial_p10, potencial_p90. Por linha (entidade × família): o `benchmark` com
    taxa_bench_p10/p90. O central fica sempre dentro do intervalo (o intervalo é alargado se preciso).
    """
    b = benchmark(taxas, p)
    boot = benchmark_bootstrap(taxas, p, n_boot, seed)
    n = b["n_equip"].to_numpy()[:, None]
    pot_boot = pd.DataFrame(n * boot).groupby(b["entidade"].to_numpy()).sum(min_count=1)
    central = (b["n_equip"] * b["taxa_bench"]).groupby(b["entidade"]).sum(min_count=1)
    lo = np.nanquantile(pot_boot.to_numpy(), quantis[0], axis=1)
    hi = np.nanquantile(pot_boot.to_numpy(), quantis[1], axis=1)
    out = pd.DataFrame({"potencial": central.reindex(pot_boot.index)}, index=pot_boot.index)
    out["potencial_p10"] = np.fmin(lo, out["potencial"])
    out["potencial_p90"] = np.fmax(hi, out["potencial"])
    linhas = b.assign(taxa_bench_p10=np.fmin(np.nanquantile(boot, quantis[0], axis=1), b["taxa_bench"]),
                      taxa_bench_p90=np.fmax(np.nanquantile(boot, quantis[1], axis=1), b["taxa_bench"]))
    return out.rename_axis("entidade").reset_index(), linhas


def pct_achieved(realizado: pd.Series, potencial: pd.Series) -> pd.Series:
    """D6: realizado ÷ potencial anual; potencial nulo ou zero vira NaN."""
    return realizado / potencial.where(potencial > 0)


def potencial_cliente(frota: pd.DataFrame, realizado: pd.DataFrame, segmentos: pd.DataFrame,
                      p: ParametrosPotencial = ParametrosPotencial()) -> pd.DataFrame:
    """Uma linha por entidade: segmento, porte, n_equip, realizado_12m, potencial, pct_achieved, nivel dominante."""
    b = benchmark(taxas_cliente(frota, realizado, segmentos, p), p)
    b["potencial"] = b["n_equip"] * b["taxa_bench"]
    c = b.groupby("entidade").agg(segmento=("segmento", "first"), porte=("porte", "first"),
                                  n_equip=("n_equip", "sum"), realizado_12m=("amostras_12m", "sum"),
                                  potencial=("potencial", "sum"),
                                  nivel=("nivel", lambda s: s.value_counts().idxmax())).reset_index()
    c["pct_achieved"] = pct_achieved(c["realizado_12m"], c["potencial"])
    return c


def distribuicao_por_segmento(cli: pd.DataFrame) -> pd.DataFrame:
    """Distribuição do % Achieved por segmento (n, quartis e % acima de 100%)."""
    g = cli.dropna(subset=["pct_achieved"]).groupby("segmento")["pct_achieved"]
    return pd.DataFrame({"clientes": g.size(), "p25": g.quantile(.25), "mediana": g.median(),
                         "p75": g.quantile(.75), "acima_100": g.apply(lambda s: (s > 1).mean())}) \
        .sort_values("clientes", ascending=False)


def sensibilidade(frota: pd.DataFrame, realizado: pd.DataFrame, segmentos: pd.DataFrame,
                  variantes: dict[str, ParametrosPotencial]) -> pd.DataFrame:
    """Compara definições de "similar": potencial total, mediana do % Achieved e Spearman contra a 1ª variante."""
    res, base = [], None
    for nome, p in variantes.items():
        c = potencial_cliente(frota, realizado, segmentos, p).set_index("entidade")
        base = c if base is None else base
        res.append({"variante": nome, "potencial_total": c["potencial"].sum(),
                    "mediana_pct_achieved": c["pct_achieved"].median(),
                    "spearman_vs_base": c["potencial"].corr(base["potencial"].reindex(c.index), method="spearman")})
    return pd.DataFrame(res)
