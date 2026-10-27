"""Dispara o BACKLOG.md em sessões background do Claude Code, integra as concluídas na main e gera o PROGRESSO.md.

Uso:
    python scripts/run_backlog.py run    [--ambiente offline|fabric|humano] [--model X] [--dry]
    python scripts/run_backlog.py colher [--dry]     # commita, faz merge na main e marca done o que terminou
    python scripts/run_backlog.py auto   [--ambiente X] [--intervalo 120]   # colher + run em loop
    python scripts/run_backlog.py restart [T01 T02 ...] [--dry] [--auto]   # recomeça tarefas doing/blocked
    python scripts/run_backlog.py status             # imprime e regenera PROGRESSO.md
O modelo, o esforço e o teto de gasto vêm do campo `Dificuldade` de cada tarefa (tabela ROTA).
Acompanhar: `claude agents`, `claude logs <id>`, `claude attach <id>`, `claude stop <id>`.
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from functools import lru_cache
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


@lru_cache(maxsize=1)
def _identidade():
    ok = all(subprocess.run(["git", "config", "--get", k], capture_output=True, text=True, cwd=RAIZ).stdout.strip()
             for k in ("user.name", "user.email"))
    return [] if ok else ["-c", "user.name=backlog-auto", "-c", "user.email=backlog-auto@localhost"]


def git(*a, cwd=RAIZ):
    # Commits automáticos não dependem de chave de assinatura, agente GPG/SSH nem credenciais (nunca há push).
    sem_chave = ["-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *_identidade()]
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    return subprocess.run(["git", *sem_chave, *a], capture_output=True, text=True, encoding="utf-8", cwd=cwd, env=env)


def salvar_pendentes():
    """Commita as mudanças em arquivos já rastreados da main (não toca em arquivos novos)."""
    if not git("status", "--porcelain", "--untracked-files=no").stdout.strip():
        return False
    git("add", "-u")
    git("commit", "-m", "backlog: salva mudanças pendentes antes de integrar")
    return True


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
    if not args.dry:
        if salvar_pendentes():
            print("  main: mudanças pendentes commitadas automaticamente.")
        if git("status", "--porcelain", "--untracked-files=no").stdout.strip():
            sys.exit("A main continua com mudanças que não puderam ser commitadas (merge em andamento ou hook recusou); verifique `git status`.")
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
                subprocess.run([exe, "rm", s["id"]], capture_output=True)
            git("worktree", "prune")
            git("branch", "-d", f"worktree-backlog-{t['id']}")
            feitas += 1
    if feitas:
        print("\nLote concluído? Rode o 'Fechamento de lote' do BACKLOG.md antes do próximo.")
    return feitas


def cmd_restart(args):
    """Descarta sessão, worktree e branch de tarefas travadas e as devolve para `todo`."""
    linhas, tarefas = ler()
    exe = achar_claude()
    sessoes = {s.get("name"): s for s in (sessoes_ativas(exe) if exe else [])}
    if args.ids:
        alvo = args.ids
    else:
        alvo = [i for i, t in tarefas.items() if t["status"] in ("doing", "blocked")
                and (args.forcar or sessoes.get(f"backlog-{i}", {}).get("status") != "busy")]
        poupadas = [i for i, t in tarefas.items() if t["status"] == "doing" and i not in alvo]
        if poupadas:
            print(f"  Poupadas por estarem trabalhando (use --forcar ou cite o id): {', '.join(poupadas)}")
    desconhecidas = [i for i in alvo if i not in tarefas]
    if desconhecidas:
        sys.exit(f"Tarefas inexistentes: {', '.join(desconhecidas)}")
    feitas = [i for i in alvo if tarefas[i]["status"] == "done"]
    if feitas:
        sys.exit(f"{', '.join(feitas)} já está done (integrada na main); não há o que reiniciar.")
    if not alvo:
        print("Nenhuma tarefa doing/blocked para reiniciar.")
    else:
        for tid in alvo:
            nome, branch = f"backlog-{tid}", f"worktree-backlog-{tid}"
            perdidos = len(git("log", "--oneline", f"main..{branch}").stdout.split("\n")) - 1 if (WORKTREES / nome).exists() else 0
            print(f"  {tid}  {'(simulação) ' if args.dry else ''}reinicia"
                  + (f" (descarta {perdidos} commit(s) não integrados)" if perdidos > 0 else ""))
            if args.dry:
                continue
            s = sessoes.get(nome)
            if s and exe:
                subprocess.run([exe, "stop", s["id"]], capture_output=True)
                subprocess.run([exe, "rm", s["id"]], capture_output=True)
            if (WORKTREES / nome).exists():
                git("worktree", "remove", "-f", "-f", str(WORKTREES / nome))
            git("worktree", "prune")
            git("branch", "-D", branch)
            gravar_status(linhas, tarefas, tid, "todo")
        if not args.dry:
            commitar_controle("backlog: reinicia " + ", ".join(alvo))
    if args.auto and not args.dry:
        cmd_auto(argparse.Namespace(ambiente=args.ambiente, intervalo=args.intervalo))


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
    p.add_argument("--ambiente", choices=("offline", "fabric", "humano"), help="sem o filtro, dispara todos")
    p.add_argument("--intervalo", type=int, default=120, help="segundos entre verificações")
    p = sub.add_parser("restart", help="recomeça tarefas travadas (doing/blocked); sem ids, todas elas")
    p.add_argument("ids", nargs="*")
    p.add_argument("--dry", action="store_true")
    p.add_argument("--forcar", action="store_true", help="inclui também as sessões que estão trabalhando")
    p.add_argument("--auto", action="store_true", help="depois de reiniciar, retoma o fluxo automático")
    p.add_argument("--ambiente", choices=("offline", "fabric", "humano"))
    p.add_argument("--intervalo", type=int, default=120)
    sub.add_parser("status")
    args = ap.parse_args()
    if sys.platform.startswith("win"):
        sys.stdout.reconfigure(encoding="utf-8")
    {"run": cmd_run, "colher": cmd_colher, "auto": cmd_auto, "restart": cmd_restart, "status": cmd_status}[args.cmd](args)


if __name__ == "__main__":
    main()
