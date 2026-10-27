"""Hook PostToolUse: lembra a regra de documentação do AGENTS.md após editar código ou rodar scripts."""
import json
import re
import sys

CODIGO = re.compile(r"\.(py|ipynb|sql)$", re.IGNORECASE)
EXECUCAO = re.compile(r"\b(python|pytest)\b", re.IGNORECASE)

try:
    evento = json.load(sys.stdin)
except ValueError:
    sys.exit(0)

entrada = evento.get("tool_input") or {}
caminho = (entrada.get("file_path") or "").replace("\\", "/")
comando = entrada.get("command") or ""

if "/.claude/" in caminho:
    sys.exit(0)
if not (CODIGO.search(caminho) or EXECUCAO.search(comando)):
    sys.exit(0)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": (
            "Lembrete (AGENTS.md, regra de documentação): antes de encerrar, registre o que mudou "
            "no doc do papel, marque o backlog em docs_fabric/06 e 12, decisões/descobertas no 13 "
            "e doc novo no LEIA-ME."
        ),
    }
}))
