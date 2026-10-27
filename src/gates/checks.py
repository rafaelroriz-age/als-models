"""Gates de qualidade G0 (fontes) e G1 (tabela-base), em pandas puro para rodar igual local e no Fabric."""
from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

DATA_MIN_PLAUSIVEL = pd.Timestamp("2010-01-01")

# Colunas que não podem ser majoritariamente nulas para o projeto andar.
CHAVES_OBRIGATORIAS = {
    "bronze_s360.amostra": {"id": 0.0, "cliente_id": 1.0, "data_coleta": 5.0},
    "bronze_s360.compartimento": {"id": 0.0, "equipamento_id": 1.0},
    "bronze_s360.equipamento": {"id": 0.0},
    "silver_protheus.notassaida": {"cod_cliente": 0.5, "emissao": 0.5, "total": 0.5},
    "silver_zoho.accounts": {"zoho_id": 0.0},
}


@dataclass
class Resultado:
    gate: str
    checagem: str
    alvo: str
    ok: bool
    detalhe: str


def avaliar_g0(perfis: list[dict], hoje: pd.Timestamp | None = None) -> list[dict]:
    hoje = hoje or pd.Timestamp.now()
    out: list[Resultado] = []
    por_tabela = {p["tabela"]: p for p in perfis}
    for tabela, limites in CHAVES_OBRIGATORIAS.items():
        p = por_tabela.get(tabela)
        if p is None:
            out.append(Resultado("G0", "tabela_acessivel", tabela, False, "sem perfil (erro de leitura)"))
            continue
        out.append(Resultado("G0", "nao_vazia", tabela, p["n_linhas"] > 0, f"{p['n_linhas']} linhas"))
        for col, max_pct in limites.items():
            pct = p["nulos_pct"].get(col)
            out.append(Resultado("G0", f"nulos<= {max_pct}%", f"{tabela}.{col}",
                                 pct is not None and pct <= max_pct, f"{pct}% nulos"))
    for p in perfis:
        for col, (mn, mx) in p["datas"].items():
            mn_t, mx_t = pd.to_datetime(mn, errors="coerce"), pd.to_datetime(mx, errors="coerce")
            ok = pd.notna(mn_t) and pd.notna(mx_t) and mn_t >= DATA_MIN_PLAUSIVEL and mx_t <= hoje + pd.Timedelta(days=1)
            out.append(Resultado("G0", "datas_plausiveis", f"{p['tabela']}.{col}", bool(ok), f"{mn} .. {mx}"))
    return [asdict(r) for r in out]


def avaliar_g1(base: pd.DataFrame, chave: list[str], valor: str) -> list[dict]:
    """Tabela-base entidade × mês: chave única, valores não negativos e meses sem buracos por entidade."""
    out = [
        Resultado("G1", "chave_unica", "+".join(chave), not base.duplicated(chave).any(),
                  f"{int(base.duplicated(chave).sum())} duplicadas"),
        Resultado("G1", "nao_negativo", valor, bool((base[valor].fillna(0) >= 0).all()),
                  f"{int((base[valor] < 0).sum())} negativos"),
        Resultado("G1", "sem_nulos", valor, bool(base[valor].notna().all()), f"{int(base[valor].isna().sum())} nulos"),
    ]
    entidade = [c for c in chave if c != "periodo"]
    if "periodo" in base and entidade:
        g = base.groupby(entidade)["periodo"].agg(["min", "max", "nunique"])
        esperado = ((g["max"].dt.year - g["min"].dt.year) * 12 + (g["max"].dt.month - g["min"].dt.month) + 1)
        buracos = int((esperado != g["nunique"]).sum())
        out.append(Resultado("G1", "meses_continuos", "+".join(entidade), buracos == 0, f"{buracos} entidades com buracos"))
    return [asdict(r) for r in out]


def avaliar_g1_limpo(df: pd.DataFrame, chaves_nao_nulas: list[str], unico: list[str],
                     datas: list[str], hoje: pd.Timestamp | None = None,
                     data_min: pd.Timestamp = DATA_MIN_PLAUSIVEL) -> list[dict]:
    """Tabela limpa (Bronze/Silver → limpo): nulos em chaves, duplicatas e datas fora do intervalo plausível."""
    hoje = hoje or pd.Timestamp.now()
    out: list[Resultado] = []
    for col in chaves_nao_nulas:
        if col not in df:
            out.append(Resultado("G1", "chave_sem_nulos", col, False, "coluna ausente"))
            continue
        n = int(df[col].isna().sum())
        out.append(Resultado("G1", "chave_sem_nulos", col, n == 0, f"{n} nulos"))
    if all(c in df for c in unico):
        n = int(df.duplicated(unico).sum())
        out.append(Resultado("G1", "sem_duplicatas", "+".join(unico), n == 0, f"{n} duplicadas"))
    else:
        out.append(Resultado("G1", "sem_duplicatas", "+".join(unico), False, "coluna ausente"))
    for col in datas:
        if col not in df:
            out.append(Resultado("G1", "datas_no_intervalo", col, False, "coluna ausente"))
            continue
        d = pd.to_datetime(df[col], errors="coerce").dropna()
        fora = int(((d < data_min) | (d > hoje + pd.Timedelta(days=1))).sum())
        out.append(Resultado("G1", "datas_no_intervalo", col, fora == 0, f"{fora} fora de {data_min.date()}..{hoje.date()}"))
    return [asdict(r) for r in out]


def cobertura_join(esquerda: pd.DataFrame, direita: pd.DataFrame, chave: str, minimo_pct: float = 90.0,
                   nome: str | None = None) -> list[dict]:
    """% de linhas (não nulas) de `esquerda[chave]` com par em `direita[chave]`; falha abaixo de `minimo_pct`."""
    alvo = nome or chave
    if chave not in esquerda or chave not in direita:
        return [asdict(Resultado("G1", "cobertura_join", alvo, False, "coluna ausente"))]
    k = esquerda[chave].dropna()
    pct = 0.0 if k.empty else round(100 * k.isin(set(direita[chave].dropna())).mean(), 2)
    return [asdict(Resultado("G1", "cobertura_join", alvo, pct >= minimo_pct, f"{pct}% (mín {minimo_pct}%)"))]


def resumo(resultados: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(resultados)
