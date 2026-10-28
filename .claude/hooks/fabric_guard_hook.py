"""Hook PreToolUse: impede que agentes escrevam código ou comandos que alterem dados existentes no Fabric."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from fabric_guard import violacoes  # noqa: E402

CODIGO = re.compile(r"\.(py|ipynb|sql)$", re.IGNORECASE)
ISENTOS = ("scripts/fabric_guard.py", "tests/test_fabric_guard.py", "/.claude/hooks/")
COMANDO_FABRIC = re.compile(r"fabric|pyodbc|sqlcmd|spark|onelake|lakehouse", re.IGNORECASE)

try:
    evento = json.load(sys.stdin)
except ValueError:
    sys.exit(0)

entrada = evento.get("tool_input") or {}
caminho = (entrada.get("file_path") or "").replace("\\", "/")
if any(i in caminho for i in ISENTOS):
    sys.exit(0)

if CODIGO.search(caminho):
    texto = entrada.get("content") or entrada.get("new_string") or ""
else:
    comando = entrada.get("command") or ""
    texto = comando if COMANDO_FABRIC.search(comando) else ""

achados = violacoes(texto)
if achados:
    print(
        "Bloqueado pela barreira do Fabric (" + ", ".join(achados) + "): este projeto só lê dados existentes "
        "e grava em Files/als_oilmodel/ (views temporárias são livres). Para uma tabela temporária de "
        "desenvolvimento, use o prefixo als_dev_ e peça ao usuário ALS_FABRIC_DEV=1; para outra escrita "
        "legítima, ALS_FABRIC_ESCRITA=1 na sessão.",
        file=sys.stderr,
    )
    sys.exit(2)
