# Manual do backlog automatizado

Como o fluxo de tarefas do ALS OilModel funciona, como iniciar, acompanhar, parar e consertar. Os comandos rodam no PowerShell, na raiz do projeto.

## 1. Como funciona

```text
BACKLOG.md ──► run_backlog.py run ──► uma sessão `claude --bg` por tarefa ──► commit no worktree
 (fila)         (escolhe o lote)        (worktree + modelo próprios)               │
    ▲                                                                              ▼
    └──────── marca done ◄──── run_backlog.py colher ◄── merge na main ◄───────────┘
                                         ▲
                       `auto` = colher + run em loop até acabar
```

- **[BACKLOG.md](BACKLOG.md)** é a fila: 25 tarefas (T01–T25) com status, dependências, arquivos que tocam, dificuldade e prompt.
- **Lote:** `run` pega as tarefas `todo` cujas dependências estão `done` e escolhe as que não tocam nos mesmos arquivos, para rodarem em paralelo sem conflito.
- **Sessão:** cada tarefa vira uma sessão em background, num worktree próprio (`.claude/worktrees/backlog-Txx`, branch `worktree-backlog-Txx`). O agente trabalha, roda `pytest`, documenta e faz commit lá.
- **Colheita:** `colher` integra na `main` o que terminou e marca `done`. Só com `done` as tarefas dependentes são liberadas.
- **Modelo por dificuldade:** o campo `Dificuldade` da tarefa escolhe modelo, esforço e teto de gasto por sessão.

| Dificuldade | Modelo | Esforço | Teto por sessão |
|---|---|---|---|
| baixa | haiku | low | US$ 1 |
| media | sonnet | medium | US$ 3 |
| alta | opus | high | US$ 8 |

A tabela está em `ROTA`, em [scripts/run_backlog.py](scripts/run_backlog.py). `--model X` força um modelo para o lote inteiro.

## 2. Regras

1. **Aprovação automática:** as sessões rodam em `bypassPermissions`, sem pedir aprovação, e fazem commit local sozinhas. Nunca fazem push.
2. **Dados da empresa no Fabric:** ler é livre; gravar só em `Files/als_oilmodel/` e em notebooks `als_*`. Alterar ou apagar dado que já existe (tabelas, schemas, views) é bloqueado pelo hook [fabric_guard](scripts/fabric_guard.py) mesmo no modo automático. Só uma pessoa libera, com `ALS_FABRIC_ESCRITA=1`. Limite: o guard lê o texto do comando ou do arquivo, então não pega escrita montada dinamicamente; revise notebooks novos antes de publicar.
3. **Agentes não editam o BACKLOG.md.** O status só muda por `run`, `colher` ou `backlog.py set`.
4. **Regra de pronto** (vale para toda tarefa, detalhada no topo do BACKLOG.md): testes verdes, resultado registrado no doc indicado, sem TAT.
5. **Fechamento de lote:** depois que um lote termina, rode o prompt "Fechamento de lote" do BACKLOG.md (o Organizador consolida os docs 06, 12 e 13) antes do próximo.
6. **O que vai para uma pessoa:** aprovar regras de negócio (RN-02/03/04/07), responder a pauta da T23, liberar a porta 1433 ou outro workspace, e qualquer escrita em dado existente. E-mails e mensagens ficam como rascunho; nunca são enviados.

## 3. Pré-requisitos (uma vez só)

No `claude.exe` da extensão do VS Code (o `claude` não está no PATH):

```powershell
cd "C:\Users\dynatest\OneDrive - Dynatest Engenharia\Área de Trabalho\Novos_proj\als-oilmodel"
& "C:\Users\dynatest\.vscode\extensions\anthropic.claude-code-2.1.310-win32-x64\resources\native-binary\claude.exe" --dangerously-skip-permissions
```

1. Aceite o aviso de **confiança da pasta** ("Workspace not trusted").
2. Aceite o aviso do **modo sem aprovação** (disclaimer de `bypassPermissions`).
3. Saia com `/exit`.

Sem isso, os disparos falham com essas mensagens e nada fica marcado como `doing`. Se a extensão atualizar, o número da versão no caminho muda.

Antes de colher, a `main` precisa estar sem mudanças não commitadas (`git status`).

## 4. Como começar

```powershell
python scripts/run_backlog.py run --dry    # mostra o lote, o modelo e o teto de cada tarefa; não dispara nada
python scripts/run_backlog.py auto         # modo totalmente automático (recomendado)
```

Alternativa passo a passo:

```powershell
python scripts/run_backlog.py run          # dispara um lote
python scripts/run_backlog.py colher       # depois que terminarem
```

`--ambiente offline|fabric|humano` filtra por ambiente. Sem o filtro, o `auto` dispara todos. Uma tarefa `humano` só prepara material e rascunho.

## 5. Como saber se está rodando

| Pergunta | Comando |
|---|---|
| Quais sessões estão ativas e em que estado? | `claude agents` (em terminal interativo; use `claude agents --json` em script) |
| O que uma sessão está fazendo? | `claude logs <id>` |
| Quero ver ou responder dentro dela | `claude attach <id>` |
| Visão geral por bloco (regenera [PROGRESSO.md](PROGRESSO.md)) | `python scripts/run_backlog.py status` |
| Status de cada tarefa | `python scripts/backlog.py list` |
| O que está liberado agora | `python scripts/backlog.py next` |
| O que a tarefa deve fazer | `python scripts/backlog.py show T07` |
| O que o agente fez | `git log --oneline worktree-backlog-T07` |

Estados no `claude agents`:

| Estado | Significa | O que fazer |
|---|---|---|
| `busy` | trabalhando | nada |
| `idle` | terminou o turno | o `colher` integra |
| `waiting` | travada num pedido de permissão | `claude attach <id>` e aprovar, ou parar e redisparar (seção 7) |

Status da tarefa no BACKLOG: `todo` (fila), `doing` (sessão disparada), `done` (integrada na `main`), `blocked` (parada à mão). Cada disparo grava um registro em `.claude/logs/lote_*.json`.

Para guardar a saída do `auto` em arquivo: `python -u scripts/run_backlog.py auto | Tee-Object .claude\logs\auto.log`.

## 6. Como parar

| Quero | Comando |
|---|---|
| Parar o `auto` (as sessões já disparadas continuam) | `Ctrl+C` na janela dele |
| Parar uma sessão | `claude stop <id>` |
| Parar e apagar sessão, worktree e estado | `claude rm <id>` |
| Fazer a tarefa voltar para a fila | `python scripts/backlog.py set T07 todo` |

Para reiniciar tarefas travadas: `claude stop <id>`, `claude rm <id>`, `backlog.py set Txx todo` e, na `main`, `git commit -am "backlog: reinicia Txx"`. Depois rode `run` ou `auto`. O trabalho parcial do worktree é descartado.

## 7. Problemas comuns

| Sintoma | Causa e solução |
|---|---|
| `Workspace not trusted` | Faltou o passo 1 da seção 3. |
| `--bg with bypassPermissions requires accepting the disclaimer` | Faltou o passo 2 da seção 3. |
| `Nenhuma tarefa liberada` | Todas as `todo` dependem de tarefas ainda não `done` (veja `backlog.py list`), ou a que bloqueia está `doing`/`idle` sem ter sido colhida. Rode `colher`. |
| Tarefa `doing` há muito tempo | `claude agents`: se `waiting`, aprove; se não aparece e o worktree tem commit, rode `colher`; se não tem nada, reinicie (seção 6). |
| `colher`: "terminou sem nenhuma mudança" | A sessão acabou sem commit. Veja `claude logs <id>`, depois reinicie a tarefa. |
| `colher`: "main tem mudanças não commitadas" | Faça `git commit` ou `git stash` e rode de novo. |
| `colher`: "conflito de merge" | O merge foi cancelado e a tarefa continua `doing`. Resolva à mão com `git merge worktree-backlog-Txx` e depois `backlog.py set Txx done`. |
| Hook bloqueou um comando do agente | O comando mencionava Fabric com escrita (ex.: `DROP`, `saveAsTable`). É falso positivo comum em testes; reescreva ou peça a uma pessoa. |

## 8. Pelo celular

| Caminho | Serve para | Limite |
|---|---|---|
| **Controle remoto da sessão do PC** (`remoteControlAtStartup` já é `true` em `~/.claude/settings.json`; ou `claude --remote-control <nome>`) | Tudo, inclusive Fabric: a sessão roda no PC, com o login Azure em cache. Do celular você pede "rode o `auto`". | O PC precisa estar ligado com a sessão aberta. Confirme no app que ela aparece; não dá para verificar daqui. |
| **Sessão na nuvem** (`claude --cloud "<tarefa>"`, repositório GitHub `rafaelroriz-age/als-models`) | Só tarefas `offline`, sem PC ligado. | Precisa de `git push` antes (o GitHub só tem o commit inicial). Não enxerga o Fabric. |

Para o Fabric sem depender da porta 1433, a T25 cria `scripts/fabric_run.py`: executa notebooks pela API na 443, com login por device code que você completa no navegador do celular.

## 9. Arquivos

| Arquivo | Papel |
|---|---|
| [BACKLOG.md](BACKLOG.md) | Fila de tarefas e regras de pronto |
| [PROGRESSO.md](PROGRESSO.md) | Painel gerado; não edite à mão |
| [scripts/backlog.py](scripts/backlog.py) | Lê o backlog: `list`, `next`, `show`, `set` |
| [scripts/run_backlog.py](scripts/run_backlog.py) | `run`, `colher`, `auto`, `status` |
| [scripts/fabric_guard.py](scripts/fabric_guard.py) e `.claude/hooks/fabric_guard_hook.py` | Barreira de escrita no Fabric |
| `.claude/worktrees/` | Cópias isoladas das sessões (fora do git) |
| `.claude/logs/` | Registro de cada disparo |
