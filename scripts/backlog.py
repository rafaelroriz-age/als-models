"""Lê o BACKLOG.md: lista tarefas, mostra o próximo lote paralelo, imprime prompts e atualiza status.

Uso:
    python scripts/backlog.py list [--ambiente offline|fabric|humano]
    python scripts/backlog.py next [--ambiente offline] [--prompts]
    python scripts/backlog.py show T07
    python scripts/backlog.py set T07 done
"""
import argparse
import re
import sys
from pathlib import Path

BACKLOG = Path(__file__).resolve().parent.parent / "BACKLOG.md"
STATUS = ("todo", "doing", "done", "blocked")
TITULO = re.compile(r"^### (T\d+) · (.+)$")
CAMPO = re.compile(r"^- \*\*(\w+):\*\* ?(.*)$")


def ler():
    linhas = BACKLOG.read_text(encoding="utf-8").splitlines()
    tarefas, atual, em_prompt, bloco = {}, None, False, ""
    for i, linha in enumerate(linhas):
        if linha.startswith("## Bloco"):
            bloco = linha[3:].strip()
        m = TITULO.match(linha)
        if m:
            atual = {"id": m.group(1), "titulo": m.group(2), "linha_status": None, "prompt": "", "bloco": bloco}
            tarefas[atual["id"]] = atual
            em_prompt = False
            continue
        if atual is None:
            continue
        if em_prompt:
            if linha.startswith("```"):
                if atual["prompt"]:
                    em_prompt = False
                continue
            atual["prompt"] += linha + "\n"
            continue
        c = CAMPO.match(linha)
        if c:
            chave, valor = c.group(1).lower(), c.group(2).strip()
            atual[chave] = valor
            if chave == "status":
                atual["linha_status"] = i
            em_prompt = chave == "prompt"
            if em_prompt:
                atual["prompt"] = ""
    return linhas, tarefas


def lista(valor):
    return [v.strip() for v in valor.split(",") if v.strip() and v.strip() != "—"]


def prontas(tarefas, ambiente=None):
    return [
        t for t in tarefas.values()
        if t["status"] == "todo"
        and all(tarefas[d]["status"] == "done" for d in lista(t["depende"]))
        and (ambiente is None or t["ambiente"] == ambiente)
    ]


def conflita(a, b):
    for x in lista(a["toca"]):
        for y in lista(b["toca"]):
            x, y = x.split(" ")[0].rstrip("/"), y.split(" ")[0].rstrip("/")
            if x == y or x.startswith(y + "/") or y.startswith(x + "/"):
                return True
    return False


def lote(candidatas):
    escolhidas = []
    for t in candidatas:
        if not any(conflita(t, e) for e in escolhidas):
            escolhidas.append(t)
    return escolhidas


def cmd_list(tarefas, args):
    for t in tarefas.values():
        if args.ambiente and t["ambiente"] != args.ambiente:
            continue
        deps = t["depende"]
        print(f'{t["id"]}  {t["status"]:<7} {t["ambiente"]:<7} {t["papel"]:<22} {t["titulo"]}  [dep: {deps}]')


def cmd_next(tarefas, args):
    prox = prontas(tarefas, args.ambiente)
    if not prox:
        print("Nenhuma tarefa liberada.")
        return
    paralelo = lote(prox)
    espera = [t for t in prox if t not in paralelo]
    print("Lote paralelo seguro (sem arquivos em comum):")
    for t in paralelo:
        print(f'  {t["id"]}  [{t["ambiente"]}] {t["titulo"]}')
    if espera:
        print("Liberadas, mas conflitam com o lote (próxima rodada):")
        for t in espera:
            print(f'  {t["id"]}  [{t["ambiente"]}] {t["titulo"]}')
    if args.prompts:
        for t in paralelo:
            print(f'\n===== {t["id"]} =====\n{t["prompt"]}')


def cmd_show(tarefas, args):
    t = tarefas.get(args.id)
    if not t:
        sys.exit(f"Tarefa {args.id} não existe.")
    print(t["prompt"].rstrip())


def gravar_status(linhas, tarefas, tid, status):
    t = tarefas.get(tid)
    if not t:
        sys.exit(f"Tarefa {tid} não existe.")
    if status not in STATUS:
        sys.exit(f"Status deve ser um de {STATUS}.")
    pendentes = [d for d in lista(t["depende"]) if tarefas[d]["status"] != "done"]
    if status == "done" and pendentes:
        print(f"Aviso: dependências ainda não concluídas: {', '.join(pendentes)}")
    linhas[t["linha_status"]] = f"- **Status:** {status}"
    t["status"] = status
    BACKLOG.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def cmd_set(linhas, tarefas, args):
    gravar_status(linhas, tarefas, args.id, args.status)
    print(f'{args.id} -> {args.status}')


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap =argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for nome in ("list", "next"):
        p = sub.add_parser(nome)
        p.add_argument("--ambiente", choices=("offline", "fabric", "humano"))
        if nome == "next":
            p.add_argument("--prompts", action="store_true", help="imprime também o prompt de cada tarefa do lote")
    sub.add_parser("show").add_argument("id")
    p = sub.add_parser("set")
    p.add_argument("id")
    p.add_argument("status")
    args = ap.parse_args()

    linhas, tarefas = ler()
    {"list": lambda: cmd_list(tarefas, args), "next": lambda: cmd_next(tarefas, args),
     "show": lambda: cmd_show(tarefas, args), "set": lambda: cmd_set(linhas, tarefas, args)}[args.cmd]()


if __name__ == "__main__":
    main()
