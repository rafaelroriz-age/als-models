# -*- coding: utf-8 -*-
"""Dispara automaticamente o próximo lote de tarefas do BACKLOG.md como agentes em background.

Uso:
    python scripts/run_backlog.py run [--ambiente offline] [--dry]
    python scripts/run_backlog.py status
    python scripts/run_backlog.py fetch
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Fix encoding on Windows
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

BACKLOG = Path(__file__).resolve().parent.parent / "BACKLOG.md"
PROGRESSO = Path(__file__).resolve().parent.parent / "PROGRESSO.md"
LOGS = Path(__file__).resolve().parent.parent / ".claude" / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

# Importa as funções do backlog.py
sys.path.insert(0, str(Path(__file__).resolve().parent))
from backlog import ler, prontas, lote, lista


def cmd_run(args):
    """Dispara o próximo lote em background como agentes isolados."""
    linhas, tarefas = ler()
    prox = prontas(tarefas, args.ambiente)
    if not prox:
        print("❌ Nenhuma tarefa liberada.")
        return
    paralelo = lote(prox)
    print(f"🚀 Disparando {len(paralelo)} tarefas em background (worktree isolado):\n")

    agentes_disparados = []
    for t in paralelo:
        aid = f"{t['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        cmd = [
            "claude", "agent", "run",
            "--name", f"backlog-{t['id']}",
            "--model", "sonnet",  # ou opus, conforme preferência
            "--worktree",
            t["prompt"].strip()
        ]

        if args.dry:
            print(f"  [{t['id']}] (dry-run) {t['titulo'][:50]}")
            print(f"       > {' '.join(cmd[:6])} ...\n")
        else:
            try:
                # Salva o log da tarefa
                log_file = LOGS / f"{aid}.log"
                with open(log_file, "w", encoding="utf-8") as f:
                    f.write(f"Tarefa: {t['id']}\nTítulo: {t['titulo']}\nHora: {datetime.now().isoformat()}\n\n")

                # Dispara em background
                proc = subprocess.Popen(
                    cmd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                agentes_disparados.append({"id": t["id"], "pid": proc.pid, "log": str(log_file)})
                print(f"  ✅ {t['id']:4} → {t['papel']:22} {t['titulo'][:50]}")
                print(f"       PID={proc.pid}  log={log_file.name}\n")
            except Exception as e:
                print(f"  ❌ {t['id']:4} → erro ao disparar: {e}\n")

    # Salva metadados do lote
    lote_meta = {
        "timestamp": datetime.now().isoformat(),
        "ambiente": args.ambiente or "mixed",
        "tarefas": [{"id": t["id"], "titulo": t["titulo"]} for t in paralelo],
        "agentes_disparados": agentes_disparados
    }
    meta_file = LOGS / f"lote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    meta_file.write_text(json.dumps(lote_meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"📋 Metadados salvo em: {meta_file.name}")
    print(f"📊 Para acompanhar, rode: python scripts/run_backlog.py status")


def cmd_status(args):
    """Mostra o status atual do backlog e dos agentes rodando."""
    linhas, tarefas = ler()

    # Conta por status
    totais = {"todo": 0, "doing": 0, "done": 0, "blocked": 0}
    for t in tarefas.values():
        s = t["status"]
        totais[s] = totais.get(s, 0) + 1

    print("\n📊 STATUS DO BACKLOG")
    print("=" * 60)
    print(f"Total de tarefas: {len(tarefas)}")
    print(f"  ✅ Concluídas (done): {totais.get('done', 0)}")
    print(f"  🔄 Em progresso (doing): {totais.get('doing', 0)}")
    print(f"  ⏳ Pendentes (todo): {totais.get('todo', 0)}")
    print(f"  🚫 Bloqueadas (blocked): {totais.get('blocked', 0)}")

    # Próximo lote
    prox = prontas(tarefas)
    paralelo = lote(prox) if prox else []
    print(f"\n🚀 Próximo lote seguro: {len(paralelo)} tarefas")
    for t in paralelo[:5]:
        print(f"  - {t['id']:4} [{t['ambiente']:7}] {t['titulo'][:45]}")
    if len(paralelo) > 5:
        print(f"  ... e {len(paralelo) - 5} mais")

    # Logs recentes
    print(f"\n📁 Logs recentes:")
    for log in sorted(LOGS.glob("lote_*.json"), reverse=True)[:3]:
        meta = json.loads(log.read_text(encoding="utf-8"))
        n_tarefas = len(meta.get("tarefas", []))
        print(f"  {log.name:35} {n_tarefas} tarefas em {meta.get('timestamp', '?')[:10]}")


def cmd_fetch(args):
    """Busca resultados dos agentes e atualiza BACKLOG.md e PROGRESSO.md."""
    print("⏳ Buscando resultados dos agentes... (não implementado ainda)")
    print("   Próxima etapa: integração com a API do Claude Code ou polling de arquivos.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("run", help="Dispara o próximo lote em background")
    p.add_argument("--ambiente", choices=("offline", "fabric", "humano"))
    p.add_argument("--dry", action="store_true", help="Simula sem disparar")

    sub.add_parser("status", help="Mostra o status do backlog e agentes")
    sub.add_parser("fetch", help="Busca resultados dos agentes (não pronto)")

    args = ap.parse_args()

    {
        "run": lambda: cmd_run(args),
        "status": lambda: cmd_status(args),
        "fetch": lambda: cmd_fetch(args),
    }[args.cmd]()


if __name__ == "__main__":
    main()
