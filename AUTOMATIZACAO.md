# Automação do Backlog — Guia Rápido

Tudo pronto para disparar o backlog de forma totalmente automatizada.

## 3 comandos para rodar tudo

```bash
# 1. Ver o status atual
python scripts/run_backlog.py status

# 2. Disparar o próximo lote (primeiros 9 agentes em background, worktree isolado)
python scripts/run_backlog.py run --ambiente offline

# 3. Acompanhar o progresso
cat PROGRESSO.md    # dashboard visual
python scripts/backlog.py list   # tabela detalhada
```

---

## O que acontece ao rodar

```
python scripts/run_backlog.py run --ambiente offline
```

- Identifica o próximo lote de tarefas que podem rodar em paralelo (sem conflito de arquivos).
- Dispara um agente para cada tarefa em background, em worktree isolado.
- Salva PID, logs e metadados em `.claude/logs/`.
- Imprime na tela o status de cada disparo.

**Lote 1 (agora):** T01, T06–T13, T23 (9 tarefas)
- ~3–4 horas se rodarem em paralelo
- Cada agente roda num worktree separado, sem conflito

---

## Depois que o Lote 1 terminar

1. **Rode o "Fechamento de lote":**
   ```bash
   # Cole o prompt de Fechamento de Lote do BACKLOG.md
   # (atualiza docs_fabric/06, 12 e 13)
   ```

2. **Veja o progresso:**
   ```bash
   python scripts/run_backlog.py status
   cat PROGRESSO.md
   ```

3. **Dispare o Lote 2:**
   ```bash
   python scripts/run_backlog.py run --ambiente fabric
   # (Lote 2 é T02–T05, depende de T01 estar ok)
   ```

---

## Para acompanhar sem disparar nada

```bash
# Simular: ver o que seria disparado sem disparar
python scripts/run_backlog.py run --ambiente offline --dry

# Ver todas as tarefas e status
python scripts/backlog.py list

# Ver só as pendentes (liberadas)
python scripts/backlog.py next --ambiente offline

# Ver prompts de um lote específico
python scripts/backlog.py next --ambiente offline --prompts
```

---

## Se algo der errado

**Um agente falhou?**
- Log fica em `.claude/logs/lote_*.log` ou `.claude/logs/XXXXXX.log`.
- Copie o prompt: `python scripts/backlog.py show T07`
- Rode manualmente ou ajuste e tente novamente.
- Marque o status: `python scripts/backlog.py set T07 done`

**Precisa mudar uma tarefa?**
- Edite direto no [BACKLOG.md](BACKLOG.md) (coluna `Prompt`, etc.)
- O script lê tudo do zero toda vez.

**Porta 1433 bloqueada?**
- T01 vai dizer. Enquanto isso, rode só `--ambiente offline`.
- Lote 2 fica bloqueado.

---

## Status do projeto em tempo real

Veja [PROGRESSO.md](PROGRESSO.md) para:
- Qual lote está rodando agora
- Status de cada tarefa (todo/doing/done/blocked)
- Próximas etapas desbloqueadas
- Checklist para começar

---

## Resumo

| Ação | Comando |
|------|---------|
| Disparar Lote 1 agora | `python scripts/run_backlog.py run --ambiente offline` |
| Acompanhar | `cat PROGRESSO.md` ou `python scripts/run_backlog.py status` |
| Depois, disparar Lote 2 | `python scripts/run_backlog.py run --ambiente fabric` |
| Manual: ver próximo | `python scripts/backlog.py next` |
| Manual: copiar prompt | `python scripts/backlog.py show T07` |
| Manual: marcar pronto | `python scripts/backlog.py set T07 done` |

---

**Tudo está em:** [BACKLOG.md](BACKLOG.md) (tarefas) e [PROGRESSO.md](PROGRESSO.md) (dashboard).
