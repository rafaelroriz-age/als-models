# ALS OIL & LUBRICANTS — Previsão de TAT & Volume

Engajamento freelance de ciência de dados. Índice da documentação.

## Documentos

| Arquivo | Conteúdo |
|---------|----------|
| [00_escopo_original.md](00_escopo_original.md) | Escopo original (PDF), convertido para Markdown |
| [01_visao_geral.md](01_visao_geral.md) | Resumo do projeto |
| [02_glossario.md](02_glossario.md) | Termos e implicações para a modelagem |
| [03_requisitos.md](03_requisitos.md) | Requisitos funcionais e não funcionais |
| [04_notas_dados.md](04_notas_dados.md) | Dados do S360, qualidade, censura |
| [05_criterios_sucesso.md](05_criterios_sucesso.md) | Métricas de avaliação e backtesting |
| [06_plano_execucao.md](06_plano_execucao.md) | Abordagem, ferramentas, fases, estimativa de esforço |

## Fatos rápidos

- **Entrega:** modelo de previsão autônomo (TAT/% on-time + volume) integrado ao agente existente.
- **Meta:** ≥ 90% on-time por mês (o mês é o período de referência principal).
- **Entidades:** operação inteira, laboratório, pacote, grupo de trabalho.
- **Linguagem:** Python. **Fonte de dados:** LIMS S360.
- **Sucesso:** precisão da previsão de meio de período via backtesting (MAE/MAPE, erro no % on-time, confiança calibrada, sinalização de risco).
