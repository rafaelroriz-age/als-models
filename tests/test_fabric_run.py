import base64
import json
import sys
from types import SimpleNamespace

import pytest
import requests

from scripts.fabric_run import API, ONELAKE, Executor, Recusado, validar_nome

WS, LH, NB = "ws-1", "lh-1", "nb-1"
JOB = f"{API}/workspaces/{WS}/items/{NB}/jobs/instances/job-1"
# Montados por partes para o hook da barreira não barrar o próprio teste da barreira.
ESCRITAS = ["spark.sql('DROP " + "TABLE silver_x')", "df.write.saveAs" + "Table('silver_x')"]


def resp(status=200, corpo=None, headers=None, conteudo=None):
    r = requests.Response()
    r.status_code = status
    r.headers.update(headers or {})
    r._content = conteudo if conteudo is not None else (json.dumps(corpo).encode() if corpo is not None else b"")
    return r


class Http:
    """Sessão falsa: cada rota (método, prefixo de URL) devolve a próxima resposta da fila (a última se repete)."""

    def __init__(self, rotas):
        self.rotas, self.chamadas = rotas, []

    def request(self, metodo, url, **kw):
        self.chamadas.append((metodo, url, kw.get("params")))
        for (m, prefixo), fila in self.rotas.items():
            if m == metodo and url.startswith(prefixo) and fila:
                return fila.pop(0) if len(fila) > 1 else fila[0]
        raise AssertionError(f"chamada inesperada: {metodo} {url}")

    def get(self, url, **kw):
        return self.request("GET", url, **kw)

    def post(self, url, **kw):
        return self.request("POST", url, **kw)


def executor(rotas):
    cred = SimpleNamespace(get_token=lambda escopo: SimpleNamespace(token="t"))
    return Executor(cred=cred, http=Http(rotas), dormir=lambda s: None)


def definicao(texto):
    payload = base64.b64encode(json.dumps({"cells": [{"source": [texto]}]}).encode()).decode()
    return {"definition": {"parts": [{"path": "notebook-content.ipynb", "payload": payload,
                                      "payloadType": "InlineBase64"}]}}


@pytest.mark.parametrize("nome", ["perfil", "Als_00", "x_als_00", ""])
def test_recusa_nome_sem_prefixo(nome):
    with pytest.raises(Recusado):
        validar_nome(nome)


def test_localiza_ids():
    ex = executor({
        ("GET", f"{API}/workspaces/{WS}/lakehouses"): [resp(corpo={"value": [{"id": LH, "displayName": "LakehouseOeL"}]})],
        ("GET", f"{API}/workspaces/{WS}/notebooks"): [resp(corpo={"value": [{"id": NB, "displayName": "als_00"}]})],
        ("GET", f"{API}/workspaces"): [resp(corpo={"value": [{"id": WS, "displayName": "Prod"}]})],
    })
    assert ex.localizar("Prod", "LakehouseOel", "als_00") == {"ws": WS, "lh": LH, "nb": NB}
    with pytest.raises(SystemExit, match="não publicado"):
        ex.localizar("Prod", "LakehouseOel", "als_99")


def test_checar_aceita_leitura_com_definicao_assincrona(monkeypatch):
    monkeypatch.delenv("ALS_FABRIC_ESCRITA", raising=False)
    op = f"{API}/operations/op-1"
    ex = executor({
        ("POST", f"{API}/workspaces/{WS}/notebooks/{NB}/getDefinition"): [
            resp(202, headers={"Location": op, "Retry-After": "1"})],
        ("GET", f"{op}/result"): [resp(corpo=definicao("fb.query('SELECT COUNT(*) FROM silver_x')"))],
        ("GET", op): [resp(corpo={"status": "Running"}), resp(corpo={"status": "Succeeded"})],
    })
    ex.checar("als_00_perfil_qualidade", WS, NB)
    assert [c[1] for c in ex.http.chamadas].count(op) == 2


@pytest.mark.parametrize("codigo", ESCRITAS)
def test_checar_recusa_escrita_em_dado_existente(codigo, monkeypatch):
    monkeypatch.delenv("ALS_FABRIC_ESCRITA", raising=False)
    ex = executor({("POST", f"{API}/workspaces/{WS}/notebooks/{NB}/getDefinition"): [resp(corpo=definicao(codigo))]})
    with pytest.raises(Recusado, match="barreira"):
        ex.checar("als_00_perfil_qualidade", WS, NB)


def test_checar_recusa_nome_antes_de_chamar_a_api():
    ex = executor({})
    with pytest.raises(Recusado):
        ex.checar("outro_notebook", WS, NB)
    assert ex.http.chamadas == []


def test_executar_segue_location_ate_concluir():
    ex = executor({
        ("POST", f"{API}/workspaces/{WS}/items/{NB}/jobs/instances"): [
            resp(202, headers={"Location": JOB, "Retry-After": "5"})],
        ("GET", JOB): [resp(corpo={"status": "NotStarted"}), resp(corpo={"status": "InProgress"}),
                       resp(corpo={"status": "Completed", "endTimeUtc": "2026-10-27T18:00:00"})],
    })
    job = ex.executar(WS, NB)
    assert job["status"] == "Completed" and job["location"] == JOB
    metodo, url, params = ex.http.chamadas[0]
    assert metodo == "POST" and params == {"jobType": "RunNotebook"}
    assert [c[1] for c in ex.http.chamadas].count(JOB) == 3


def test_executar_reporta_falha_e_timeout():
    rotas = {("POST", f"{API}/workspaces/{WS}/items/{NB}/jobs/instances"): [resp(202, headers={"Location": JOB})],
             ("GET", JOB): [resp(corpo={"status": "Failed", "failureReason": {"message": "erro"}})]}
    assert executor(rotas).executar(WS, NB)["failureReason"] == {"message": "erro"}
    rotas[("GET", JOB)] = [resp(corpo={"status": "InProgress"})]
    assert executor(rotas).executar(WS, NB, timeout=-1)["status"] == "Timeout"


def test_executar_propaga_erro_http():
    ex = executor({("POST", f"{API}/workspaces/{WS}/items/{NB}/jobs/instances"): [resp(403)]})
    with pytest.raises(requests.HTTPError):
        ex.executar(WS, NB)


def test_baixar_lista_pagina_e_grava_em_data(tmp_path):
    base = f"{LH}/Files/als_oilmodel/perfil"
    ex = executor({
        ("GET", f"{ONELAKE}/{WS}/{base}/perfil.json"): [resp(conteudo=b'{"ok": 1}')],
        ("GET", f"{ONELAKE}/{WS}/{base}/sub/x.parquet"): [resp(conteudo=b"PAR1")],
        ("GET", f"{ONELAKE}/{WS}"): [
            resp(corpo={"paths": [{"name": f"{base}/sub", "isDirectory": "true"},
                                  {"name": f"{base}/perfil.json", "contentLength": "9"}]},
                 headers={"x-ms-continuation": "c1"}),
            resp(corpo={"paths": [{"name": f"{base}/sub/x.parquet"}]})],
    })
    arquivos = ex.baixar(WS, LH, "perfil", tmp_path)
    assert (tmp_path / "perfil/perfil.json").read_bytes() == b'{"ok": 1}'
    assert (tmp_path / "perfil/sub/x.parquet").read_bytes() == b"PAR1"
    assert len(arquivos) == 2
    listagens = [c[2] for c in ex.http.chamadas if c[1] == f"{ONELAKE}/{WS}"]
    assert listagens[0]["directory"] == base and listagens[1]["continuation"] == "c1"
    assert all(m == "GET" for m, _, _ in ex.http.chamadas)  # só leitura no OneLake


def test_baixar_pasta_inexistente_nao_falha(tmp_path):
    ex = executor({("GET", f"{ONELAKE}/{WS}"): [resp(404)]})
    assert ex.baixar(WS, LH, "perfil", tmp_path) == []


def test_baixar_recusa_caminho_fora_de_data(tmp_path):
    ex = executor({("GET", f"{ONELAKE}/{WS}"): [
        resp(corpo={"paths": [{"name": f"{LH}/Files/als_oilmodel/../../fora.txt"}]})]})
    with pytest.raises(RuntimeError, match="fora de data"):
        ex.baixar(WS, LH, "perfil", tmp_path / "data")


def test_auth_device_usa_device_code(monkeypatch):
    import azure.identity

    criadas = []

    class FakeDevice:
        def __init__(self, **kw):
            criadas.append(kw)

    monkeypatch.setattr(azure.identity, "DeviceCodeCredential", FakeDevice)
    monkeypatch.setenv("ALS_AUTH", "device")
    from scripts.fabric_run import credencial

    assert isinstance(credencial(), FakeDevice)
    assert callable(criadas[0]["prompt_callback"]) and "cache_persistence_options" in criadas[0]


def test_main_recusa_nome_sem_api(monkeypatch):
    import scripts.fabric_run as fr

    monkeypatch.setattr(sys, "argv", ["fabric_run.py", "perfil_qualidade"])
    monkeypatch.setattr(fr, "Executor", lambda *a, **k: pytest.fail("não deveria autenticar"))
    with pytest.raises(SystemExit, match="als_"):
        fr.main()
