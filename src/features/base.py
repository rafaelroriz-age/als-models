"""Tabela-base entidade × mês (T14): ponte de clientes S360 × Protheus × Zoho, limpeza das amostras e grade mensal.

Entidade = raiz do CNPJ (8 dígitos, como o "Raiz CNPJ" do Customer Status), obtida pelo Zoho `accounts`:
- S360 `cliente.id_cigam`/`codigo_legado` = Zoho `erp_id` (código legado CIGAM ou código Protheus);
- Protheus `cod_cliente` = Zoho `erp_id` quando ele já é código Protheus (`A99999`) ou o sufixo do nome
  da conta (`"RUMO - MALHA NORTE - SAO PAULO/SP - A19079"`, às vezes com a loja: `A5680901`).
- Protheus sem código no Zoho: razão social (`contasreceber.nome_cliente`) = Zoho `razao_social`, aceita só
  quando todas as contas Zoho com o mesmo nome apontam para a mesma entidade.
Sem ponte: `protheus:<cod>` (S360 cujo código é Protheus cai na mesma entidade) ou `s360:<cliente_id>`.
"""
from __future__ import annotations

from dataclasses import dataclass

import re
import unicodedata

import numpy as np
import pandas as pd

from src.features.regras import inicio_mes

RX_PROTHEUS = r"^[A-Z]\d{5}$"
RX_SUFIXO_CONTA = r"-\s*\(?([A-Z]\d{5})(?:\d{2})?\)?\s*$"
_RX_SOCIETARIO = re.compile(r"\b(S A|SA|LTDA|ME|EPP|EIRELI)\b")


@dataclass(frozen=True)
class ParametrosBase:
    data_min: str = "2010-01-01"              # datas antes disso são erro de digitação (perfil: anos 1, 19, 201...)
    # CFOP fora do faturamento: remessa de ativo (x554), material de uso e consumo (x557) e simples faturamento
    # de entrega futura (x922), cujo valor reaparece na remessa x116/x117 (evita dupla contagem).
    cfop_excluidos: tuple[str, ...] = ("554", "557", "922")
    cfop_servico: tuple[str, ...] = ("933",)  # prestação de serviço (análise)
    estagio_ganho: str = "Closed Won"
    estagio_perdido: str = "Closed Lost"


# ---------------------------------------------------------------- chaves


def raiz_cnpj(cnpj: pd.Series) -> pd.Series:
    """8 primeiros dígitos do CNPJ (zeros à esquerda restaurados); CPF (11 dígitos) e lixo → NA."""
    d = cnpj.astype("string").str.replace(r"\D", "", regex=True)
    ok = d.str.len().between(12, 14) & d.str.strip("0").str.len().gt(0)
    return d.str.zfill(14).str[:8].where(ok.fillna(False))


def normalizar_nome(nome: pd.Series) -> pd.Series:
    """Razão social comparável: sem acento e pontuação, maiúscula, sem sufixo societário (SA, LTDA, ME, EPP, EIRELI)."""
    def _n(s):
        if s is None or pd.isna(s):
            return pd.NA
        s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
        s = _RX_SOCIETARIO.sub(" ", re.sub(r"[^A-Z0-9 ]", " ", s))
        s = re.sub(r"\s+", " ", s).strip()
        return s or pd.NA
    return nome.map(_n).astype("string")


def codigo_protheus_zoho(erp_id: pd.Series, conta: pd.Series) -> pd.Series:
    """Código Protheus de uma conta Zoho: o `erp_id` se já tiver o formato `A99999`, senão o sufixo do nome."""
    erp = erp_id.astype("string").str.strip().str.upper()
    sufixo = conta.astype("string").str.strip().str.upper().str.extract(RX_SUFIXO_CONTA, expand=False)
    return erp.where(erp.str.match(RX_PROTHEUS).fillna(False), sufixo)


def _moda(s: pd.Series):
    s = s.dropna()
    return s.value_counts().sort_index().idxmax() if len(s) else pd.NA


def mapa_zoho(accounts: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por conta Zoho: zoho_id, raiz, erp_id, cod_protheus, nome, segmento, entidade (raiz ou `zoho:<id>`)."""
    z = accounts.copy()
    z["erp_id"] = z["erp_id"].astype("string").str.strip().str.upper().replace("", pd.NA)
    z["raiz"] = raiz_cnpj(z["cnpj"])
    z["cod_protheus"] = codigo_protheus_zoho(z["erp_id"], z["conta"])
    z["nome"] = normalizar_nome(z["razao_social"]) if "razao_social" in z else pd.Series(pd.NA, index=z.index, dtype="string")
    z["segmento"] = z["segmento"].astype("string").str.strip().replace({"N/A": pd.NA, "": pd.NA})
    z["entidade"] = z["raiz"].fillna("zoho:" + z["zoho_id"].astype("string"))
    return z[["zoho_id", "raiz", "erp_id", "cod_protheus", "nome", "segmento", "entidade"]]


def _indice(z: pd.DataFrame, col: str) -> pd.Series:
    """código → entidade; código que aponta para várias entidades fica com a mais frequente (desempate por ordem)."""
    return z.dropna(subset=[col]).groupby(col)["entidade"].agg(_moda)


def mapear_s360(clientes: pd.DataFrame, z: pd.DataFrame) -> pd.DataFrame:
    """cliente_id → entidade e a regra usada (`zoho_erp`, `zoho_protheus`, `protheus_direto`, `sem_ponte`)."""
    por_erp, por_cod = _indice(z, "erp_id"), _indice(z, "cod_protheus")
    c = clientes[["cliente_id"]].copy()
    c["entidade"], c["regra"] = pd.Series(pd.NA, index=c.index, dtype="string"), pd.Series(pd.NA, index=c.index, dtype="string")
    chaves = [clientes[k].astype("string").str.strip().str.upper() for k in ("id_cigam", "codigo_legado")]
    for regra, indice in (("zoho_erp", por_erp), ("zoho_protheus", por_cod)):
        for k in chaves:
            achou = c["entidade"].isna() & k.map(indice).notna()
            c.loc[achou, "entidade"], c.loc[achou, "regra"] = k[achou].map(indice), regra
    for k in chaves:
        achou = c["entidade"].isna() & k.str.match(RX_PROTHEUS).fillna(False)
        c.loc[achou, "entidade"], c.loc[achou, "regra"] = "protheus:" + k[achou], "protheus_direto"
    falta = c["entidade"].isna()
    c.loc[falta, "entidade"] = "s360:" + c.loc[falta, "cliente_id"].astype("string")
    c.loc[falta, "regra"] = "sem_ponte"
    return c


def mapear_protheus(codigos: pd.Series, z: pd.DataFrame, clientes: pd.DataFrame,
                    mapa_s360: pd.DataFrame, nomes: pd.Series | None = None) -> pd.DataFrame:
    """cod_cliente → entidade: Zoho (`zoho`), cliente S360 com o mesmo código (`s360`), razão social igual à de
    contas Zoho de uma só entidade (`nome_zoho`; `nomes` = nome do cliente indexado por cod_cliente) ou `protheus:<cod>`."""
    cod = pd.Series(codigos.dropna().astype("string").str.strip().str.upper().unique(), name="cod_cliente")
    out = pd.DataFrame({"cod_cliente": cod, "entidade": cod.map(_indice(z, "cod_protheus")).astype("string")})
    out["regra"] = np.where(out["entidade"].notna(), "zoho", None)
    s360 = clientes.assign(k=clientes["id_cigam"].astype("string").str.strip().str.upper()).merge(mapa_s360, on="cliente_id")
    s360 = s360[~s360["regra"].isin(["sem_ponte", "protheus_direto"])].groupby("k")["entidade"].agg(_moda)
    achou = out["entidade"].isna() & out["cod_cliente"].map(s360).notna()
    out.loc[achou, "entidade"], out.loc[achou, "regra"] = out.loc[achou, "cod_cliente"].map(s360), "s360"
    if nomes is not None:
        n = normalizar_nome(pd.Series(nomes.to_numpy(), index=nomes.index.astype("string").str.strip().str.upper()))
        n = n[~n.index.duplicated()]
        porz = z.dropna(subset=["nome"]).groupby("nome")["entidade"].agg(["nunique", "first"])
        unico = porz.loc[porz["nunique"] == 1, "first"]
        alvo = out["cod_cliente"].map(n).map(unico)
        achou = out["entidade"].isna() & alvo.notna()
        out.loc[achou, "entidade"], out.loc[achou, "regra"] = alvo[achou], "nome_zoho"
    falta = out["entidade"].isna()
    out.loc[falta, "entidade"], out.loc[falta, "regra"] = "protheus:" + out.loc[falta, "cod_cliente"], "sem_ponte"
    return out


# ---------------------------------------------------------------- amostras


def limpar_amostras(agg: pd.DataFrame, ate: pd.Timestamp, clientes_validos: set) -> tuple[pd.DataFrame, dict]:
    """Agregado do S360 (cliente_id, ano, mes, status_data, avulsa, n, n_ids) → amostras por cliente × mês.

    Descarta (e conta): ids duplicados, sem data, data fora do intervalo, cliente inexistente e mês > `ate`
    (mês corrente incompleto). Avulsas (D9: sem compartimento/equipamento válido) saem do alvo `amostras`
    e ficam só como contagem em `avulsas`.
    """
    a = agg.copy()
    a["n"], a["n_ids"] = a["n"].astype(int), a["n_ids"].astype(int)
    descarte = {"duplicadas": int((a["n"] - a["n_ids"]).sum())}
    a["n"] = a["n_ids"]
    for motivo in ("sem_data", "fora_intervalo"):
        m = a["status_data"].eq(motivo)
        descarte[motivo] = int(a.loc[m, "n"].sum())
        a = a[~m]
    m = a["cliente_id"].isna() | ~a["cliente_id"].isin(clientes_validos)
    descarte["sem_cliente"] = int(a.loc[m, "n"].sum())
    a = a[~m].assign(cliente_id=lambda x: x["cliente_id"].astype("int64"))
    a["periodo"] = pd.to_datetime(dict(year=a["ano"].astype(int), month=a["mes"].astype(int), day=1))
    m = a["periodo"] > inicio_mes(pd.Timestamp(ate))
    descarte["mes_incompleto"] = int(a.loc[m, "n"].sum())
    a = a[~m]
    a["avulsa"] = a["avulsa"].astype(int).astype(bool)
    descarte["avulsas"] = int(a.loc[a["avulsa"], "n"].sum())
    descarte["por_data_entrada"] = int(a.loc[a["status_data"].eq("entrada"), "n"].sum())
    out = (a.assign(amostras=a["n"].where(~a["avulsa"], 0), avulsas=a["n"].where(a["avulsa"], 0))
           .groupby(["cliente_id", "periodo"], as_index=False)[["amostras", "avulsas"]].sum())
    descarte["mantidas"] = int(out["amostras"].sum())
    return out, descarte


# ---------------------------------------------------------------- faturamento e oportunidades


def faturamento_mensal(nf: pd.DataFrame, p: ParametrosBase = ParametrosBase()) -> tuple[pd.DataFrame, dict]:
    """Agregado do Protheus (cod_cliente, cfop, ano, mes, total) → faturamento e faturamento_servico por código × mês."""
    f = nf.copy()
    f["total"] = pd.to_numeric(f["total"], errors="coerce").fillna(0.0).astype(float)
    sufixo = f["cfop"].astype("string").str.strip().str[-3:]
    excl = sufixo.isin(p.cfop_excluidos)
    info = {"cfop_excluido_total": round(float(f.loc[excl, "total"].sum()), 2),
            "faturamento_total": round(float(f.loc[~excl, "total"].sum()), 2)}
    f = f[~excl].assign(servico=sufixo[~excl].isin(p.cfop_servico))
    f["cod_cliente"] = f["cod_cliente"].astype("string").str.strip().str.upper()
    f["periodo"] = pd.to_datetime(dict(year=f["ano"].astype(int), month=f["mes"].astype(int), day=1))
    out = (f.assign(faturamento_servico=f["total"].where(f["servico"], 0.0))
           .groupby(["cod_cliente", "periodo"], as_index=False)
           .agg(faturamento=("total", "sum"), faturamento_servico=("faturamento_servico", "sum")))
    return out, info


def oportunidades_mensal(deals: pd.DataFrame, p: ParametrosBase = ParametrosBase()) -> pd.DataFrame:
    """Agregado de deals (conta_id, estagio, ano, mes, n, valor, valor_ponderado) → colunas por conta × mês.

    O mês é o fechamento real (ganhas/perdidas) ou o previsto (abertas), conforme a consulta do notebook.
    """
    d = deals.copy()
    d["periodo"] = pd.to_datetime(dict(year=d["ano"].astype(int), month=d["mes"].astype(int), day=1))
    for c in ("n", "valor", "valor_ponderado"):
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0.0).astype(float)
    tipo = np.select([d["estagio"].eq(p.estagio_ganho), d["estagio"].eq(p.estagio_perdido)],
                     ["ganhas", "perdidas"], default="abertas")
    d["tipo"] = tipo
    cols = {"abertas": ["n", "valor", "valor_ponderado"], "ganhas": ["n", "valor"], "perdidas": ["n"]}
    partes = []
    for t, cs in cols.items():
        g = d[d["tipo"].eq(t)].groupby(["conta_id", "periodo"])[cs].sum()
        partes.append(g.rename(columns=lambda c: f"oport_{t}_{c}"))
    return pd.concat(partes, axis=1).fillna(0.0).reset_index()


# ---------------------------------------------------------------- grade mensal


def grade_mensal(inicio: pd.Series, ate: pd.Timestamp) -> pd.DataFrame:
    """entidade × mês do 1º mês (`inicio`, indexado por entidade) até `ate`, vetorizado."""
    fim = inicio_mes(pd.Timestamp(ate))
    ini = inicio_mes(pd.Series(pd.to_datetime(inicio.to_numpy()), index=inicio.index))
    ini = ini[ini <= fim]
    meses = ((fim.year - ini.dt.year) * 12 + (fim.month - ini.dt.month) + 1).astype(int)
    ent = np.repeat(ini.index.to_numpy(), meses.to_numpy())
    passo = np.arange(meses.sum()) - np.repeat(np.cumsum(meses.to_numpy()) - meses.to_numpy(), meses.to_numpy())
    base = np.repeat(ini.dt.to_period("M").to_numpy(), meses.to_numpy())
    periodo = pd.PeriodIndex(base, freq="M") + passo
    return pd.DataFrame({"entidade": ent, "periodo": periodo.to_timestamp()})


def montar_base(amostras: pd.DataFrame, faturamento: pd.DataFrame, oportunidades: pd.DataFrame,
                ate: pd.Timestamp, atributos: pd.DataFrame | None = None) -> pd.DataFrame:
    """Tabela-base entidade × mês. Entradas já com `entidade` e `periodo`.

    A grade vai do 1º mês com qualquer atividade até `ate`. Colunas de cada fonte são 0 nos meses sem
    registro **dentro da cobertura da fonte** e NaN antes do 1º mês da fonte (ex.: Protheus só desde 2024-10),
    para não confundir "sem dado" com "zero".
    """
    fontes = {"amostras": amostras, "faturamento": faturamento, "oportunidades": oportunidades}
    agreg = {k: v.groupby(["entidade", "periodo"], as_index=False).sum(numeric_only=True) for k, v in fontes.items()}
    inicio = pd.concat([v[["entidade", "periodo"]] for v in agreg.values()]).groupby("entidade")["periodo"].min()
    base = grade_mensal(inicio, ate)
    for nome, v in agreg.items():
        cols = [c for c in v.columns if c not in ("entidade", "periodo")]
        base = base.merge(v, on=["entidade", "periodo"], how="left")
        dentro = base["periodo"] >= v["periodo"].min() if len(v) else pd.Series(False, index=base.index)
        base[cols] = base[cols].fillna(0.0).where(dentro)
        base[f"tem_{nome}"] = base["entidade"].isin(set(v["entidade"]))
    if atributos is not None:
        base = base.merge(atributos, on="entidade", how="left")
    return base.sort_values(["entidade", "periodo"], ignore_index=True)


# ---------------------------------------------------------------- cobertura


def cobertura_ponderada(mapa: pd.DataFrame, pesos: pd.DataFrame, chave: str, peso: str) -> dict:
    """% de chaves e % do `peso` (amostras, faturamento) cuja entidade veio de uma ponte (regra ≠ `sem_ponte`)."""
    m = pesos.groupby(chave, as_index=False)[peso].sum().merge(mapa[[chave, "regra"]], on=chave, how="left")
    m["regra"] = m["regra"].fillna("sem_ponte")
    ok = m["regra"].ne("sem_ponte")
    total = float(m[peso].sum())
    return {
        "chaves": int(len(m)), "chaves_com_ponte": int(ok.sum()),
        "pct_chaves": round(100 * ok.mean(), 2) if len(m) else 0.0,
        "pct_peso": round(100 * float(m.loc[ok, peso].sum()) / total, 2) if total else 0.0,
        "por_regra_pct_peso": (m.groupby("regra")[peso].sum() / total * 100).round(2).to_dict() if total else {},
    }
