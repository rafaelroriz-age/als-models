# Plano de Execução

> Abordagem proposta, ferramentas e estimativa de esforço para o Forecast de Amostras e Vendas, no ecossistema Azure (Microsoft Fabric).

## Abordagem proposta (resumo)

Dois modelos encadeados, atrás de uma camada de dados medallion no lakehouse:

1. **Consumo de amostras** — previsão de volume por cliente/equipamento/compartimento, a partir de horas trabalhadas (horímetro), meses/ano e intervalos de coleta, com sazonalidade por segmento. Entrega as visões **Real** e **Potencial**.
2. **Vendas** — previsão de **faturamento** e de **EBIT** (targets separados), **derivada do consumo**. Componentes da fase 1: recorrente, não recorrente ativa, churn e variável de mercado, com cross-check Zoho. Novos e reativados ficam fora do escopo por ora.
   - Hipóteses testadas por protótipo: (a) oportunidades >80% somam ou só descontam; (b) receita como venda de kit ou como análise processada (ver [13](13_revisao_alinhamento_reuniao_2026-10-21.md)).

Ambos com **intervalos de incerteza**, validados por **snapshot mensal + reconstrução retroativa**, e entregues por **protótipos comparáveis** (dashboard HTML + SQL, modelo semântico, API/MCP) para o cliente escolher.

## Arquitetura no Fabric

```
S360 (espelhado) ─┐
ERP/Protheus ───────┼─► Lakehouse OneLake ─► Bronze ─► Silver ─► Gold ─► Modelo (MLflow) ─► Modelo Semântico / API
Zoho CRM ──────────┘    (Delta)              (bruto)   (limpo)   (fato/dim)                    (Power BI / agente)
```

## Ferramentas / bibliotecas

| Preocupação | Escolha | Por quê |
|-------------|---------|---------|
| Ingestão | Já existente (bronze/silver) | reuso; sem nova ingestão |
| Armazenamento | OneLake Lakehouse (tabelas Delta) | camada única, DirectLake |
| Arquitetura | Medallion já existente (bronze, silver) | novas camadas só se o escopo exigir |
| Transformação | Spark (PySpark) + SQL (analytics endpoint) | joins faturamento × amostras no pré-processamento |
| Séries temporais (consumo/vendas) | `statsforecast` / `prophet` / `scikit-learn` + `XGBoost`/`LightGBM` | ML clássico de menor custo (FinOps) |
| Sazonalidade/features | pandas, numpy, `holidays` (feriados BR) | sazonalidade por segmento |
| Rastreamento/registro | MLflow (nativo no Fabric) | experimentos e registro de modelos |
| Validação de dados | Great Expectations + pytest | parte da metodologia |
| Entrega | Protótipos: dashboard HTML + SQL, modelo semântico (DirectLake), API/MCP | o cliente escolhe após comparação |
| Orquestração | Data pipelines do Fabric (agendamento) | automação |

## Fases e tarefas

### Fase 0 — Descoberta e auditoria de dados (antes de comprometer)
- [x] Probe: S360, Protheus e Zoho acessíveis no `LakehouseOel` (ver discovery).
- [x] Mapear schemas/tabelas ([08 discovery](08_dicionario_de_dados_discovery.md)).
- [x] Validar chaves (CNPJ, ERP ID, ID equipamento, setor/segmento): medidas em 27/10 (T03) em [14](14_fase0_engenharia_reversa_e_base_de_codigo.md) §2. Protheus ↔ S360 casa 50,5% com a regra de grupo (pendente de confirmação pelo time de dados, [13](13_revisao_alinhamento_reuniao_2026-10-21.md) §5); cadeia amostra → equipamento 97,7%.
- [x] Revisar as 3 planilhas + dicionário de dados; regras extraídas em [14](14_fase0_engenharia_reversa_e_base_de_codigo.md) §1.
- [ ] Relatório de qualidade (missingness, outliers, sanidade de horímetro/timestamps): código pronto (`notebooks/00_validacao/01_perfil_qualidade.py`), bloqueado pela porta 1433.
- [x] Base de código inicial (`src/`, baselines, harness de backtest, gates, 24 testes).
- **Saída:** mapa de dados + perguntas resolvidas.

### Fase 1 — Pipeline de pré-processamento (sobre Bronze/Silver existentes)
- Medallion já existe: **não** recriar ingestão nem alterar a Gold do agente atual.
- Criar `lh_forecast` com shortcuts somente leitura para Bronze/Silver (ver [09](09_conexao_e_consumo_fabric.md)).
- Limpeza complementar, joins em SQL (faturamento × amostras) e tabelas de features; Great Expectations + pytest.

### Fase 1b — Classificação de clientes (proposta do Rafael, a validar)
- Classificar clientes (recorrente, não recorrente ativo, menor atividade etc.) antes da previsão, em série temporal, para dar manutenibilidade ao modelo. Critério a definir a partir dos dados (pirâmide faturamento × nº de máquinas × potencial).
- Modelo de vida útil/abandono de equipamento por período e segmento, para filtrar cadastrados inativos. **27/10 (T05):** regra proposta de equipamento ativo (flag = 1 + coleta nos últimos 12 meses), que deixa 85,9% do cadastro inativo; vida útil por família não melhora o corte ([13](13_revisao_alinhamento_reuniao_2026-10-21.md) §3, R3). Modelo ainda não implementado.

### Fase 2 — KPI 1: consumo de amostras
- Features: horímetro, meses/ano, intervalo de coleta, tipo de equipamento, segmento, sazonalidade.
- Modelo de volume por cliente/equipamento/compartimento (Real).
- Modelo de **Potencial** via benchmark de clientes similares e % achieved. **27/10 (T05):** o potencial atual é valor colado sem fonte nos dados; a base proposta é frota ativa × taxa anual da família, a calibrar pelo benchmark (T16). Fórmula original segue com o Bahia.
- Sinais de ação: queda >20%, compartimento churn.

### Fase 3 — KPI 2: vendas (faturamento)
- Quantificar a correlação consumo→venda (projeção por amostra).
- Modelar componentes (recorrente, não recorrente ativa, churn; novos e reativados fora do escopo por ora).
- [x] Cross-check Zoho (evitar dupla contagem): **T18 (27/10)** — 4 variantes no Forecast 27 (só base, soma opportunities >80%, desconta escopo, desconta parcial); código + testes prontos; execução em dados reais interrompida por falta de memória ([13](13_revisao_alinhamento_reuniao_2026-10-21.md) §2, H1).
- Forecast semanal + mensal de faturamento e de EBIT (targets separados).

### Fase 4 — Validação (snapshot + reconstrução retroativa)
- Snapshot mensal do forecast × realizado.
- Reconstrução retroativa sobre o histórico do Fabric (linha de base).
- MAPE por mês/segmento/cliente; convergência ao longo do mês.
- Great Expectations / pytest nos pipelines.

### Fase 5 — Entrega e handoff
- [x] Protótipos de entrega: **T20 (27/10)** — dashboard HTML estático com dados sintéticos (Real/Potencial, p10–p90, % Achieved, filtros por segmento/mês/período, tabela por cliente/equipamento, alertas); `src/serving/dashboard.template.html` e exemplo em `exemplo/dashboard_sintetico.html`. SQL da saída não executado. Alternativas (b) semântico e (c) API/MCP em aberto ([13](13_revisao_alinhamento_reuniao_2026-10-21.md) §2, H3). Pipeline agendada pendente da escolha do cliente.
- [x] Comparativo das opções de entrega: **T21 (27/10)** — quadro (a) HTML + SQL × (b) semântico × (c) API/MCP em [13](13_revisao_alinhamento_reuniao_2026-10-21.md) §2 (H3). Recomendação: (b) como entrega principal sobre `als_*` da Gold, (a) só como retrato provisório, (c) na fase do agente do CRM. Escolha final é do cliente (7 perguntas no 13).
- [ ] Medir CU e latência de consulta do semântico/SQL com as tabelas reais da T15/T16 (a T22 mediu só o custo de treino/previsão dos modelos).
- [x] FinOps: custo × acurácia dos modelos escolhidos (T22, proxy tempo × vCores; detalhe abaixo; refazer com a métrica de capacidade na F8).
- Documentação de premissas/limitações e handoff.

#### FinOps: custo × acurácia por modelo (T22, 27/10/2026)

**Método.** `scripts/finops_modelos.py` lê só `base/base_cliente_mes.parquet` (T14, local, sem tocar o Fabric) e roda o KPI 1 no nível cliente: 1.996 clientes com consumo nos últimos 12 meses, série mensal de 2015-01 a 2026-08, h = 3, 3 origens móveis. Cada modelo roda em 400 séries (recorte determinístico por hash do id) com 1 núcleo; o custo é extrapolado linearmente para as 1.996 séries. O `ml_global` foi medido também com 800 séries: 0,0485 vs 0,0468 s por série-origem, então a escala é linear. Resultado bruto em `<dados>/finops/custos.json`.

**Métrica usada: proxy, não a de capacidade do Fabric.** Não houve acesso ao Capacity Metrics App nesta execução. Proxy = tempo de parede × vCores; CU-s = vCore-s ÷ 2 (1 CU = 2 vCores no Spark do Fabric). Para um notebook Python de 2 vCores (mínimo), CU-s ≈ segundos de parede. Premissas a confirmar com a métrica real na F8: (a) a CPU local (12 lógicas, Python 3.14) é parecida com a do nó do Fabric; (b) o notebook Python de 2 vCores fatura 1 CU. O número vale como ordem de grandeza.

| Modelo | s/série-origem | CU-s por origem (1.996 séries) | CU-s backtest 12 origens | WAPE (recorte 400, h 1–3, 3 origens) | Viés | Cobertura p10–p90 |
|---|---|---|---|---|---|---|
| ingenuo_sazonal | 0,0034 | 7 | 82 | 0,516 | −9,6% | n/a |
| media_movel_3 | 0,0024 | 5 | 57 | 0,347 | −15,3% | n/a |
| media_movel_12 | 0,0020 | 4 | 49 | 0,410 | −15,9% | n/a |
| ETS | 0,312 | 622 | 7.470 | 0,350 | −5,1% | n/a |
| Theta | 0,026 | 52 | 623 | 0,334 | −6,6% | n/a |
| Croston | 0,0019 | 4 | 45 | 0,498 | −23,8% | n/a |
| SBA | 0,0019 | 4 | 46 | 0,515 | −27,6% | n/a |
| TSB | 0,0021 | 4 | 50 | 0,452 | −22,7% | n/a |
| ML global (LightGBM, 3 quantis) | 0,048 | 97 | 1.161 | 0,329 | −13,0% | 0,82 |

Leitura custo × acurácia (WAPE do recorte, só para ordenar; os números oficiais por nível e segmento são da T15/T19):
- A `media_movel_3` já fica em 0,347 por ~5 CU-s por origem. Theta (0,334) e ML global (0,329) ganham 4–5% relativos de WAPE e custam 10× e 20× mais, ainda baratos em termos absolutos (1–2 min).
- ETS (0,350) custa 6× o Theta e não bate a média móvel de 3 meses nem o Theta neste recorte: é o modelo mais caro e sem ganho; candidato a sair, ou a rodar só em níveis agregados.
- Croston/SBA/TSB são quase de graça mas perdem para a média móvel nos clientes (WAPE 0,45–0,52); só fazem sentido no nível de compartimento/equipamento esparso (fora desta medição).
- O ML global é o único com intervalo (cobertura 0,82 vs 0,80 nominal) e o melhor WAPE; entrega a incerteza que os outros não dão.

**Execução completa.** Carga + grade mensal 17,8 s; gate G1 0,14 s; backtest de todos os 9 modelos em 400 séries × 3 origens: 462,6 s (ETS = 81%); comparação + G3: 0,25 s. O script inteiro, com as medições individuais, levou 1.075 s (≈ 18 min). Extrapolando para as 1.996 séries:

| Cenário (nível cliente, 1 núcleo) | Tempo ≈ CU-s (2 vCores) |
|---|---|
| Forecast de produção: 1 origem, todos os modelos | ≈ 797 s (13 min) |
| Forecast de produção: 1 origem, sem ETS | ≈ 175 s (3 min) |
| Forecast de produção só com Theta + ML global + média móvel 3 | ≈ 154 s (2,6 min) |
| Backtest completo (12 origens), todos os modelos | ≈ 9.560 s (2 h 40 min; ETS ≈ 2 h 04) |
| Backtest completo (12 origens), sem ETS | ≈ 2.100 s (35 min) |

**Janela estimada para o agendamento na F8.** Mensal, após o fechamento do mês e a atualização da tabela-base (T14, ≈ 20 s sobre o parquet; a leitura do SQL endpoint não foi medida aqui): reservar 15–20 min de notebook Python de 2 vCores para o forecast dos 3 níveis agregados de cliente com Theta + ML global + baseline (≈ 3 min medidos + folga para equipamento/compartimento, hoje fora da medição), ou ≈ 30 min se o ETS ficar. Isso é ≈ 150–1.000 CU-s por execução mensal, trivial perto de uma capacidade F2 (2 CU = 7.200 CU-s por hora). O backtest de revalidação (12 origens) é trimestral ou sob demanda: ≈ 35 min sem ETS, fora do horário de pico, para não disputar CU com relatórios.

**Limites.** (1) Só nível cliente: equipamento e compartimento têm ordens de grandeza a mais de séries (T15 usa amostra mod 100) e vão multiplicar o custo, em especial o ETS, que deve ficar fora desses níveis (paralelizar por `id` ou usar Theta/ML global). (2) WAPE do recorte de 400 séries oscila com a amostra (ML global 0,329 com 400 séries e 0,383 com 800): serve para o custo × acurácia relativo, não como resultado de T15. (3) Proxy local, a refazer com o Capacity Metrics App (ou `notebookutils`/Monitoring hub) numa execução real no Fabric. (4) O custo do MLflow, da gravação de tabelas e do SQL endpoint não entrou.


## Estimativa de esforço

| Fase | Tempo integral (dias) | 4–6 h/dia (dias úteis) |
|------|----------------------|------------------------|
| Fase 0 — Descoberta/auditoria | 3–4 | 6–8 |
| Fase 1 — Engenharia de dados | 4–6 | 8–12 |
| Fase 2 — KPI 1 consumo | 4–6 | 8–12 |
| Fase 3 — KPI 2 vendas | 4–6 | 8–12 |
| Fase 4 — Validação | 3–4 | 6–8 |
| Fase 5 — Entrega/handoff | 3–4 | 6–8 |
| **Total** | **~21–30 dias** | **~42–60 dias úteis (~8–12 semanas)** |

**Nota:** a estimativa não inclui a Fase 1b nem a prototipagem comparativa de entregáveis; revisar o prazo.

**Premissas:**
- Acesso ao lakehouse (S360 espelhado, ERP, Zoho) liberado no início.
- Histórico de amostras desde 2022 e faturamento disponíveis; ≥ 12 meses para backtesting.
- Dicionário de dados entregue; chave de equipamento confirmada.
- Capacidade F8 disponível sem competir com o agente.
- Entrega por protótipos comparáveis; a escolha do cliente define o escopo final.

**Riscos que elevam o prazo:**
- Descoberta de dados difícil (sem dicionário, chaves ambíguas, horímetro sujo).
- Histórico fino ou sazonalidade mal documentada por segmento.
- Entrega exigir API real-time em vez de semântico.
- FinOps: necessidade de otimizar/reduzir modelo por custo.

## Hipóteses e descobertas

Em vez de perguntas ao cliente, o que estava em aberto virou **hipótese a testar por protótipo** (H1–H4) ou **descoberta por dados** (R1–R7). Ver [13](13_revisao_alinhamento_reuniao_2026-10-21.md).

Ainda sem resposta: meta de MAPE, cadência semanal obrigatória, hierarquia matriz/filial do Zoho e janela de CU na F8.

**Teste pré-existente falhando (não vem da T22):** `python -m pytest` → 177 passed, 1 failed (`tests/test_comparacao.py::test_g3_oraculo_bate_baselines_e_tem_cobertura`): `tabela_comparativa` devolve `cobertura` = 0 (não NaN) para modelos sem intervalo quando o oráculo tem `yhat_lo/yhat_hi`, o mesmo achado de `resumir` registrado em [12](12_plano_trabalho_esboco.md) (T11). Ao ler a cobertura, usar só o `ml_global`. Correção fica para o dono do `harness`/`comparacao` (T15/T19).
