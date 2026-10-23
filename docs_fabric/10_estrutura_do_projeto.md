# Estrutura do Projeto: do conhecimento aos entregáveis

> Ordem de trabalho: **entender → validar → construir → empacotar**. Notebooks são só laboratório; os 4 ativos finais saem de código promovido para `src/` (ver [06](06_plano_execucao.md) e [09](09_conexao_e_consumo_fabric.md)).

## 1. Mapa: o que precisamos saber → onde fica → vira qual entregável

| # | Insumo | Onde vive (repo) | Fonte atual | Vira entregável |
|---|--------|------------------|-------------|-----------------|
| 1 | Origens de dados (schemas Fabric) | `specs/01_origens_dados.md` + [08](08_dicionario_de_dados.md) | Fase 0 (probe SQL endpoint) | Contrato de schema (G0) |
| 2 | KPIs e objetivos | `specs/02_kpis_objetivos.md` | [03](03_requisitos.md), [05](05_criterios_sucesso.md) | Metas dos modelos e do backtest |
| 3 | Regras de negócio | `specs/03_regras_negocio.md` | Calculadora, Customer Status, Forecast 27 | Funções em `src/features/` |
| 4 | Plano de testes | `specs/04_plano_testes.md` | [05](05_criterios_sucesso.md) | Suíte `tests/` (pytest) |
| 5 | Notebooks de validação | `notebooks/00_validacao/` | Fase 0 | Expectations em `src/gates/` |
| 6 | Notebooks de pré-processamento | `notebooks/10_preprocessamento/` | Fase 1 | **Entregável 1** pipeline (`src/pipeline/`) |
| 7 | Modelos | `notebooks/20_kpi1_consumo/`, `30_kpi2_vendas/` | Fases 2-3 | **Entregável 2** modelos MLflow (`src/models/`) |
| 8 | Gateways de validação | `src/gates/` | Great Expectations | Travas entre etapas (seção 3) |
| 9 | Backtest e snapshots | `notebooks/40_backtest/` | Fase 4 | **Entregável 4** (`src/backtest/`) |
| 10 | Exposição | `src/serving/` | Fase 5 | **Entregável 3** semântico + MCP |

Layout de pastas:

```
specs/        contratos e regras (fonte da verdade; sem código)
notebooks/    laboratório (00_validacao, 10_preprocessamento, 20_kpi1_consumo, 30_kpi2_vendas, 40_backtest)
src/          código promovido: pipeline/ features/ models/ gates/ backtest/ serving/
tests/        pytest (unit das regras, contrato de schema, leakage)
scripts/      fabric_probe.py (descoberta local)
```

## 2. Regras de negócio já conhecidas (para `specs/03_regras_negocio.md`)

| ID | Regra | Status |
|----|-------|--------|
| RN-01 | Intervalo de coleta: motor 250h; hidráulico e transmissão 500h; arrefecimento 1000h; preventiva vs. meia preventiva | A validar |
| RN-02 | Consumo real = horas (horímetro) × meses trabalhados/ano ÷ intervalo, por compartimento | A validar |
| RN-03 | Recorrente: compras em ≥6 meses distintos dos últimos 12 **e** última compra <90 dias (sem redutor de 70%) | A validar (item 5 do checklist) |
| RN-04 | Churn: >6 meses sem compra. Reativado: volta após >1 ano | A validar |
| RN-05 | Alerta de queda: amostras do cliente caem >20% | A validar (base de comparação a definir) |
| RN-06 | Compartimento churn: compartimento deixa de ser coletado dentro do intervalo esperado | A validar |
| RN-07 | Potencial = benchmark de similares do mesmo segmento; % Achieved = realizado ÷ potencial | **Em aberto** (item 3) |
| RN-08 | Inatividade do equipamento inferida por quebra na série do horímetro e intervalos de coleta (S360 não informa venda/parada) | A validar |
| RN-09 | Sazonalidade: Cana (parada nov-mar), MT (soja/milho/algodão), Indústria (mensal/bimestral), Locomotiva (semanal) | Parcial (item 7) |
| RN-10 | Cross-check: descontar faturado no mês (Protheus), pedidos pendentes e oportunidades ativas (Zoho) | A validar |
| RN-11 | Ticket médio R$ 1.950 e conversão 5% (out/2022) | **Defasado** (item 4) |

## 3. Gateways de validação de dados

Cada gate é um conjunto de expectations (Great Expectations) que **bloqueia** a etapa seguinte e grava o resultado em `dq_resultados`. Falha crítica interrompe o pipeline; falha de aviso só registra.

| Gate | Entre | Verifica (exemplos) | Falha =  |
|------|-------|---------------------|----------|
| G0 | Fabric → pipeline | Tabelas e colunas esperadas existem, tipos, frescor da última carga | Bloqueia |
| G1 | Bronze/Silver → limpo | Raiz CNPJ e ERP ID não nulos; ID de equipamento único; sem duplicatas de amostra; datas plausíveis; horímetro não decrescente e sem saltos absurdos | Bloqueia (chaves), aviso (outliers) |
| G2 | Limpo → features | Joins sem explosão de linhas; cobertura de cliente S360↔ERP; **sem vazamento** (toda feature usa só dados ≤ data_ref) | Bloqueia |
| G3 | Features → modelo | Treino/teste separados por tempo; modelo bate baseline (ingênuo sazonal e regra da planilha) no backtest | Bloqueia promoção |
| G4 | Modelo → saída | p10 ≤ p50 ≤ p90; sem negativos; sem NaN; cross-check não gera total negativo; contrato (entidade, data_ref, período) completo | Bloqueia publicação |
| G5 | Saída → consumo | Calibração do intervalo (cobertura ≈ declarada); CU medido na F8 dentro do orçamento | Aviso / bloqueia |

## 4. Plano de testes (resumo para `specs/04_plano_testes.md`)

- **Unitários (pytest):** cada regra RN-xx com casos de borda (ex.: exatamente 6 meses, exatamente 90 dias, queda de 20,0% vs. 20,1%).
- **Contrato:** schema das tabelas de saída e das entradas (G0, G4).
- **Leakage:** reconstruir uma data passada e provar que nenhuma feature enxerga o futuro.
- **Regressão numérica:** reproduzir a Calculadora e o Forecast 27 em amostra conhecida (dourada) com tolerância definida.
- **Backtest:** MAPE/MAE por mês, segmento e cliente desde 2022 vs. baselines; curva de convergência semanal.
- **FinOps:** CU por execução e por consulta MCP/DirectLake.

## 5. Ordem de execução

1. Fase 0: `scripts/fabric_probe.py` → preencher `specs/01_origens_dados.md` e [08](08_dicionario_de_dados.md); notebooks `00_validacao` definem os G0/G1 reais.
2. Fechar `specs/02` e `03` com Bahia/Keli (checklist do plano executivo) antes de escrever feature alguma.
3. Fases 1-3: notebook → função testada em `src/` → pipeline. Nada vai para `src/` sem teste e gate.
4. Fases 4-5: backtest, snapshots, semântico/MCP, medição de CU.

## Pendências que bloqueiam o início

- Acesso de leitura ao Bronze/Silver e nomes das tabelas (sem isso o item 1 não sai).
- Campo exato do ID de equipamento no S360.
- Origem do Annual Sample Potential e parâmetros atuais de ticket/conversão.
