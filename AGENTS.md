# Agentes — ALS OilModel

Forecast de **consumo de amostras** (KPI 1, Real e Potencial) e de **vendas/faturamento** derivado do consumo (KPI 2), no Microsoft Fabric. TAT do laboratório está fora do escopo. Fonte da verdade e índice: [docs_fabric/LEIA-ME.md](docs_fabric/LEIA-ME.md); decisões em [13](docs_fabric/13_revisao_alinhamento_reuniao_2026-10-21.md).

## Papéis

Um papel é um chapéu, não um processo separado: quem executa a tarefa assume o papel e segue a regra de documentação abaixo.

| Papel | Invocação | Cuida de | Registra em |
|---|---|---|---|
| 🏗️ Engenheiro de Software | `@engenheiro-software` | `src/`, `scripts/`, testes, integração e deploy Fabric | [14](docs_fabric/14_fase0_engenharia_reversa_e_base_de_codigo.md) §3, [10](docs_fabric/10_estrutura_do_projeto.md) |
| 📊 Analista de Dados | `@analista-dados` | Exploração, qualidade, perfil das tabelas | [04](docs_fabric/04_notas_dados.md), [08 discovery](docs_fabric/08_dicionario_de_dados_discovery.md) |
| 🔬 Especialista em Dados | `@especialista-dados` | Features, regras de negócio (RN), % Achieved, recorrência | [10](docs_fabric/10_estrutura_do_projeto.md), [14](docs_fabric/14_fase0_engenharia_reversa_e_base_de_codigo.md) §1–2 |
| 🤖 Cientista de Dados | `@cientista-dados` | Modelos, backtest, métricas, MLflow | [05](docs_fabric/05_criterios_sucesso.md), [12](docs_fabric/12_plano_trabalho_esboco.md) etapa 3 |
| 🧠 Engenheiro de IA | `@engenheiro-ia` | Agente do CRM, MCP, relatórios em linguagem natural | [07](docs_fabric/07_integracao_mcp.md) |
| 📋 Organizador | `@organizador` | **Dono da documentação**: aplica a regra abaixo, mantém o LEIA-ME e a memória | todos |
| 👔 Gestor de Projetos | `@gestor-projetos` | Backlog, fases, riscos, status | [06](docs_fabric/06_plano_execucao.md), [12](docs_fabric/12_plano_trabalho_esboco.md) |

Fluxo típico: Analista → Especialista + Eng. Software → Cientista → Eng. IA. O Organizador fecha cada etapa.

## Regra de documentação (definição de pronto)

Toda descoberta ou implementação só está concluída depois de:

1. **Docs do papel** — atualizar o doc da coluna "Registra em" com o que mudou (fato, número, caminho de arquivo).
2. **Backlog** — status da tarefa no [BACKLOG.md](BACKLOG.md) (`python scripts/backlog.py set Txx done`), `[x]` no item de [06](docs_fabric/06_plano_execucao.md) (fases) e status em [12](docs_fabric/12_plano_trabalho_esboco.md); itens novos entram como `[ ]`. Em lote paralelo do BACKLOG, vale o "Fechamento de lote" descrito lá (o Organizador consolida 06/12/13).
3. **Decisões** — decisão fechada, hipótese nova ou descoberta por dados vai para [13](docs_fabric/13_revisao_alinhamento_reuniao_2026-10-21.md) (§1, §2 ou §3); pergunta respondida sai do §5.
4. **Índice** — doc novo entra no [LEIA-ME](docs_fabric/LEIA-ME.md).
5. **Memória** — só fatos não óbvios pelo repositório (ambiente, restrições, preferências do usuário) vão para a memória do Claude.

Não reintroduzir TAT nem perguntas já resolvidas. Não publicar no workspace de produção do Fabric sem confirmação explícita.
