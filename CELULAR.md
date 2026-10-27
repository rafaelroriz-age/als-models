# Rodar pelo celular

Guia curto. O manual completo está em [AUTOMATIZACAO.md](AUTOMATIZACAO.md) (seção 8).

## Antes de sair do PC

1. O PC precisa estar ligado, sem hibernar, com a sessão do Claude Code aberta na pasta `als-oilmodel`.
2. Confirme que a sessão aparece no app do celular (Claude, aba Code).
3. O GitHub só tem a versão enviada por `git push`. Se faltou push, o celular não vê os commits novos. Peça ao PC: "faça push da `main`" (só com sua confirmação).

## Comandos para colar na sessão

| O que quer | Cole isto |
|---|---|
| Ver o que está pronto | `python scripts/backlog.py list` |
| Ver o prompt de uma tarefa | `python scripts/backlog.py show T07` |
| Ver o painel | `python scripts/run_backlog.py status` |
| Ver como vai o lote | `claude agents` |
| Rodar tudo sozinho | `python scripts/run_backlog.py auto` |
| Fechar um lote | o prompt abaixo |

## Prompt de fechamento de lote

Rode depois de cada lote, antes do próximo:

```text
Atue como @organizador (AGENTS.md). Rode `git status` e `git log` para ver o que o último lote mudou. Para cada tarefa concluída: marque o item correspondente em docs_fabric/06_plano_execucao.md, atualize o status em docs_fabric/12_plano_trabalho_esboco.md, mova decisões, hipóteses e descobertas novas para docs_fabric/13_revisao_alinhamento_reuniao_2026-10-21.md (§1 a §3, e tire do §5 o que foi respondido), e inclua docs novos no docs_fabric/LEIA-ME.md. Confira se BACKLOG.md reflete os status reais (`python scripts/backlog.py list`). Não altere código.
```

## Limites

- **Fabric:** publicar no workspace de produção só com sua confirmação explícita. Escrita em dado existente é bloqueada pelo `fabric_guard`.
- **Porta 1433:** tarefas do Fabric por SQL só funcionam na rede certa. Fora dela, use só as tarefas `offline`.
- **Push:** o agente nunca faz push sozinho.
