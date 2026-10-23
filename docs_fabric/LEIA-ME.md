# ALS / LS — Forecast de Amostras e Vendas (Azure / Microsoft Fabric)

Engajamento de ciência de dados. Índice da documentação (novo escopo, ecossistema Azure).

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

## Fatos rápidos

- **Objetivo:** previsibilidade comercial — consumo de amostras (KPI 1) e vendas/faturamento derivado (KPI 2).
- **Ecossistema:** Azure / Microsoft Fabric (lakehouse OneLake, capacidade F8).
- **Entregável:** modelo semântico do Fabric (DirectLake) e/ou API/endpoint — não um notebook.
- **Ponto de partida:** 3 planilhas (Calculadora, Customer Status, Forecast) + dicionário de dados.
- **Sucesso:** MAPE por mês/segmento/cliente via snapshot mensal + reconstrução retroativa; great expectations/pytest.
- **Esforço:** ~21–30 dias (tempo integral) ou ~8–12 semanas a 4–6 h/dia.
