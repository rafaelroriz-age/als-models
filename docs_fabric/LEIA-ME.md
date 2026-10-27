# ALS / LS — Forecast de Amostras e Vendas (Azure / Microsoft Fabric)

Engajamento de ciência de dados. Índice da documentação (novo escopo, ecossistema Azure).

> **Hierarquia de fontes:** `documentacao-tecnica.md` e a transcrição da reunião de 21/10/2026 são a referência; em caso de divergência vale o mais novo. Decisões e hipóteses: [13](13_revisao_alinhamento_reuniao_2026-10-21.md).

## Documentos

| Arquivo | Conteúdo |
|---------|----------|
| [00_escopo_original.md](00_escopo_original.md) | Escopo original convertido do PDF (fiel) |
| [01_visao_geral.md](01_visao_geral.md) | Resumo do projeto e arquitetura Fabric |
| [02_glossario.md](02_glossario.md) | Termos e implicações de modelagem |
| [03_requisitos.md](03_requisitos.md) | Requisitos funcionais e não funcionais |
| [04_notas_dados.md](04_notas_dados.md) | Fontes (S360, ERP, Zoho), chaves, qualidade |
| [05_criterios_sucesso.md](05_criterios_sucesso.md) | Avaliação: snapshot, reconstrução retroativa, MAPE |
| [06_plano_execucao.md](06_plano_execucao.md) | Abordagem, ferramentas, fases, esforço |
| [07_integracao_mcp.md](07_integracao_mcp.md) | Integração do agente ao Fabric via MCP |
| [08_dicionario_de_dados.md](08_dicionario_de_dados.md) | Dicionário de dados (campos, fontes, chaves) |
| [08_dicionario_de_dados_discovery.md](08_dicionario_de_dados_discovery.md) | Schemas e colunas reais descobertos no Fabric |
| [09_conexao_e_consumo_fabric.md](09_conexao_e_consumo_fabric.md) | Conexão ao Fabric, `lh_forecast`, consumo |
| [10_estrutura_do_projeto.md](10_estrutura_do_projeto.md) | Estrutura, regras de negócio (RN), gateways, testes |
| [11_conexoes_fabric.md](11_conexoes_fabric.md) | Endpoints dos lakehouses |
| [12_plano_trabalho_esboco.md](12_plano_trabalho_esboco.md) | Plano: dados → requisitos → modelos → notebooks |
| [13_revisao_alinhamento_reuniao_2026-10-21.md](13_revisao_alinhamento_reuniao_2026-10-21.md) | Decisões, hipóteses por protótipo e descobertas por dados |
| [14_fase0_engenharia_reversa_e_base_de_codigo.md](14_fase0_engenharia_reversa_e_base_de_codigo.md) | Regras extraídas das planilhas, chaves entre fontes, base de código e como rodar |
| [15_matriz_cobertura.md](15_matriz_cobertura.md) | Matriz insumo × fonte da Etapa 1 (✅/⚠️/❌) com tabela real, granularidade e plano para cada lacuna (T04) |
| [16_decisao_modelos.md](16_decisao_modelos.md) | Modelo × critério, candidatos provisórios por problema, protocolo de avaliação e experimentos priorizados (T19) |
| [15_pauta_decisoes_time.md](15_pauta_decisoes_time.md) | Pauta para o time: 7 decisões pendentes, com opções, recomendação e quem decide (T23) |
| [../BACKLOG.md](../BACKLOG.md) | Backlog executável: 24 tarefas com prompt copiável, dependências e ordem automática; gerador de lotes paralelos (`scripts/backlog.py`) |
| [../PROGRESSO.md](../PROGRESSO.md) | Status do backlog por bloco e próximo lote; gerado por `scripts/run_backlog.py status` |
| [../CELULAR.md](../CELULAR.md) | Guia curto para rodar pelo celular: comandos prontos e prompt de fechamento de lote |
| [../AUTOMATIZACAO.md](../AUTOMATIZACAO.md) | Manual do backlog automatizado: como iniciar, acompanhar, parar e consertar; regras e barreira de escrita no Fabric |
| `documentacao-tecnica.md` | Documentação técnica de origem (Icaro Guerra) |
| `Revisando KPIs e métricas…md` | Transcrição da reunião de validação de 21/10/2026 |
| `Apresentacao_Executiva_…v2.md/.pptx`, `Plano_Executivo_…v2.pdf` | Versão anterior à reunião de 21/10 (escopo, EBIT, % Achieved e entrega desatualizados; ver 13) |

## Fatos rápidos

- **Objetivo:** previsibilidade comercial — consumo de amostras (KPI 1) e vendas/faturamento derivado (KPI 2).
- **Ecossistema:** Azure / Microsoft Fabric (lakehouse OneLake, capacidade F8).
- **Entregável:** formato definido após prototipagem (dashboard HTML + SQL, modelo semântico, API/MCP) — não um notebook.
- **Ponto de partida:** 3 planilhas (Calculadora, Customer Status, Forecast) + dicionário de dados; medallion bronze/silver já existente no `LakehouseOel`.
- **Sucesso:** MAPE por mês/segmento/cliente via snapshot mensal + reconstrução retroativa; great expectations/pytest.
- **Esforço:** ~21–30 dias (tempo integral) ou ~8–12 semanas a 4–6 h/dia.
