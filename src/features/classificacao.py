"""Classificação de clientes antes da previsão (Fase 1b): regra por recorrência, recência e pirâmide.

Classes (uma por cliente):
- `recorrente`: ativo (última atividade ≤ `dias_churn`) e compra em ≥ `min_meses` dos últimos 12 meses;
- `nao_recorrente_ativo`: ativo, não recorrente, com peso na pirâmide (faturamento, nº de máquinas, potencial);
- `menor_atividade`: ativo, não recorrente e sem peso na pirâmide;
- `churn`: sem venda nem amostra há mais de `dias_churn` (ou nunca).

Entrada: colunas do Customer Status (`data/planilhas/customer_status.parquet`).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

CLASSES = ["recorrente", "nao_recorrente_ativo", "menor_atividade", "churn"]


@dataclass(frozen=True)
class ParametrosClassificacao:
    min_meses: int = 6               # recorrente: meses com compra nos últimos 12
    dias_churn: int = 180            # sem atividade além disso = churn
    min_faturamento_12m: float = 10_000.0   # pirâmide: ~P65 do faturamento 12m
    min_maquinas: float = 10.0       # pirâmide: ~mediana de equipamentos testados no ano
    min_potencial: float = 500.0     # pirâmide: ~P70 do potencial anual de amostras
    min_pontos: int = 1              # pontos da pirâmide (0–3) para ser "não recorrente ativo"


COLUNAS = {
    "ultima_venda": "Last Date Sales",
    "ultima_amostra": "Last Date Sample",
    "meses": "Recorrencia Fat",
    "faturamento": "Faturamento 12 meses",
    "maquinas": "Equipments Tested This FY",
    "potencial": "Annual Sample Potential",
}


def dias_sem_atividade(df: pd.DataFrame, referencia: pd.Timestamp) -> pd.Series:
    """Dias desde máx(última venda, última amostra); NaN se o cliente nunca teve atividade."""
    ultima = df[[COLUNAS["ultima_venda"], COLUNAS["ultima_amostra"]]].max(axis=1)
    return (pd.Timestamp(referencia) - ultima).dt.days.astype("float64")


def pontos_piramide(df: pd.DataFrame, p: ParametrosClassificacao = ParametrosClassificacao()) -> pd.Series:
    """0–3: um ponto por critério atingido (faturamento, nº de máquinas, potencial). Nulos não pontuam."""
    fat = df[COLUNAS["faturamento"]].astype("float64").fillna(0) >= p.min_faturamento_12m
    maq = df[COLUNAS["maquinas"]].astype("float64").fillna(0) >= p.min_maquinas
    pot = df[COLUNAS["potencial"]].astype("float64").fillna(0) >= p.min_potencial
    return (fat.astype(int) + maq.astype(int) + pot.astype(int)).rename("pontos_piramide")


def classificar(df: pd.DataFrame, referencia: pd.Timestamp,
                p: ParametrosClassificacao = ParametrosClassificacao()) -> pd.DataFrame:
    """Devolve `dias_sem_atividade`, `pontos_piramide` e `classe` alinhados ao índice de `df`."""
    dias = dias_sem_atividade(df, referencia)
    pontos = pontos_piramide(df, p)
    ativo = dias.le(p.dias_churn)  # NaN -> False (churn)
    recorrente = ativo & df[COLUNAS["meses"]].ge(p.min_meses)
    relevante = pontos.ge(p.min_pontos)
    classe = np.select(
        [~ativo, recorrente, relevante],
        ["churn", "recorrente", "nao_recorrente_ativo"],
        default="menor_atividade",
    )
    return pd.DataFrame({"dias_sem_atividade": dias, "pontos_piramide": pontos,
                         "classe": pd.Categorical(classe, categories=CLASSES)}, index=df.index)


def concordancia_status(classe: pd.Series, status_manual: pd.Series) -> dict:
    """Compara a regra com o `Real Status` manual (Active/Inactive/Churn), tratando churn × não churn.

    `concordancia` = fração em que (classe == churn) coincide com (status == Churn).
    """
    c = classe.astype(str).eq("churn")
    m = status_manual.astype(str).eq("Churn")
    return {
        "concordancia": float((c == m).mean()),
        "divergentes": int((c != m).sum()),
        "regra_churn_manual_ativo": int((c & ~m).sum()),
        "regra_ativo_manual_churn": int((~c & m).sum()),
        "tabela": pd.crosstab(classe, status_manual),
    }


def arvore_interpretavel(df: pd.DataFrame, referencia: pd.Timestamp, alvo: pd.Series, profundidade: int = 3,
                         cv: int = 5, seed: int = 0) -> dict:
    """Árvore rasa sobre as mesmas variáveis da regra para prever `alvo` (ex.: Real Status manual).

    Devolve acurácia em validação cruzada, texto das regras e importâncias. Serve de comparação com a regra.
    """
    from sklearn.model_selection import cross_val_score
    from sklearn.tree import DecisionTreeClassifier, export_text

    X = pd.DataFrame({
        "dias_sem_atividade": dias_sem_atividade(df, referencia).fillna(9999),
        "meses_compra_12m": df[COLUNAS["meses"]].astype("float64"),
        "faturamento_12m": df[COLUNAS["faturamento"]].astype("float64").fillna(0),
        "maquinas": df[COLUNAS["maquinas"]].astype("float64").fillna(0),
        "potencial": df[COLUNAS["potencial"]].astype("float64").fillna(0),
    })
    y = alvo.astype(str)
    arv = DecisionTreeClassifier(max_depth=profundidade, min_samples_leaf=20, random_state=seed)
    acuracia = cross_val_score(arv, X, y, cv=cv).mean()
    arv.fit(X, y)
    return {
        "acuracia_cv": float(acuracia),
        "regras": export_text(arv, feature_names=list(X.columns)),
        "importancias": dict(zip(X.columns, map(float, arv.feature_importances_))),
        "modelo": arv,
    }
