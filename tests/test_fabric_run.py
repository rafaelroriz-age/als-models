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


# ---------------------------------------------------------------- T30: registro por convenção e parâmetros
import scripts.fabric_deploy as fd  # noqa: E402
import scripts.fabric_run as fr  # noqa: E402

NB_DEV = '"""Doc."""\n# %% [parameters]\nlakehouse = "LakehouseOel"\n\n# %%\nPASTA_FABRIC = "dev_x"\nprint(lakehouse)\n'


def arvore(tmp_path, arquivos):
    for rel, texto in arquivos.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(texto, encoding="utf-8")
    return tmp_path


def test_descobre_als_por_convencao_e_mantem_legados(tmp_path):
    raiz = arvore(tmp_path, {"notebooks/50_dev/als_50_x.py": NB_DEV, "notebooks/50_dev/rascunho.py": "x = 1\n",
                             "notebooks/00/als_00_y.py": "y = 2\n"})
    achados = fd.descobrir_notebooks(raiz, legados={"als_00_legado": raiz / "legado.py"})
    assert list(achados) == ["als_00_legado", "als_00_y", "als_50_x"]
    reais = fd.descobrir_notebooks()
    assert set(fd.NOTEBOOKS) <= set(reais) and {"als_50_pre_consultas", "als_51_views_saida"} <= set(reais)


def test_descoberta_recusa_nome_duplicado(tmp_path):
    raiz = arvore(tmp_path, {"notebooks/a/als_1.py": "", "notebooks/b/als_1.py": ""})
    with pytest.raises(SystemExit, match="duplicado"):
        fd.descobrir_notebooks(raiz, legados={})


def test_selecionar_filtra_e_recusa_desconhecido():
    nbs = {"als_a": "a", "als_b": "b"}
    assert fd.selecionar(nbs, None) == nbs and fd.selecionar(nbs, ["als_b"]) == {"als_b": "b"}
    with pytest.raises(SystemExit, match="não registrado"):
        fd.selecionar(nbs, ["als_c"])


def test_celulas_e_celula_de_parametros(tmp_path):
    py = arvore(tmp_path, {"als_50_x.py": NB_DEV}) / "als_50_x.py"
    nb = fd.para_ipynb(py, "w.whl", None)
    codigo = [c for c in nb["cells"] if c["cell_type"] == "code"]
    assert len(codigo) == 4  # %pip, docstring, parâmetros, corpo
    assert codigo[2]["metadata"] == {"tags": ["parameters"]} and "lakehouse" in "".join(codigo[2]["source"])
    assert codigo[3]["metadata"] == {} and "PASTA_FABRIC" in "".join(codigo[3]["source"])
    legado = fd.para_ipynb(fd.NOTEBOOKS["als_00_perfil_qualidade"], "w.whl", None)
    assert len(legado["cells"]) == 3  # sem `# %%`: célula única, igual ao comportamento anterior


def test_notebooks_registrados_passam_no_guard_e_nao_usam_tables(monkeypatch):
    monkeypatch.delenv("ALS_FABRIC_ESCRITA", raising=False)
    monkeypatch.delenv("ALS_FABRIC_DEV", raising=False)
    for nome, py in fd.descobrir_notebooks().items():
        texto = py.read_text(encoding="utf-8")
        assert fr.violacoes(texto) == [], nome
        if "50_dev" in py.parts:
            assert "saveAs" + "Table" not in texto and "/Tables/" not in texto
            assert "createOrReplaceTempView" in texto


def test_gerar_simulacao_escreve_ipynb_e_recusa_barreira(tmp_path, monkeypatch):
    monkeypatch.delenv("ALS_FABRIC_ESCRITA", raising=False)
    nbs = {n: p for n, p in fd.descobrir_notebooks().items() if n.startswith("als_5")}
    defs = fd.gerar(nbs, "w.whl", None, tmp_path)
    assert set(defs) == {"als_50_pre_consultas", "als_51_views_saida"}
    nb = json.loads((tmp_path / "als_50_pre_consultas.ipynb").read_text(encoding="utf-8"))
    assert any(c["metadata"].get("tags") == ["parameters"] for c in nb["cells"])
    ruim = arvore(tmp_path, {"als_ruim.py": ESCRITAS[0]}) / "als_ruim.py"
    with pytest.raises(SystemExit, match="barreira"):
        fd.gerar({"als_ruim": ruim}, "w.whl", None, tmp_path)
    with pytest.raises(SystemExit, match="als_"):
        fd.gerar({"outro": ruim}, "w.whl", None, tmp_path)


def test_deploy_main_simula_sem_api(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(fd, "DIST", tmp_path)
    monkeypatch.setattr(fd, "construir_wheel", lambda: tmp_path / "als_oilmodel-0.0.0-py3-none-any.whl")
    monkeypatch.setattr(fd, "Cliente", lambda: pytest.fail("simulação não autentica"))
    fd.main(["--notebooks", "als_50_pre_consultas"])
    assert (tmp_path / "fabric/als_50_pre_consultas.ipynb").exists()
    assert "modo simulação" in capsys.readouterr().out


def test_deploy_workspace_e_lakehouse_por_ambiente(tmp_path, monkeypatch):
    monkeypatch.setattr(fd, "construir_wheel", lambda: tmp_path / "w.whl")
    monkeypatch.delenv("ALS_WORKSPACE", raising=False)
    with pytest.raises(SystemExit, match="obrigatório"):
        fd.main(["--aplicar"])
    vistos = []

    class Cli:
        def api(self, metodo, caminho, **kw):
            vistos.append(caminho)
            if caminho == "/workspaces":
                return {"value": [{"id": WS, "displayName": "WS-env"}]}
            return {"value": [{"id": LH, "displayName": "lh_env"}]}

    monkeypatch.setattr(fd, "Cliente", Cli)
    monkeypatch.setenv("ALS_WORKSPACE", "WS-env")
    monkeypatch.setenv("ALS_LAKEHOUSE", "outro")
    with pytest.raises(SystemExit, match="lakehouse não encontrado: outro"):
        fd.main(["--aplicar"])
    assert vistos == ["/workspaces", f"/workspaces/{WS}/lakehouses"]


def test_pasta_saida_legado_convencao_e_padrao(tmp_path):
    raiz = arvore(tmp_path, {"notebooks/als_50_x.py": NB_DEV, "notebooks/als_52_sem.py": "x = 1\n"})
    nbs = fd.descobrir_notebooks(raiz, legados={})
    assert fr.pasta_saida("als_00_perfil_qualidade") == "perfil"
    assert fr.pasta_saida("als_40_backtest_baselines") is None  # legado sem saída: igual a antes
    assert fr.pasta_saida("als_50_x", nbs) == "dev_x" and fr.pasta_saida("als_52_sem", nbs) == "saida"
    assert fr.pasta_saida("als_50_pre_consultas") == "saida"
    assert fr.pasta_saida("als_99_inexistente", nbs) is None


def test_ler_parametros():
    assert fr.ler_parametros(None) == {}
    assert fr.ler_parametros(["lakehouse=LakehouseOel", "data_corte="]) == {"lakehouse": "LakehouseOel",
                                                                             "data_corte": ""}
    with pytest.raises(SystemExit):
        fr.ler_parametros(["sem_igual"])


class HttpCorpo(Http):
    def request(self, metodo, url, **kw):
        self.corpos = getattr(self, "corpos", []) + [kw.get("json")]
        return super().request(metodo, url, **kw)


def test_executar_envia_parametros_so_quando_informados():
    def rotas():
        return {("POST", f"{API}/workspaces/{WS}/items/{NB}/jobs/instances"): [resp(202, headers={"Location": JOB})],
                ("GET", JOB): [resp(corpo={"status": "Completed"})]}

    cred = SimpleNamespace(get_token=lambda escopo: SimpleNamespace(token="t"))
    ex = Executor(cred=cred, http=HttpCorpo(rotas()), dormir=lambda s: None)
    ex.executar(WS, NB)
    assert ex.http.corpos[0] is None  # padrão anterior: POST sem corpo
    ex = Executor(cred=cred, http=HttpCorpo(rotas()), dormir=lambda s: None)
    ex.executar(WS, NB, parametros={"lakehouse": "Outro"})
    assert ex.http.corpos[0] == {"executionData": {"parameters": {"lakehouse": {"value": "Outro", "type": "string"}}}}


def test_main_run_usa_env_parametros_e_pasta_por_convencao(tmp_path, monkeypatch):
    chamadas = {}

    class Ex:
        def localizar(self, ws, lh, nb):
            chamadas["localizar"] = (ws, lh, nb)
            return {"ws": WS, "lh": LH, "nb": NB}

        def checar(self, *a):
            pass

        def executar(self, ws, nb, timeout, parametros):
            chamadas["parametros"] = parametros
            return {"status": "Completed", "segundos": 1.0}

        def baixar(self, ws, lh, pasta, destino):
            chamadas["baixar"] = pasta
            return []

    monkeypatch.setattr(fr, "Executor", Ex)
    monkeypatch.setenv("ALS_LAKEHOUSE", "LhEnv")
    with pytest.raises(SystemExit) as fim:
        fr.main(["als_50_pre_consultas", "--workspace", "W", "--destino", str(tmp_path),
                 "--param", "lakehouse=LakehouseOel"])
    assert fim.value.code == 0
    assert chamadas == {"localizar": ("W", "LhEnv", "als_50_pre_consultas"),
                        "parametros": {"lakehouse": "LakehouseOel"}, "baixar": "saida"}
