import pytest

from scripts.fabric_guard import violacoes


@pytest.mark.parametrize("texto", [
    "spark.sql('INSERT INTO silver_x SELECT * FROM y')",
    "spark.sql('update silver_x set a = 1')",
    "DELETE FROM dbo.tabela WHERE id = 1",
    "DROP TABLE silver_x",
    "df.write.mode('overwrite').saveAsTable('silver_x')",
    "df.write.format('delta').save('abfss://x/LakehouseOel/Tables/silver_x')",
    "DeltaTable.forName(spark, 'silver_x').delete('a > 1')",
])
def test_bloqueia_escrita(texto, monkeypatch):
    monkeypatch.delenv("ALS_FABRIC_ESCRITA", raising=False)
    assert violacoes(texto)


@pytest.mark.parametrize("texto", [
    "SELECT * FROM silver_x WHERE data >= '2024-01-01'",
    "df.to_parquet('/lakehouse/default/Files/als_oilmodel/perfil/x.parquet')",
    "http.put(url, params={'resource': 'file'})  # Files/als_oilmodel/wheels/x.whl",
    "# a coluna updated_at não é UPDATE",
])
def test_permite_leitura_e_files(texto, monkeypatch):
    monkeypatch.delenv("ALS_FABRIC_ESCRITA", raising=False)
    assert not violacoes(texto)


def test_liberacao_explicita(monkeypatch):
    monkeypatch.setenv("ALS_FABRIC_ESCRITA", "1")
    assert not violacoes("DROP TABLE silver_x")


def test_codigo_atual_do_projeto_passa(monkeypatch):
    from pathlib import Path
    monkeypatch.delenv("ALS_FABRIC_ESCRITA", raising=False)
    raiz = Path(__file__).resolve().parents[1]
    for pasta in ("src", "notebooks", "scripts"):
        for py in (raiz / pasta).rglob("*.py"):
            if py.name == "fabric_guard.py":
                continue
            assert not violacoes(py.read_text(encoding="utf-8")), py


def _hook(payload, monkeypatch):
    import json
    import subprocess
    import sys
    from pathlib import Path
    monkeypatch.delenv("ALS_FABRIC_ESCRITA", raising=False)
    hook = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "fabric_guard_hook.py"
    return subprocess.run([sys.executable, str(hook)], input=json.dumps(payload), text=True,
                          capture_output=True).returncode


def test_hook_bloqueia_notebook_com_drop(monkeypatch):
    p = {"tool_input": {"file_path": "C:/x/notebooks/a.py", "content": "spark.sql('DROP TABLE silver_x')"}}
    assert _hook(p, monkeypatch) == 2


def test_hook_permite_gravar_em_files(monkeypatch):
    p = {"tool_input": {"file_path": "C:/x/notebooks/a.py", "content": "df.to_parquet('Files/als_oilmodel/x.parquet')"}}
    assert _hook(p, monkeypatch) == 0


def test_hook_ignora_comando_sem_relacao_com_fabric(monkeypatch):
    assert _hook({"tool_input": {"command": "git commit -m 'sem DROP TABLE aqui'"}}, monkeypatch) == 0
