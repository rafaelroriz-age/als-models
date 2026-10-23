# Notas de Dados (Azure / Fabric)

## Fontes e acesso

Acesso via **lakehouse no Microsoft Fabric**. O espelhamento do LIMS/S360 é simples (botão nativo do Fabric); ERP (Proteus) e Zoho já estão disponíveis.

| Fonte | Conteúdo | KPI | Ingestão no Fabric |
|-------|----------|-----|--------------------|
| LIMS / S360 | amostras processadas, equipamentos cadastrados/monitorados, compartimentos, setor, segmento | Consumo | Espelhamento (mirroring) |
| ERP / Proteus | faturamento e vendas (API em tempo real) | Vendas | Conector / pipeline / API |
| Zoho CRM | segmentação, oportunidades, pedidos em aberto | Vendas (cross-check) | Conector / pipeline |

## Chaves de ligação

| Chave | Liga | Observação |
|-------|------|------------|
| Raiz CNPJ | todas as fontes | identificador do cliente |
| ERP ID | ERP ↔ base de clientes | código do cliente no ERP |
| ID de equipamento (S360) | S360 ↔ calculadora | campo exato a confirmar |
| Setor / Segmento | dimensões comuns | agregação |

> Dicionário de campos completo (campo a campo, tipo, origem, status) — ver [08_dicionario_de_dados.md](08_dicionario_de_dados.md).

## Dados brutos x agregados

- As planilhas (Calculadora, Customer Status, Forecast) têm **agregados** — carregam a regra de negócio, mas não servem para treinar.
- O modelo precisa do **histórico cru**:
  - amostras processadas (LIMS/S360);
  - detalhe de equipamento/horímetro (S360);
  - faturamento/vendas (ERP/Proteus).
- As planilhas servem como **referência de lógica** e baseline, não como fonte de treino.

## Estrutura de referência (planilhas existentes)

| Arquivo | O que faz | Campos principais |
|---------|-----------|-------------------|
| Calculadora de amostras (Bahia, out/2022) | amostras/ano por tipo de equipamento | segmento, tipo de equipamento, horas trabalhadas, meses/ano, ponto de coleta, período de coleta, total de coletas, amostras/ano e /mês, ticket médio, conversão |
| Customer Status 2026 | base de clientes (2.388; 1.479 ativos; 233 recorrentes), um por linha | Raiz CNPJ, ERP ID, Sales Reps, Sector, Segment, Last Date Sales/Sample, vendas e amostras por período, Annual Sample Potential, % Achieved, equipamentos testados, Faturamento 12 meses |
| Forecast (Keli/Diego) | receita mensal estimada por componente | Receita Recorrente, Não Recorrente Ativa, Novos, Reativados, Churn, Receita Total, Variáveis de Mercado, Novo Total, Projeção por Amostra |

## Qualidade esperada e tratamento

- Registros reais: valores ausentes, outliers, erros de digitação.
- O campo **Annual Sample Potential** aparece colado (sem fórmula) — origem a confirmar.
- Parâmetros (ticket médio, conversão) são de out/2022 — **defasados**.
- Validação de dados como parte da metodologia: **great expectations** e **pytest** nos notebooks.
- Sem feedback automático do S360 (máquina vendida/parada/trocou de área) — inferir pelo histórico do equipamento.

## Plano de descoberta de dados

1. Confirmar o espelhamento do S360 no lakehouse e listar schemas/tabelas.
2. Confirmar conectores do ERP (Proteus) e Zoho; mapear tabelas de faturamento e oportunidades.
3. Validar as chaves de ligação (CNPJ, ERP ID, ID de equipamento, setor/segmento) campo a campo.
4. Traçar o ciclo de vida do equipamento → compartimento → amostra → faturamento.
5. Desenhar a arquitetura medallion (bronze/silver/gold) e as tabelas fato/dimensão.
6. Gerar relatório de qualidade (missingness, outliers, sanidade de timestamps e horímetro).
