"""Snapshot mensal do forecast, reconstrução retroativa e erro por mês/segmento/cliente (docs_fabric/05)."""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from .harness import Modelo, metricas

COLUNAS_SNAPSHOT = ["corte", "versao_modelo", "versao_dados", "modelo", "id", "periodo", "horizonte", "yhat"]
OPCIONAIS = ["yhat_lo", "yhat_hi", "segmento"]


def versao_dados(serie: pd.DataFrame) -> str:
    """Hash curto e estável do conteúdo da série usada no forecast."""
    cols = sorted(serie.columns)
    h = pd.util.hash_pandas_object(serie[cols].sort_values(cols).reset_index(drop=True), index=False)
    return hashlib.sha256(h.values.tobytes()).hexdigest()[:12]


def _mes(s) -> pd.Series:
    return pd.to_datetime(s).dt.to_period("M").dt.to_timestamp()


def montar_snapshot(prev: pd.DataFrame, corte, modelo: str, versao_modelo: str, versao_dados_: str) -> pd.DataFrame:
    """prev [id, periodo, yhat (+ yhat_lo/yhat_hi/segmento)] → snapshot com metadados de proveniência."""
    corte = pd.Timestamp(corte).normalize()
    out = prev.copy()
    out["periodo"] = _mes(out["periodo"])
    out["horizonte"] = (out["periodo"].dt.year - corte.year) * 12 + out["periodo"].dt.month - corte.month
    out = out.assign(corte=corte, modelo=modelo, versao_modelo=versao_modelo, versao_dados=versao_dados_)
    return out[COLUNAS_SNAPSHOT + [c for c in OPCIONAIS if c in out]].reset_index(drop=True)


def gravar_snapshot(snap: pd.DataFrame, raiz: str | Path) -> Path:
    """Grava em <raiz>/corte=YYYY-MM-DD/snapshot.csv (idempotente: regrava a mesma data de corte).

    `raiz` deve ficar em data/ ou em Files/als_oilmodel/; nunca sobrescreve tabelas existentes do Fabric.
    """
    cortes = snap["corte"].dt.strftime("%Y-%m-%d").unique()
    if len(cortes) != 1:
        raise ValueError("um snapshot tem exatamente uma data de corte")
    pasta = Path(raiz) / f"corte={cortes[0]}"
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / "snapshot.csv"
    snap.to_csv(destino, index=False)
    return destino


def ler_snapshots(raiz: str | Path) -> pd.DataFrame:
    arqs = sorted(Path(raiz).glob("corte=*/snapshot.csv"))
    if not arqs:
        return pd.DataFrame(columns=COLUNAS_SNAPSHOT)
    df = pd.concat([pd.read_csv(a, parse_dates=["corte", "periodo"]) for a in arqs], ignore_index=True)
    return df


def reconstruir(serie: pd.DataFrame, modelos: dict[str, Modelo], cortes: list, h: int = 3,
                min_treino: int = 12, versao_modelo: str = "v0") -> pd.DataFrame:
    """Reexecuta cada modelo com os dados que existiam em cada data de corte passada.

    serie: [id, periodo, y] mensal, opcional `disponivel_em` (data em que a linha ficou conhecida; sem ela,
    o mês fica disponível no último dia do próprio mês) e `segmento`. O modelo recebe só linhas com
    disponivel_em ≤ corte e prevê h meses a partir do último mês fechado. Devolve snapshots empilhados.
    """
    s = serie.copy()
    s["periodo"] = _mes(s["periodo"])
    disp = pd.to_datetime(s["disponivel_em"]) if "disponivel_em" in s else s["periodo"] + pd.offsets.MonthEnd(0)
    s["_disp"] = disp
    seg = s.drop_duplicates("id").set_index("id")["segmento"] if "segmento" in s else None
    base = [c for c in s.columns if c not in ("_disp", "disponivel_em", "segmento")]
    snaps = []
    for corte in pd.to_datetime(cortes):
        visivel = s[s["_disp"] <= corte]
        treino = visivel[base]
        n = treino.groupby("id")["periodo"].nunique()
        treino = treino[treino["id"].isin(n[n >= min_treino].index)]
        if treino.empty:
            continue
        vd = versao_dados(treino)
        for nome, modelo in modelos.items():
            prev = modelo(treino, h)
            if seg is not None:
                prev = prev.assign(segmento=prev["id"].map(seg))
            snaps.append(montar_snapshot(prev, corte, nome, versao_modelo, vd))
    return pd.concat(snaps, ignore_index=True) if snaps else pd.DataFrame(columns=COLUNAS_SNAPSHOT)


def _com_realizado(snap: pd.DataFrame, serie: pd.DataFrame) -> pd.DataFrame:
    real = serie.assign(periodo=_mes(serie["periodo"]))[["id", "periodo", "y"]]
    return snap.merge(real, on=["id", "periodo"], how="inner")


def _mape(y: pd.Series, yhat: pd.Series) -> float:
    m = y != 0
    return float((np.abs(yhat[m] - y[m]) / np.abs(y[m])).mean()) if m.any() else np.nan


def erro_por(snap: pd.DataFrame, serie: pd.DataFrame, por: list[str], horizonte: int | None = None) -> pd.DataFrame:
    """MAPE/WAPE/MAE/viés agrupados por `por` (ex.: ["periodo"], ["segmento"], ["id"], ["periodo","segmento"]).

    `segmento` é lido do snapshot; se faltar na série, o agrupamento por segmento não está disponível.
    """
    df = _com_realizado(snap, serie)
    if horizonte is not None:
        df = df[df["horizonte"] == horizonte]
    rows = []
    for k, g in df.groupby(por):
        k = k if isinstance(k, tuple) else (k,)
        m = metricas(g["y"], g["yhat"])
        rows.append({**dict(zip(por, k)), "mape": _mape(g["y"], g["yhat"]), **m})
    return pd.DataFrame(rows)


def convergencia(snap: pd.DataFrame, serie: pd.DataFrame, por: list[str] | None = None) -> pd.DataFrame:
    """Erro do forecast de cada mês-alvo conforme a data de corte se aproxima do fim do mês.

    Para cada (periodo, corte): dias_para_fim = fim do mês-alvo − corte. Com `por` extra (ex.: segmento)
    agrupa também por ele. Cortes após o fim do mês-alvo são descartados.
    """
    df = _com_realizado(snap, serie)
    fim = df["periodo"] + pd.offsets.MonthEnd(0)
    df = df.assign(dias_para_fim=(fim - df["corte"]).dt.days)
    df = df[df["dias_para_fim"] >= 0]
    chaves = ["periodo", "dias_para_fim"] + (por or [])
    if df.empty:
        return pd.DataFrame(columns=chaves + ["mape", "wape", "n"])
    rows = []
    for k, g in df.groupby(chaves):
        m = metricas(g["y"], g["yhat"])
        rows.append({**dict(zip(chaves, k)), "mape": _mape(g["y"], g["yhat"]), "wape": m["wape"], "n": m["n"]})
    return pd.DataFrame(rows).sort_values(chaves).reset_index(drop=True)
