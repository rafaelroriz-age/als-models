"""Dispara o BACKLOG.md em sessões background do Claude Code, integra as concluídas na main e gera o PROGRESSO.md.

Uso:
    python scripts/run_backlog.py run    [--ambiente offline|fabric|humano] [--model X] [--dry]
    python scripts/run_backlog.py colher [--dry]     # commita, faz merge na main e marca done o que terminou
    python scripts/run_backlog.py auto   [--ambiente offline] [--intervalo 120]   # colher + run em loop
    python scripts/run_backlog.py status              # imprime e regenera PROGRESSO.md
O modelo, o esforço e o teto de gasto vêm do campo `Dificuldade` de cada tarefa (tabela ROTA).
Acompanhar: `claude agents`, `claude logs <id>`, `claude attach <id>`, `claude stop <id>`.
"""
import argparse
import glob
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backlog import gravar_status, ler, lote, prontas  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
PROGRESSO = RAIZ / "PROGRESSO.md"
LOGS = RAIZ / ".claude" / "logs"
WORKTREES = RAIZ / ".claude" / "worktrees"
ICONE = {"todo": "⬜", "doing": "🔄", "done": "✅", "blocked": "⛔"}
ROTA = {
    "baixa": {"model": "haiku", "effort": "low", "budget": "1"},
    "media": {"model": "sonnet", "effort": "medium", "budget": "3"},
    "alta": {"model": "opus", "effort": "high", "budget": "8"},
}
SO_CONTROLE = {"BACKLOG.md", "PROGRESSO.md"}

PREAMBULO = (
    "Você roda em background num worktree isolado, sem ninguém para aprovar prompts. "
    "Faça só a tarefa abaixo, rode `python -m pytest`, registre o resultado no doc indicado e, ao terminar, "
    "faça `git add` e `git commit` na branch do worktree (sem push). Não edite BACKLOG.md nem PROGRESSO.md: "
    "o status é atualizado pelo integrador. Seja econômico: leia só os arquivos citados e os que precisar. "
    "Nunca altere dados que já existem no Fabric: leitura e gravação em Files/als_oilmodel/ apenas "
    "(barreira em scripts/fabric_guard.py).\n\n"
)


def git(*a, cwd=RAIZ):
    return subprocess.run(["git", *a], capture_output=True, text=True, encoding="utf-8", cwd=cwd)


def achar_claude():
    exe = shutil.which("claude")
    if exe:
        return exe
    candidatos = sorted(glob.glob(str(Path.home() / ".vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude*")))
    return candidatos[-1] if candidatos else None


def sessoes_ativas(exe):
    try:
        r = subprocess.run([exe, "agents", "--json"], capture_output=True, text=True, timeout=30, encoding="utf-8")
        return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else []
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return []


def rota(t):
    return ROTA.get(t.get("dificuldade", "media"), ROTA["media"])


def commitar_controle(msg):
    if git("diff", "--quiet", "--", "BACKLOG.md").returncode:
        git("commit", "-m", msg, "--", "BACKLOG.md")


def cmd_run(args):
    exe = achar_claude()
    if not exe and not args.dry:
        sys.exit("CLI `claude` não encontrado no PATH nem na extensão do VS Code.")
    linhas, tarefas = ler()
    paralelo = lote(prontas(tarefas, args.ambiente))
    if not paralelo:
        print("Nenhuma tarefa liberada.")
        return 0
    print(f"{'(simulação) ' if args.dry else ''}Lote de {len(paralelo)} tarefas:")
    disparadas = []
    for t in paralelo:
        nome = f"backlog-{t['id']}"
        r_ = rota(t)
        modelo = args.model or r_["model"]
        cmd = [exe or "claude", "--bg", "-w", nome, "-n", nome, "--model", modelo, "--effort", r_["effort"],
               "--max-budget-usd", r_["budget"], "--permission-mode", "bypassPermissions", "--",PREAMBULO + t["prompt"].strip()]
        rotulo = f"{t['id']}  [{t.get('dificuldade', 'media')} → {modelo}/{r_['effort']}/US${r_['budget']}]"
        if args.dry:
            print(f"  {rotulo} {t['titulo']}")
            continue
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=RAIZ)
        saida = (r.stdout + r.stderr).strip()
        if r.returncode == 0:
            gravar_status(linhas, tarefas, t["id"], "doing")
            disparadas.append({"tarefa": t["id"], "modelo": modelo, "effort": r_["effort"], "retorno": saida})
            print(f"  {rotulo} disparada")
        else:
            print(f"  {rotulo} FALHOU (código {r.returncode}): {saida[:300]}")
    if disparadas:
        commitar_controle("backlog: disparo de " + ", ".join(d["tarefa"] for d in disparadas))
        LOGS.mkdir(parents=True, exist_ok=True)
        meta = LOGS / f"lote_{datetime.now():%Y%m%d_%H%M%S}.json"
        meta.write_text(json.dumps(disparadas, indent=2, ensure_ascii=False), encoding="utf-8")
        print("\nQuando terminarem: `python scripts/run_backlog.py colher` (ou deixe `auto` rodando).")
    return len(disparadas)


def integrar(tid, dry):
    """Garante o commit no worktree e faz merge na main. Retorna (ok, mensagem)."""
    wt, branch = WORKTREES / f"backlog-{tid}", f"worktree-backlog-{tid}"
    if not wt.exists():
        return False, "worktree não encontrado"
    if git("status", "--porcelain", cwd=wt).stdout.strip():
        if dry:
            return True, "(simulação) commit automático das mudanças pendentes + merge"
        git("add", "-A", cwd=wt)
        git("commit", "-m", f"{tid}: commit automático do integrador", cwd=wt)
    if not git("log", "--oneline", f"main..{branch}").stdout.strip():
        return False, "terminou sem nenhuma mudança (verifique `claude logs`)"
    if dry:
        return True, "(simulação) merge na main"
    r = git("merge", "--no-ff", "-m", f"Integra {tid} (backlog)", branch)
    if r.returncode:
        conflitos = set(git("diff", "--name-only", "--diff-filter=U").stdout.split())
        if conflitos and conflitos <= SO_CONTROLE:
            git("checkout", "--ours", "--", *conflitos)
            git("add", "--", *conflitos)
            git("commit", "--no-edit")
        else:
            git("merge", "--abort")
            return False, f"conflito de merge em {', '.join(sorted(conflitos)) or (r.stdout + r.stderr).strip()[:200]}; resolva à mão"
    return True, "integrada na main"


def cmd_colher(args):
    exe = achar_claude()
    sessoes = {s.get("name"): s for s in (sessoes_ativas(exe) if exe else [])}
    linhas, tarefas = ler()
    doing = [t for t in tarefas.values() if t["status"] == "doing"]
    if not doing:
        print("Nada em andamento.")
        return 0
    if not args.dry and git("status", "--porcelain", "--untracked-files=no").stdout.strip():
        sys.exit("A main tem mudanças não commitadas; commite ou guarde (git stash) antes de colher.")
    feitas = 0
    for t in doing:
        s = sessoes.get(f"backlog-{t['id']}")
        estado = s.get("status") if s else "encerrada"
        if estado == "busy":
            print(f"  {t['id']}  trabalhando")
            continue
        if estado == "waiting":
            print(f"  {t['id']}  esperando {s.get('waitingFor', '?')}: `claude attach {s.get('id')}`")
            continue
        ok, msg = integrar(t["id"], args.dry)
        print(f"  {t['id']}  {msg}")
        if ok and not args.dry:
            gravar_status(linhas, tarefas, t["id"], "done")
            commitar_controle(f"backlog: {t['id']} done")
            if s and exe:
                subprocess.run([exe, "stop", s["id"]], capture_output=True)
            feitas += 1
    if feitas:
        print("\nLote concluído? Rode o 'Fechamento de lote' do BACKLOG.md antes do próximo.")
    return feitas


def cmd_auto(args):
    while True:
        cmd_colher(argparse.Namespace(dry=False))
        disparadas = cmd_run(argparse.Namespace(ambiente=args.ambiente, model=None, dry=False))
        _, tarefas = ler()
        if not disparadas and not any(t["status"] == "doing" for t in tarefas.values()):
            print("Nada em andamento nem liberado. Fim.")
            return
        time.sleep(args.intervalo)


def gerar_progresso(tarefas, sessoes):
    cont = {s: sum(t["status"] == s for t in tarefas.values()) for s in ICONE}
    prox = lote(prontas(tarefas))
    L = [
        "# Progresso — ALS OilModel",
        "",
        "> Gerado por `python scripts/run_backlog.py status` a partir do [BACKLOG.md](BACKLOG.md). Não edite à mão.",
        "",
        f"Atualizado em {datetime.now():%d/%m/%Y %H:%M} · **{cont['done']}/{len(tarefas)} concluídas** · "
        f"{cont['doing']} em andamento · {cont['todo']} a fazer · {cont['blocked']} bloqueadas",
        "",
        "## Próximo lote (pode rodar em paralelo)",
        "",
    ]
    L += [f"- **{t['id']}** [{t['ambiente']}, {t.get('dificuldade', 'media')} → {rota(t)['model']}] {t['titulo']}"
          for t in prox] or ["- nenhum liberado"]
    bg = [s for s in sessoes if str(s.get("name", "")).startswith("backlog-")]
    L += ["", "## Sessões em background agora", ""]
    L += [f"- {s['name']}: {s.get('status', '?')}" + (f" ({s['waitingFor']})" if s.get("waitingFor") else "")
          for s in bg] or ["- nenhuma"]
    blocos = {}
    for t in tarefas.values():
        blocos.setdefault(t["bloco"], []).append(t)
    for bloco, ts in blocos.items():
        feitas = sum(t["status"] == "done" for t in ts)
        L += ["", f"## {bloco} ({feitas}/{len(ts)})", "",
              "| | Tarefa | Papel | Ambiente | Dificuldade | Depende |", "|---|---|---|---|---|---|"]
        L += [f"| {ICONE[t['status']]} | **{t['id']}** {t['titulo']} | {t['papel']} | {t['ambiente']} | "
              f"{t.get('dificuldade', 'media')} | {t['depende']} |" for t in ts]
    return "\n".join(L) + "\n"


def cmd_status(args):
    _, tarefas = ler()
    exe = achar_claude()
    texto = gerar_progresso(tarefas, sessoes_ativas(exe) if exe else [])
    PROGRESSO.write_text(texto, encoding="utf-8")
    print(texto)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run")
    p.add_argument("--ambiente", choices=("offline", "fabric", "humano"))
    p.add_argument("--model", help="força um modelo para todo o lote (ignora a Dificuldade)")
    p.add_argument("--dry", action="store_true", help="mostra o que seria disparado, sem disparar nem gravar nada")
    sub.add_parser("colher").add_argument("--dry", action="store_true")
    p = sub.add_parser("auto")
    p.add_argument("--ambiente", choices=("offline", "fabric", "humano"), default="offline")
    p.add_argument("--intervalo", type=int, default=120, help="segundos entre verificações")
    sub.add_parser("status")
    args = ap.parse_args()
    if sys.platform.startswith("win"):
        sys.stdout.reconfigure(encoding="utf-8")
    {"run": cmd_run, "colher": cmd_colher, "auto": cmd_auto, "status": cmd_status}[args.cmd](args)


if __name__ == "__main__":
    main()
