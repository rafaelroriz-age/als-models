# Notas de Dados (Azure / Fabric)

## Fontes e acesso

Acesso via lakehouse `LakehouseOel` no Microsoft Fabric. S360, Protheus e Zoho já estão ingeridos (`bronze_*` e `silver_*`); ver [discovery](08_dicionario_de_dados_discovery.md).

| Fonte | Conteúdo | KPI | Ingestão no Fabric |
|-------|----------|-----|--------------------|
| LIMS / S360 | amostras processadas, equipamentos cadastrados/monitorados, compartimentos, setor, segmento | Consumo | Já ingerido (bronze/silver) |
| ERP / Protheus | faturamento e vendas | Vendas | Já ingerido (bronze/silver) |
| Zoho CRM | segmentação, oportunidades, pedidos em aberto | Vendas (cross-check) | Já ingerido (bronze/silver) |

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
  - faturamento/vendas (ERP/Protheus).
- As planilhas servem como **referência de lógica** e baseline, não como fonte de treino.

## Estrutura de referência (planilhas existentes)

| Arquivo | O que faz | Campos principais |
|---------|-----------|-------------------|
| Calculadora de amostras (Bahia, out/2022) | amostras/ano por tipo de equipamento | segmento, tipo de equipamento, horas trabalhadas, meses/ano, ponto de coleta, período de coleta, total de coletas, amostras/ano e /mês, ticket médio, conversão |
| Customer Status 2026 | base de clientes (2.388; 1.479 ativos; 233 recorrentes), um por linha | Raiz CNPJ, ERP ID, Sales Reps, Sector, Segment, Last Date Sales/Sample, vendas e amostras por período, Annual Sample Potential, % Achieved, equipamentos testados, Faturamento 12 meses |
| Forecast (Keli/Diego) | receita mensal estimada por componente | Receita Recorrente, Não Recorrente Ativa, Novos, Reativados, Churn, Receita Total, Variáveis de Mercado, Novo Total, Projeção por Amostra |

## Qualidade esperada e tratamento

- Registros reais: valores ausentes, outliers, erros de digitação.
- O campo **Annual Sample Potential** aparece colado no Customer Status; a origem será descoberta por engenharia reversa das planilhas, artefatos e dados.
- Parâmetros (ticket médio, conversão) são de out/2022 — **defasados**.
- Validação de dados como parte da metodologia: **great expectations** e **pytest** nos notebooks.
- Sem feedback automático do S360 (máquina vendida/parada/trocou de área) — inferir pelo histórico do equipamento.
- **Horímetro (confirmado):** uma leitura por coleta (`horas_oleo`, `horimetro_equipado` em `amostra`), não uma série contínua. `silver_s360` é orientada a TAT e não traz `equipamento` nem `compartimento` (só a bronze).
- Qualidade do S360 (reunião de 21/10): amostras avulsas sem equipamento (identificar e limpar no pré-processamento); equipamentos cadastrados já inativos (engenharia reversa); clientes que superdeclaram frota; frota de alguns grandes clientes em sistema externo.

## Plano de descoberta de dados

1. Schemas e tabelas já listados no [discovery](08_dicionario_de_dados_discovery.md); validar conteúdo, frescor e cobertura.
2. Mapear as tabelas de faturamento (Protheus) e de oportunidades (Zoho) já ingeridas.
3. Validar as chaves de ligação (CNPJ, ERP ID, ID de equipamento, setor/segmento) campo a campo. **Feito em 2026-10-27 (T03)**, resultados em [14](14_fase0_engenharia_reversa_e_base_de_codigo.md) §2: Protheus ↔ S360 casa 40,1% (50,5% com a regra de grupo `A`+5 dígitos), a cadeia amostra → equipamento fecha em 97,7%, e só 44,8% do faturamento tem cliente S360.
4. Traçar o ciclo de vida do equipamento → compartimento → amostra → faturamento.
5. Mapear as camadas medallion **já existentes** (`bronze_*` e `silver_*` de protheus, s360 e zoho no `LakehouseOel`) e desenhar apenas as tabelas fato/dimensão de saída do Forecast.
6. Gerar relatório de qualidade (missingness, outliers, sanidade de timestamps e horímetro).

## Resultado do perfil de qualidade (T02, 2026-10-27)

Perfil executado contra o SQL endpoint do LakehouseOel (somente leitura); tabelas completas e gates propostos em [08](08_dicionario_de_dados_discovery.md#perfil-de-qualidade-das-tabelas-chave-t02-2026-10-27). Resumo:

- **Volume:** `amostra` 8,66 mi linhas (6,2 mi com `data_coleta` válida 2015–2026-10), `cliente` 10,2 mil, `equipamento` 1,06 mi, `compartimento` 3,48 mi, `notassaida` 58,7 mil (2024-08 → 2026-10), `contasreceber` 58,5 mil (desde 2018-11), Zoho `accounts` 9,8 mil e `deals` 22,2 mil (desde 2026-01).
- **Qualidade:** `data_coleta` 25,81% nula e com valores impossíveis (ano 0001, 1969, 2115); 150 `amostra.id` duplicados; 1.652 itens duplicados em `notassaida`; horímetro com 85 negativos, P99 de 618 mil h e 21 mil valores > 1 mi h; `accounts.id_protheus` 100% nulo.
- **Impacto:** KPI 1 depende de definir a data de referência da amostra e a regra de deduplicação; KPI 2 tem só 27 meses de faturamento e out/2026 parcial.
- **G0:** 22/27 checagens passam; as 5 falhas são achados reais (listados em 08). Pendente decidir limiares e validar casamento de chaves (T03).
