"""Features de série temporal por entidade × mês (lags, médias móveis, sazonalidade, tendência, segmento, status).

Entrada: tabela mensal com `entidade`, `periodo` (qualquer dia do mês), `valor` e, opcionalmente, `segmento`.
Saída: uma linha por entidade × mês (do 1º mês da entidade até `ate`, meses sem registro = 0) com o alvo `valor`
e as features. **Toda feature do mês t usa só meses < t** (sem vazamento, G2); o próprio `valor` de t é só o alvo.
Os parâmetros que dependem de RN ainda não aprovada (janelas, status/RN-03/RN-04) ficam em `ParametrosSeries`.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from src.features.regras import ParametrosRecorrencia, classificar_clientes, completar_meses, inicio_mes

SEM_HISTORICO = "sem_historico"


@dataclass(frozen=True)
class ParametrosSeries:
    lags: tuple[int, ...] = (1, 2, 3, 12)
    janelas_mm: tuple[int, ...] = (3, 12)
    janela_tendencia: int = 6                 # tendência curta: inclinação (OLS) dos últimos N meses anteriores
    janela_completa: bool = True              # True: média móvel só com a janela cheia; False: aceita janela parcial
    incluir_status: bool = True               # status depende de RN-03/RN-04 (churn "a validar"): pode ser desligado
    recorrencia: ParametrosRecorrencia = field(default_factory=ParametrosRecorrencia)


def _inclinacao(janela: np.ndarray) -> float:
    """Inclinação por mês da reta de mínimos quadrados; NaN se a janela tiver NaN."""
    if np.isnan(janela).any():
        return np.nan
    x = np.arange(len(janela), dtype=float)
    return float(np.polyfit(x, janela, 1)[0])


def _features_numericas(g: pd.Series, p: ParametrosSeries) -> pd.DataFrame:
    """Features de uma entidade; `g` é a série mensal contínua. Tudo parte de `anterior` = valor deslocado 1 mês."""
    anterior = g.shift(1)
    out = {}
    for k in p.lags:
        out[f"lag_{k}"] = g.shift(k)
    for w in p.janelas_mm:
        out[f"mm_{w}"] = anterior.rolling(w, min_periods=w if p.janela_completa else 1).mean()
    out[f"tendencia_{p.janela_tendencia}"] = anterior.rolling(p.janela_tendencia).apply(_inclinacao, raw=True)
    return pd.DataFrame(out, index=g.index)


def _status_por_mes(base: pd.DataFrame, p: ParametrosSeries) -> pd.Series:
    """Classe do cliente (RN-03/RN-04) no fim do mês anterior a cada mês, via `classificar_clientes`."""
    mensal = base.rename(columns={"entidade": "cliente"})[["cliente", "periodo", "valor"]]
    partes = []
    for mes in sorted(base["periodo"].unique()):
        mes = pd.Timestamp(mes)
        corte = mes - pd.Timedelta(days=1)
        hist = mensal[mensal["periodo"] < mes]
        alvo = base.loc[base["periodo"] == mes, ["entidade"]]
        if hist.empty:
            classe = pd.Series(SEM_HISTORICO, index=alvo["entidade"])
        else:
            cl = classificar_clientes(hist, corte, p.recorrencia).set_index("cliente")["classe"]
            classe = alvo["entidade"].map(cl).fillna(SEM_HISTORICO)
            classe.index = alvo["entidade"]
        partes.append(pd.DataFrame({"entidade": alvo["entidade"].to_numpy(), "periodo": mes,
                                    "status": classe.to_numpy()}))
    return pd.concat(partes, ignore_index=True)


def gerar_features(mensal: pd.DataFrame, ate: str | pd.Timestamp | None = None,
                   p: ParametrosSeries = ParametrosSeries()) -> pd.DataFrame:
    """Tabela entidade × mês com `valor` (alvo) e features; ver o docstring do módulo.

    Colunas: entidade, periodo, valor, segmento (se houver), lag_*, mm_*, tendencia_*, mes_sin, mes_cos, status.
    """
    df = mensal.assign(periodo=inicio_mes(mensal["periodo"]))
    ate = None if ate is None else pd.Timestamp(ate)
    base = completar_meses(df.rename(columns={"entidade": "cliente"}), ate=ate).rename(columns={"cliente": "entidade"})
    base = base.sort_values(["entidade", "periodo"], ignore_index=True)

    if "segmento" in df:
        seg = (df.sort_values("periodo").dropna(subset=["segmento"])
               .drop_duplicates(["entidade", "periodo"], keep="last")[["entidade", "periodo", "segmento"]])
        base = base.merge(seg, on=["entidade", "periodo"], how="left")
        base["segmento"] = base.groupby("entidade")["segmento"].ffill()  # atributo: último conhecido, sem olhar o futuro

    num = base.groupby("entidade", sort=False)["valor"].apply(lambda s: _features_numericas(s, p))
    base = pd.concat([base, num.reset_index(level=0, drop=True)], axis=1)

    mes = base["periodo"].dt.month
    base["mes_sin"] = np.sin(2 * np.pi * mes / 12)   # calendário conhecido com antecedência: não é vazamento
    base["mes_cos"] = np.cos(2 * np.pi * mes / 12)

    if p.incluir_status:
        base = base.merge(_status_por_mes(base, p), on=["entidade", "periodo"], how="left")
    return base
