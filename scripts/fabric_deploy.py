"""Empacota src/ como wheel, converte os notebooks .py em .ipynb do Fabric e (com --aplicar) publica no workspace.

Sem --aplicar só gera dist/ (nada sai da máquina). Com --aplicar:
  1. sobe o wheel (e, com --planilhas, as .xlsx) para Files/als_oilmodel/ do lakehouse padrão via OneLake;
  2. cria ou atualiza os notebooks `als_*` no workspace, com o lakehouse padrão anexado.
Notebooks: os 3 legados de NOTEBOOKS (nome fixo) + todo `notebooks/**/als_*.py`, publicado com o nome do arquivo
(convenção da T30). Linhas `# %%` separam células; `# %% [parameters]` vira a célula de parâmetros do Fabric.
Workspace e lakehouse: argumento ou ALS_WORKSPACE / ALS_LAKEHOUSE (padrão LakehouseOel).
Uso: python scripts/fabric_deploy.py [--aplicar --workspace "<nome>"] [--lakehouse LakehouseOel] [--planilhas]
     [--notebooks als_50_pre_consultas ...]
"""
from __future__ import annotations

import argparse
import ast
import base64
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fabric_guard import violacoes  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
DIST = RAIZ / "dist"
NOTEBOOKS = {  # legados, nome fixo; notebooks novos entram por convenção (descobrir_notebooks)
    "als_00_perfil_qualidade": RAIZ / "notebooks/00_validacao/01_perfil_qualidade.py",
    "als_01_engenharia_reversa_planilhas": RAIZ / "notebooks/00_validacao/02_engenharia_reversa_planilhas.py",
    "als_40_backtest_baselines": RAIZ / "notebooks/40_backtest/01_backtest_baselines.py",
}
PLANILHAS = [
    "Calculadora de amostras v8 - horimetros preventiva - out.2022.xlsx",
    "Forecast 27.xlsx",
    "Customer Status Novo_Geral_Novas Carteiras 2026.xlsx",
]
PASTA_FILES = "als_oilmodel"
LAKEHOUSE = "LakehouseOel"
API = "https://api.fabric.microsoft.com/v1"
ONELAKE = "https://onelake.dfs.fabric.microsoft.com"
_CELULA = re.compile(r"^# %%(?:[ \t]*\[(?P<tag>[\w-]+)\])?[ \t]*$", re.M)


def construir_wheel() -> Path:
    DIST.mkdir(exist_ok=True)
    for w in DIST.glob("als_oilmodel-*.whl"):
        w.unlink()
    subprocess.run([sys.executable, "-m", "pip", "wheel", str(RAIZ), "--no-deps", "-w", str(DIST), "-q"], check=True)
    return next(DIST.glob("als_oilmodel-*.whl"))


def descobrir_notebooks(raiz: Path = RAIZ, legados: dict[str, Path] | None = None) -> dict[str, Path]:
    """Legados (NOTEBOOKS) + `notebooks/**/als_*.py` com o nome do arquivo. Nome repetido é erro."""
    achados = dict(NOTEBOOKS if legados is None else legados)
    for py in sorted((raiz / "notebooks").rglob("als_*.py")):
        if py.stem in achados and achados[py.stem].resolve() != py.resolve():
            raise SystemExit(f"notebook `{py.stem}` duplicado: {achados[py.stem]} e {py}")
        achados[py.stem] = py
    return achados


def selecionar(notebooks: dict[str, Path], nomes: list[str] | None) -> dict[str, Path]:
    if not nomes:
        return notebooks
    falta = [n for n in nomes if n not in notebooks]
    if falta:
        raise SystemExit(f"notebook não registrado: {', '.join(falta)} (registrados: {', '.join(notebooks)})")
    return {n: notebooks[n] for n in nomes}


def _celula(tipo: str, fonte: str, tags: list[str] | None = None) -> dict:
    c = {"cell_type": tipo, "metadata": {"tags": tags} if tags else {}, "source": fonte.splitlines(keepends=True)}
    if tipo == "code":
        c.update(outputs=[], execution_count=None)
    return c


def celulas_codigo(fonte: str) -> list[dict]:
    """Sem `# %%`, uma célula só (comportamento original). Com marcadores, uma célula por trecho."""
    marcas = list(_CELULA.finditer(fonte))
    if not marcas:
        return [_celula("code", fonte)]
    trechos = [(None, fonte[:marcas[0].start()])]
    trechos += [(m.group("tag"), fonte[m.end():(marcas[i + 1].start() if i + 1 < len(marcas) else len(fonte))])
                for i, m in enumerate(marcas)]
    return [_celula("code", t.strip("\n") + "\n", [tag] if tag else None) for tag, t in trechos if t.strip()]


def para_ipynb(py: Path, wheel: str, lakehouse: dict | None) -> dict:
    fonte = py.read_text(encoding="utf-8")
    doc = ast.get_docstring(ast.parse(fonte)) or py.stem
    instalar = (f"%pip install /lakehouse/default/Files/{PASTA_FILES}/wheels/{wheel} -q\n"
                f"import os\nos.environ.setdefault('ALS_PASTA_PLANILHAS', '/lakehouse/default/Files/{PASTA_FILES}/planilhas')")
    meta = {"language_info": {"name": "python"}, "kernel_info": {"name": "synapse_pyspark"},
            "kernelspec": {"name": "synapse_pyspark", "display_name": "Synapse PySpark"}}
    if lakehouse:
        meta["dependencies"] = {"lakehouse": {
            "default_lakehouse": lakehouse["id"], "default_lakehouse_name": lakehouse["displayName"],
            "default_lakehouse_workspace_id": lakehouse["workspaceId"]}}
    return {"nbformat": 4, "nbformat_minor": 5, "metadata": meta,
            "cells": [_celula("markdown", f"# {py.stem}\n\n{doc}"), _celula("code", instalar), *celulas_codigo(fonte)]}


def gerar(notebooks: dict[str, Path], wheel: str, lakehouse: dict | None, saida: Path) -> dict[str, str]:
    """Converte cada notebook para .ipynb em `saida` (recusa nome sem `als_` e o que a barreira bloquear)."""
    saida.mkdir(parents=True, exist_ok=True)
    defs = {}
    for nome, py in notebooks.items():
        if not nome.startswith("als_"):
            sys.exit(f"{nome}: só notebooks `als_*` deste projeto podem ser publicados")
        achados = violacoes(py.read_text(encoding="utf-8"))
        if achados:
            sys.exit(f"{py.name} bloqueado pela barreira do Fabric ({', '.join(achados)}); ver scripts/fabric_guard.py")
        nb = para_ipynb(py, wheel, lakehouse)
        (saida / f"{nome}.ipynb").write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
        defs[nome] = base64.b64encode(json.dumps(nb, ensure_ascii=False).encode("utf-8")).decode()
    return defs


class Cliente:
    def __init__(self):
        sys.path.insert(0, str(RAIZ))
        from src.pipeline.fabric import _credencial
        import requests

        self.cred, self.http = _credencial(), requests.Session()

    def _h(self, escopo: str) -> dict:
        return {"Authorization": f"Bearer {self.cred.get_token(escopo).token}"}

    def api(self, metodo: str, caminho: str, **kw):
        r = self.http.request(metodo, f"{API}{caminho}", headers=self._h("https://api.fabric.microsoft.com/.default"), **kw)
        if r.status_code == 202 and "Location" in r.headers:  # operação longa
            while True:
                time.sleep(int(r.headers.get("Retry-After", 3)))
                r = self.http.get(r.headers["Location"], headers=self._h("https://api.fabric.microsoft.com/.default"))
                if r.status_code != 202 and r.json().get("status") not in ("Running", "NotStarted"):
                    break
        r.raise_for_status()
        return r.json() if r.content else {}

    def subir_arquivo(self, ws_id: str, lh_id: str, destino: str, dados: bytes) -> None:
        url = f"{ONELAKE}/{ws_id}/{lh_id}/Files/{destino}"
        h = {**self._h("https://storage.azure.com/.default"), "x-ms-version": "2023-11-03"}
        self.http.put(url, params={"resource": "file", "overwrite": "true"}, headers=h).raise_for_status()
        self.http.patch(url, params={"action": "append", "position": 0}, headers=h, data=dados).raise_for_status()
        self.http.patch(url, params={"action": "flush", "position": len(dados)}, headers=h).raise_for_status()


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--workspace", default=os.environ.get("ALS_WORKSPACE"))
    ap.add_argument("--lakehouse", default=os.environ.get("ALS_LAKEHOUSE", LAKEHOUSE))
    ap.add_argument("--planilhas", action="store_true")
    ap.add_argument("--notebooks", nargs="+", help="só estes `als_*` (padrão: todos os registrados)")
    a = ap.parse_args(argv)

    notebooks = selecionar(descobrir_notebooks(), a.notebooks)
    wheel = construir_wheel()
    print(f"wheel: {wheel.name}")
    cli = lakehouse = ws_id = None
    if a.aplicar:
        if not a.workspace:
            sys.exit("--workspace (ou ALS_WORKSPACE) é obrigatório com --aplicar")
        cli = Cliente()
        ws = [w for w in cli.api("GET", "/workspaces")["value"] if w["displayName"] == a.workspace]
        if not ws:
            sys.exit(f"workspace não encontrado: {a.workspace}")
        ws_id = ws[0]["id"]
        lhs = [l for l in cli.api("GET", f"/workspaces/{ws_id}/lakehouses")["value"]
               if l["displayName"].lower() == a.lakehouse.lower()]
        if not lhs:
            sys.exit(f"lakehouse não encontrado: {a.lakehouse}")
        lakehouse = {**lhs[0], "workspaceId": ws_id}

    saida = DIST / "fabric"
    defs = gerar(notebooks, wheel.name, lakehouse, saida)
    print(f"notebooks gerados em {saida}: {', '.join(defs)}")
    if not a.aplicar:
        print("modo simulação: nada foi publicado. Use --aplicar --workspace \"<nome>\" para publicar.")
        return

    cli.subir_arquivo(ws_id, lakehouse["id"], f"{PASTA_FILES}/wheels/{wheel.name}", wheel.read_bytes())
    print(f"wheel enviado para Files/{PASTA_FILES}/wheels/")
    if a.planilhas:
        for nome in PLANILHAS:
            cli.subir_arquivo(ws_id, lakehouse["id"], f"{PASTA_FILES}/planilhas/{nome}", (RAIZ / nome).read_bytes())
        print(f"planilhas enviadas para Files/{PASTA_FILES}/planilhas/")
    existentes = {n["displayName"]: n["id"] for n in cli.api("GET", f"/workspaces/{ws_id}/notebooks")["value"]}
    for nome, b64 in defs.items():
        definicao = {"format": "ipynb", "parts": [
            {"path": "notebook-content.ipynb", "payload": b64, "payloadType": "InlineBase64"}]}
        if nome in existentes:
            cli.api("POST", f"/workspaces/{ws_id}/notebooks/{existentes[nome]}/updateDefinition",
                    json={"definition": definicao})
            print(f"atualizado: {nome}")
        else:
            cli.api("POST", f"/workspaces/{ws_id}/notebooks", json={"displayName": nome, "definition": definicao})
            print(f"criado: {nome}")


if __name__ == "__main__":
    main()
