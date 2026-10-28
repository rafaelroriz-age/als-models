"""Executa no Fabric, pela API (porta 443), um notebook `als_*` já publicado e baixa as saídas para data/.

Passos: localiza workspace, lakehouse e notebook; lê a definição publicada e recusa o que a barreira
(scripts/fabric_guard.py) bloquear; dispara o job RunNotebook e acompanha pelo header Location até concluir;
baixa de Files/als_oilmodel/<pasta>/ no OneLake para data/<pasta>/ (só leitura no Fabric).
Autenticação: login interativo em cache (padrão) ou ALS_AUTH=device (device code, login pelo navegador do celular).
Notebooks: qualquer `als_*` registrado em fabric_deploy.descobrir_notebooks. Pasta de saída: SAIDAS (legados) ou a
constante `PASTA_FABRIC` do .py (padrão `saida`). `--param chave=valor` vai para a célula de parâmetros do notebook.
Workspace/lakehouse: argumento ou ALS_WORKSPACE / ALS_LAKEHOUSE (o lakehouse é o do Files de onde se baixa).
Uso: python scripts/fabric_run.py als_00_perfil_qualidade [--workspace "<nome>"] [--pasta perfil] [--publicar]
     python scripts/fabric_run.py als_50_pre_consultas [--param lakehouse=LakehouseOel --param horizonte=6]
"""
from __future__ import annotations

import argparse
import ast
import base64
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fabric_deploy import API, LAKEHOUSE, ONELAKE, PASTA_FILES, RAIZ, Cliente, descobrir_notebooks  # noqa: E402
from fabric_guard import violacoes  # noqa: E402

WORKSPACE = os.environ.get("ALS_WORKSPACE", "O&L Global - Prod - DA")
SAIDAS = {  # legados: notebook -> subpasta de Files/als_oilmodel/ que ele grava
    "als_00_perfil_qualidade": "perfil",
    "als_01_engenharia_reversa_planilhas": "planilhas",
}
PASTA_PADRAO = "saida"  # notebooks descobertos por convenção sem PASTA_FABRIC
FINAIS = {"Completed", "Failed", "Cancelled", "Deduped"}
ESCOPO_API = "https://api.fabric.microsoft.com/.default"
ESCOPO_STORAGE = "https://storage.azure.com/.default"


class Recusado(Exception):
    """Notebook fora da regra: nome sem `als_` ou conteúdo bloqueado pela barreira."""


def credencial():
    sys.path.insert(0, str(RAIZ))
    if os.environ.get("ALS_AUTH", "").lower() != "device":
        from src.pipeline.fabric import _credencial
        return _credencial()
    from azure.identity import AuthenticationRecord, DeviceCodeCredential, TokenCachePersistenceOptions
    from src.pipeline.fabric import _AUTH_RECORD

    def avisar(uri, codigo, _expira):
        print(f"Abra {uri} (no celular serve) e digite o código {codigo}", flush=True)

    kw = {"cache_persistence_options": TokenCachePersistenceOptions(name="als_oilmodel"), "prompt_callback": avisar}
    if _AUTH_RECORD.exists():
        kw["authentication_record"] = AuthenticationRecord.deserialize(_AUTH_RECORD.read_text(encoding="utf-8"))
    return DeviceCodeCredential(**kw)


def validar_nome(nome: str) -> None:
    if not nome.startswith("als_"):
        raise Recusado(f"{nome}: só notebooks `als_*` deste projeto podem ser executados")


def pasta_saida(nome: str, notebooks: dict[str, Path] | None = None) -> str | None:
    """Subpasta de Files/als_oilmodel/ que o notebook grava: SAIDAS, senão `PASTA_FABRIC = "..."` no .py
    (padrão `saida`) para os descobertos por convenção; None para legado sem saída."""
    if nome in SAIDAS:
        return SAIDAS[nome]
    py = (descobrir_notebooks() if notebooks is None else notebooks).get(nome)
    if py is None or not py.name.startswith("als_"):
        return None
    for no in ast.walk(ast.parse(py.read_text(encoding="utf-8"))):
        if (isinstance(no, ast.Assign) and any(getattr(t, "id", None) == "PASTA_FABRIC" for t in no.targets)
                and isinstance(no.value, ast.Constant) and isinstance(no.value.value, str)):
            return no.value.value
    return PASTA_PADRAO


def ler_parametros(pares: list[str] | None) -> dict[str, str]:
    out = {}
    for par in pares or []:
        chave, sep, valor = par.partition("=")
        if not sep or not chave.strip().isidentifier():
            raise SystemExit(f"--param inválido: {par!r} (use chave=valor)")
        out[chave.strip()] = valor
    return out


class Executor(Cliente):
    def __init__(self, cred=None, http=None, dormir=time.sleep):
        import requests

        self.cred, self.http, self.dormir = cred or credencial(), http or requests.Session(), dormir

    def _get(self, url: str, escopo: str = ESCOPO_API, **kw):
        r = self.http.get(url, headers={**self._h(escopo), "x-ms-version": "2023-11-03"}, **kw)
        r.raise_for_status()
        return r

    def localizar(self, workspace: str, lakehouse: str, notebook: str) -> dict:
        ws = [w for w in self.api("GET", "/workspaces")["value"] if w["displayName"] == workspace]
        if not ws:
            raise SystemExit(f"workspace não encontrado: {workspace}")
        ws_id = ws[0]["id"]
        lhs = [l for l in self.api("GET", f"/workspaces/{ws_id}/lakehouses")["value"]
               if l["displayName"].lower() == lakehouse.lower()]
        nbs = [n for n in self.api("GET", f"/workspaces/{ws_id}/notebooks")["value"] if n["displayName"] == notebook]
        if not lhs:
            raise SystemExit(f"lakehouse não encontrado: {lakehouse}")
        if not nbs:
            raise SystemExit(f"notebook não publicado: {notebook} (publique com scripts/fabric_deploy.py --aplicar)")
        return {"ws": ws_id, "lh": lhs[0]["id"], "nb": nbs[0]["id"]}

    def definicao(self, ws_id: str, nb_id: str) -> str:
        """Texto do notebook publicado (operação longa: 202 + Location até Succeeded, depois /result)."""
        r = self.http.post(f"{API}/workspaces/{ws_id}/notebooks/{nb_id}/getDefinition",
                           params={"format": "ipynb"}, headers=self._h(ESCOPO_API))
        r.raise_for_status()
        if r.status_code == 202:
            op = r.headers["Location"]
            while True:
                self.dormir(int(r.headers.get("Retry-After", 2)))
                r = self._get(op)
                estado = r.json().get("status")
                if estado == "Succeeded":
                    r = self._get(r.headers.get("Location", f"{op}/result"))
                    break
                if estado not in ("NotStarted", "Running"):
                    raise RuntimeError(f"getDefinition terminou em {estado}: {r.json()}")
        partes = r.json()["definition"]["parts"]
        return "\n".join(base64.b64decode(p["payload"]).decode("utf-8") for p in partes
                         if p.get("payloadType", "InlineBase64") == "InlineBase64")

    def checar(self, nome: str, ws_id: str, nb_id: str) -> None:
        validar_nome(nome)
        achados = violacoes(self.definicao(ws_id, nb_id))
        if achados:
            raise Recusado(f"{nome} bloqueado pela barreira do Fabric ({', '.join(achados)}); ver scripts/fabric_guard.py")

    def executar(self, ws_id: str, nb_id: str, timeout: int = 3600, parametros: dict[str, str] | None = None) -> dict:
        kw = {}
        if parametros:  # sobrepõe a célula de parâmetros do notebook
            kw["json"] = {"executionData": {"parameters": {
                k: {"value": v, "type": "string"} for k, v in parametros.items()}}}
        r = self.http.post(f"{API}/workspaces/{ws_id}/items/{nb_id}/jobs/instances",
                           params={"jobType": "RunNotebook"}, headers=self._h(ESCOPO_API), **kw)
        r.raise_for_status()
        local, espera = r.headers["Location"], int(r.headers.get("Retry-After", 30))
        inicio, ultimo = time.monotonic(), None
        while True:
            job = self._get(local).json()
            decorrido = time.monotonic() - inicio
            if job.get("status") != ultimo:
                ultimo = job.get("status")
                print(f"[{decorrido:6.0f}s] {ultimo}", flush=True)
            if ultimo in FINAIS:
                return {**job, "segundos": round(decorrido, 1), "location": local}
            if decorrido > timeout:
                return {**job, "status": "Timeout", "segundos": round(decorrido, 1), "location": local}
            self.dormir(min(espera, 30))

    def baixar(self, ws_id: str, lh_id: str, pasta: str, destino: Path) -> list[Path]:
        """Lista Files/als_oilmodel/<pasta> no OneLake e baixa cada arquivo para destino/<pasta>/."""
        base = f"{PASTA_FILES}/{pasta}".rstrip("/")
        params = {"resource": "filesystem", "recursive": "true", "directory": f"{lh_id}/Files/{base}"}
        arquivos, raiz = [], destino.resolve()
        while True:
            r = self.http.get(f"{ONELAKE}/{ws_id}", params=params,
                              headers={**self._h(ESCOPO_STORAGE), "x-ms-version": "2023-11-03"})
            if r.status_code == 404:  # o notebook ainda não gravou nada nessa pasta
                print(f"Files/{base}/ não existe no OneLake; nada a baixar", flush=True)
                return arquivos
            r.raise_for_status()
            for p in r.json().get("paths", []):
                if str(p.get("isDirectory", "false")).lower() == "true":
                    continue
                rel = p["name"].split(f"Files/{PASTA_FILES}/", 1)[-1]
                alvo = (raiz / rel).resolve()
                if raiz not in alvo.parents:
                    raise RuntimeError(f"caminho fora de data/: {p['name']}")
                alvo.parent.mkdir(parents=True, exist_ok=True)
                alvo.write_bytes(self._get(f"{ONELAKE}/{ws_id}/{p['name']}", ESCOPO_STORAGE).content)
                arquivos.append(alvo)
            cont = r.headers.get("x-ms-continuation")
            if not cont:
                return arquivos
            params = {**params, "continuation": cont}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("notebook")
    ap.add_argument("--workspace", default=WORKSPACE)
    ap.add_argument("--lakehouse", default=os.environ.get("ALS_LAKEHOUSE", LAKEHOUSE))
    ap.add_argument("--pasta", help="subpasta de Files/als_oilmodel/ a baixar (padrão: a do notebook)")
    ap.add_argument("--destino", default=str(RAIZ / "data"))
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--sem-download", action="store_true")
    ap.add_argument("--publicar", action="store_true", help="roda fabric_deploy.py --aplicar antes de executar")
    ap.add_argument("--param", action="append", metavar="CHAVE=VALOR", help="parâmetro do notebook (repetível)")
    a = ap.parse_args(argv)

    try:
        validar_nome(a.notebook)
    except Recusado as e:
        sys.exit(str(e))
    parametros = ler_parametros(a.param)
    if a.publicar:
        subprocess.run([sys.executable, str(RAIZ / "scripts/fabric_deploy.py"), "--aplicar",
                        "--workspace", a.workspace, "--lakehouse", a.lakehouse], check=True)
    ex = Executor()
    ids = ex.localizar(a.workspace, a.lakehouse, a.notebook)
    try:
        ex.checar(a.notebook, ids["ws"], ids["nb"])
    except Recusado as e:
        sys.exit(str(e))
    job = ex.executar(ids["ws"], ids["nb"], a.timeout, parametros)
    print(json.dumps({k: job.get(k) for k in ("status", "segundos", "startTimeUtc", "endTimeUtc", "failureReason",
                                               "location")}, indent=2, ensure_ascii=False))
    pasta = a.pasta if a.pasta is not None else pasta_saida(a.notebook)
    if job["status"] == "Completed" and not a.sem_download and pasta is not None:
        arquivos = ex.baixar(ids["ws"], ids["lh"], pasta, Path(a.destino))
        print(f"{len(arquivos)} arquivo(s) baixado(s) para {Path(a.destino) / pasta}")
    sys.exit(0 if job["status"] == "Completed" else 1)


if __name__ == "__main__":
    main()
