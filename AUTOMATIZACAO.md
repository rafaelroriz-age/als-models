# Rodar o backlog de forma automatizada (PC e celular)

## Pré-requisito único (uma vez)

Sessões em background só iniciam em pastas confiáveis. Abra `claude` na raiz do projeto, aceite o aviso "Workspace not trusted" e saia. Sem isso, `run_backlog.py run` falha com essa mensagem.

## Comandos

| Quero | Comando |
|---|---|
| Ver o que seria disparado | `python scripts/run_backlog.py run --ambiente offline --dry` |
| Disparar o lote (uma sessão `--bg` por tarefa, cada uma em worktree próprio) | `python scripts/run_backlog.py run --ambiente offline` |
| Ver onde estamos (regenera o [PROGRESSO.md](PROGRESSO.md)) | `python scripts/run_backlog.py status` |
| Integrar o que terminou (commit no worktree se faltar, merge na main, marca `done`, encerra a sessão) | `python scripts/run_backlog.py colher` (`--dry` para simular) |
| Tudo automático: colher + disparar o próximo lote, em loop até acabar | `python scripts/run_backlog.py auto --ambiente offline` |

**Roteamento de modelos:** o campo `Dificuldade` de cada tarefa no BACKLOG define modelo, esforço e teto de gasto por sessão: `baixa` → haiku/low/US$1, `media` → sonnet/medium/US$3, `alta` → opus/high/US$8 (tabela `ROTA` em `scripts/run_backlog.py`; `--model` força um modelo para o lote).

**Aprovação automática:** as sessões rodam com `--permission-mode bypassPermissions`, sem pedir aprovação. A proteção que continua valendo é o hook `fabric_guard` (PreToolUse), que bloqueia alteração de dados existentes no Fabric mesmo nesse modo, e o isolamento em worktree. O `colher` exige a main sem mudanças não commitadas; conflito de merge fora de BACKLOG/PROGRESSO aborta o merge e deixa a tarefa `doing` para resolução manual.
| Acompanhar / entrar / parar uma sessão | `claude agents`, `claude logs <id>`, `claude attach <id>`, `claude stop <id>` |
| Marcar status à mão | `python scripts/backlog.py set T07 done` |

O `run` marca cada tarefa disparada como `doing`. Ao fim do lote: confira os commits nos worktrees, marque `done` o que passou, rode o "Fechamento de lote" do [BACKLOG.md](BACKLOG.md) e repita.

## Pelo celular

| Caminho | Serve para | Limite |
|---|---|---|
| **Controle remoto da sessão do PC** (`remoteControlAtStartup` já está `true` em `~/.claude/settings.json`; ou `claude --remote-control <nome>`) | Tudo, inclusive Fabric: a sessão roda no PC, com o login Azure em cache. Do celular você diz "rode o lote offline" e ela executa `run_backlog.py`. | O PC precisa estar ligado e com a sessão aberta. Confirme no app que a sessão aparece; isso não dá para verificar daqui. |
| **Sessão na nuvem** (`claude --cloud "<tarefa>"`, a partir do repositório GitHub `rafaelroriz-age/als-models`) | Só tarefas `offline` (bloco B), sem PC ligado. | Precisa de `git push` antes (hoje só existe o commit inicial; nada do que foi feito está no GitHub). Não enxerga o Fabric: o login é interativo e não há credencial na nuvem. |

Para o Fabric sem depender da rede (porta 1433 bloqueada), a T25 cria `scripts/fabric_run.py`: executa notebooks pela API na 443 e aceita login por device code, que você completa no navegador do celular quando o cache expirar.

## O que vai para você

Só o que depende de pessoas: aprovar regras de negócio (RN-02/03/04/07), responder a pauta da T23, liberar a porta 1433 ou a publicação em outro workspace, e qualquer escrita em dados existentes (`ALS_FABRIC_ESCRITA=1`). O resto o Claude executa; para e-mail e mensagens, deixa rascunho.

## Segurança no Fabric

Ler é livre; gravar só em `Files/als_oilmodel/` e em notebooks `als_*`. A barreira [scripts/fabric_guard.py](scripts/fabric_guard.py) roda como hook antes de cada edição ou comando e dentro do `fabric_deploy.py`, e bloqueia DML/DDL, `saveAsTable`/`insertInto`, operações Delta de escrita e gravação em `Tables/`. Limite: ela lê o texto do comando ou do arquivo escrito, então não pega escrita construída dinamicamente. Por isso o preâmbulo dos agentes repete a regra, e vale revisar notebooks novos antes de publicar.
