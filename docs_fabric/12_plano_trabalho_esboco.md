# Plano de Trabalho (esboço): dados → requisitos → modelos → notebooks

> Esboço para enriquecer depois. Sequência: **1 Cobertura de dados → 2 Requisitos → 3 Revisão técnica de modelos → 4 Notebooks de teste**. As etapas 1 e 2 rodam em paralelo; a 3 usa o que elas descobrirem; a 4 só começa com a 1 liberada. Complementa [10](10_estrutura_do_projeto.md) e [06](06_plano_execucao.md).

## Estado atual

- O probe foi refeito com sucesso: o `LakehouseOel` expõe `bronze_`/`silver_` de protheus, s360 e zoho, mais `s360._public` ([08 discovery](08_dicionario_de_dados_discovery.md), `fabric_probe_results.json`).
- O medallion já existe. Novas camadas só se o escopo exigir no futuro.
- Lakehouses conhecidos ([11](11_conexoes_fabric.md)): `LakehouseOel`, `Ontology_OeL_lh_…`, `s360`. Protheus e Zoho estão no `LakehouseOel`.
- Ponto de partida adicional: [Dicionario_de_Dados_Projeto_Ciencia_de_Dados.xlsx](Dicionario_de_Dados_Projeto_Ciencia_de_Dados.xlsx).
- Decisões, hipóteses e descobertas: ver [13](13_revisao_alinhamento_reuniao_2026-10-21.md).
- Status em 27/10/2026: Fase 0 com base de código pronta ([14](14_fase0_engenharia_reversa_e_base_de_codigo.md)). Na etapa 4, já existem `00_validacao/01_perfil_qualidade` (cobertura e perfil; aguarda porta 1433), `00_validacao/02_engenharia_reversa_planilhas` e `40_backtest/01_backtest_baselines`; os baselines de KPI 1 e 2 estão em `src/models/baselines.py`. Backlog por fase em [06](06_plano_execucao.md).

---

## Etapa 1 — As tabelas disponíveis cobrem os dados que os KPIs precisam?

**Pergunta:** para cada KPI, cada insumo existe, com granularidade, histórico e qualidade suficientes?

**Método:** matriz *insumo × fonte* (checklist de cobertura), preenchida com o resultado do probe.

| Insumo necessário | KPI | Fonte esperada | Verificar |
|---|---|---|---|
| Amostras (data, cliente, equipamento, compartimento, status) | 1 e 2 | S360 | Chaves, histórico desde 2022, duplicatas |
| ID do equipamento | 1 | S360 | Campo exato a descobrir pelos dados (candidato `equipamento_id`) |
| Horímetro (uma leitura por coleta: `horas_oleo`, `horimetro_equipado`) | 1 | S360 (`amostra`) | Monotonicidade por equipamento, lacunas, outliers |
| Compartimento e intervalo de coleta (250/500/1000h) | 1 | S360 + regra | Está na base ou só na planilha? |
| Cliente / raiz CNPJ ↔ ERP ID | 1 e 2 | S360 ↔ Protheus | Taxa de casamento do join |
| Faturamento (valor, data, item) | 2 | Protheus | Granularidade, vínculo com amostra |
| Pedidos pendentes | 2 | Protheus | Existe? Frescor |
| Oportunidades abertas | 2 | Zoho CRM | Estágio, valor, cliente |
| Segmento do cliente (Cana, MT, Indústria, Locomotiva) | 1 e 2 | S360/Zoho | Preenchimento |
| Annual Sample Potential | 1 (visão Potencial) | **Origem a descobrir** (RN-07) | Planilhas, artefatos e dados |
| Ticket médio e conversão atuais | 2 | **Defasado** (RN-11) | Recalcular a partir do faturamento |
| Calendário / sazonalidade | 1 e 2 | Derivado | Meses parados por segmento |

**Saídas:**
- `specs/01_origens_dados.md`: tabela, colunas, chave, volume, período, frescor.
- Matriz de cobertura com status por linha: ✅ existe / ⚠️ parcial / ❌ falta / ❓ não verificado.
- Lista de lacunas com dono e plano (pedir ao time de dados, derivar, ou aceitar a limitação).
- Perfil de qualidade por tabela-chave: nulos, duplicatas, datas fora do intervalo, cobertura de join. Isso vira o rascunho de G0/G1.

**Critério de saída:** todo insumo da matriz está ✅ ou ⚠️ com decisão registrada. Nenhum ❓.

**A enriquecer:** volume mínimo de histórico por segmento; tratamento de clientes novos sem histórico; fontes externas (clima, safra) como candidatas.

---

## Etapa 2 — Levantar e validar requisitos

**Levantar** (partir de [03](03_requisitos.md), [05](05_criterios_sucesso.md), Calculadora, Customer Status, Forecast 27):

- Funcionais: granularidade (Cliente → Equipamento → Compartimento), períodos (semana/mês), visões Real e Potencial, alertas (queda >20%, compartimento churn), composição da receita (Recorrente, Não Recorrente Ativa, Churn, Mercado; Novos e Reativados fora do escopo por ora), cross-check mensal.
- Não funcionais: frequência de refresh (semanal/mensal), orçamento de CU na F8, latência de consulta, auditabilidade (snapshots), explicabilidade.
- Métricas de sucesso: meta de acurácia por KPI (MAPE/MAE), baseline a superar, cobertura do intervalo de confiança.

**Validar** (regras RN-01…RN-17 de [10](10_estrutura_do_projeto.md); primeiro por descoberta nas planilhas, artefatos e dados, depois com o negócio apenas o que os dados não resolverem):

| Item a validar | Com quem | Como |
|---|---|---|
| RN-03/04 (recorrente, churn) | Bahia / Keli | Aplicar a regra a clientes conhecidos e pedir confirmação do enquadramento |
| RN-05/06 (alertas) | Negócio | Definir a base de comparação da queda de 20% |
| RN-07 (potencial) | Negócio + dados | Decidir a origem do Annual Sample Potential |
| RN-11 (ticket, conversão) | Financeiro | Recalcular com faturamento atual |
| RN-01/02 (intervalos e consumo) | Operação | Reproduzir a Calculadora v8 em amostra conhecida |

**Saídas:** `specs/02_kpis_objetivos.md`, `specs/03_regras_negocio.md` (cada regra com dono, status e exemplo numérico), `specs/04_plano_testes.md`, registro de decisões e pendências.

**Critério de saída:** regras críticas (RN-02, 03, 04, 07) aprovadas por escrito pelo negócio. As demais podem ficar como hipótese documentada.

**A enriquecer:** tratamento de equipamentos sem horímetro; quem aprova mudanças de regra.

---

## Etapa 3 — Revisão técnica para escolha de modelos preditivos

**Natureza dos problemas:**

| Problema | Alvo | Característica | Risco principal |
|---|---|---|---|
| KPI 1 real | Amostras por equipamento/compartimento/mês | Determinístico em boa parte (horas ÷ intervalo), com ruído de operação | Horímetro ausente ou com lacunas |
| KPI 1 potencial | Amostras de clientes similares | Benchmark por segmento | Definição de "similar" |
| KPI 2 | Receita por tipo de cliente | Série esparsa, com churn e reativação | Poucos eventos por cliente |
| Alertas | Queda >20%, compartimento churn | Regra/classificação | Falso positivo |

**Candidatos por família (a comparar, não decididos):**

1. **Baselines (obrigatórios):** ingênuo sazonal; regra da Calculadora/Forecast 27; média móvel por segmento. Todo modelo precisa bater esses (gate G3).
2. **Estatísticos de série temporal:** ETS/Theta e SARIMA (statsmodels, statsforecast). Bons em séries longas e sazonais; baratos em CU.
3. **Séries esparsas/intermitentes:** Croston, SBA, TSB. Prováveis para compartimento e equipamento com poucas coletas.
4. **Hierárquicos:** reconciliação Cliente → Equipamento → Compartimento (MinT/bottom-up), para que os níveis somem de forma coerente.
   - *T13 (offline, implementado):* `src/models/hierarquia.py` com bottom-up, top-down por proporções históricas (janela opcional; cliente sem volume divide igualmente) e agregação por tipo de equipamento, setor e segmento; `tests/test_hierarquia.py` prova que os níveis somam e que segmento = soma dos clientes (`python -m pytest`: 35 passed). MinT fica como extensão documentada na docstring do módulo, não implementada (exige previsões em todos os níveis, de T10/T11, e covariância dos erros).
5. **ML tabular global:** LightGBM/XGBoost com features de lag, sazonalidade e segmento; regressão quantílica para p10/p50/p90. Costuma ser o melhor custo-benefício para muitas séries curtas.
   - *T11 (offline, implementado):* `src/models/ml_global.py` → `ml_global(treino, h, p=ParametrosML())`, mesma interface dos baselines; devolve `yhat` = p50, `yhat_lo` = p10, `yhat_hi` = p90. Um `LGBMRegressor(objective="quantile")` por quantil, treinado em todas as séries juntas, estratégia direta empilhada (linha = mês t × horizonte k, features de T07 do mês t, alvo y(t+k−1), só alvos ≤ origem; previsão com as features de origem+1). Features: `lag_1/2/3/12`, `mm_3/12`, `tendencia_6`, seno/cosseno do mês alvo, `horizonte` e `segmento` (categórica); `status` (RN-03/RN-04) desligado por padrão (`ParametrosML.series`). Lags, médias e alvo divididos por uma escala da linha (mm_12 → mm_3 → lag_1) para o modelo ser global entre clientes de tamanhos diferentes. Quantis ordenados por linha (sem cruzamento) e cortados em 0. Extra opcional `ml` no `pyproject.toml` (`lightgbm>=4.0`; testado com 4.7.0).
   - *Hiperparâmetros iniciais (sem tuning):* `n_estimators=300`, `learning_rate=0.05`, `num_leaves=15`, `min_child_samples=20`, `subsample=0.8` (`subsample_freq=1`), `colsample_bytree=0.8`, `reg_lambda=1.0`, `random_state=42`, `n_jobs=1`. Tuning só em origens de validação, nunca nas de teste (protocolo abaixo).
   - *Resultado em dados sintéticos* (séries sazonais de 48 meses, metade Poisson e metade com ruído de 15%; origens 2024-12, 2025-03 e 2025-06; h=3): 30 séries → WAPE 0,117 (ingênuo sazonal 0,134; média móvel 3 0,263), cobertura p10–p90 0,72; 300 séries → WAPE 0,114 (0,138; 0,275), cobertura 0,77 (nominal 0,80: leve subcobertura, a recalibrar com dados reais, ex.: conformal).
   - *Custo (proxy tempo × 1 núcleo, notebook local, `n_jobs=1`):* um ajuste (3 quantis) com 30 séries / 3,6 mil linhas ≈ 2,8 s; com 300 séries / 36 mil linhas ≈ 14 s, dos quais ≈ 6 s são as features de T07 (`tendencia` via `rolling.apply`). Backtest de 3 origens × 300 séries ≈ 46 s. Custo em CU na F8 fica para T22.
   - *Testes:* `tests/test_ml_global.py` (ordem dos quantis, cobertura entre 0,6 e 0,95 e WAPE abaixo da média móvel, treino só até a origem, e alterar valores após a origem não muda a previsão); `python -m pytest`: 104 passed.
   - *Achado para T15:* `resumir` do harness calcula `cobertura` = 0 para modelos sem intervalo quando são resumidos junto com um modelo que tem `yhat_lo/yhat_hi` (NaN vira "fora"); ler a cobertura só dos modelos com intervalo.
6. **Probabilístico/híbrido:** modelo de vida útil (horas até a próxima coleta) combinado com previsão de uso do horímetro; e modelo de sobrevivência para churn/reativação.
7. **Classificação e detecção de mudança de regime (proposta do Rafael, 21/10):** classificar clientes antes de prever (árvores/floresta) e detectar mudança de ponto em séries de receita (changepoint, ex.: PELT). Modelo de sobrevivência/vida útil para frota inativa por segmento.
8. **Deep learning (N-BEATS, TFT, foundation models como Chronos/TimesFM):** só como experimento, se os candidatos acima não baterem as metas. Maior custo e menor explicabilidade.

**Critérios de comparação:** acurácia no backtest (MAPE/MAE/WAPE por nível e segmento), calibração do intervalo, desempenho em série curta e esparsa, explicabilidade para o negócio, custo em CU (F8), facilidade de operar em MLflow/Fabric, robustez a dado faltante.

**Saídas:** documento de decisão com tabela *modelo × critério*, uma recomendação por problema (KPI 1 real, potencial, KPI 2, alertas) e lista de experimentos priorizados.

**Critério de saída:** 2–3 candidatos por problema escolhidos, mais os baselines, com protocolo de avaliação fechado (ver abaixo).

**A enriquecer:** biblioteca por candidato; custo estimado por execução; quantidade mínima de histórico para cada família.

**Implementação dos estatísticos (T10):** `src/models/estatisticos.py` (`ets`, `theta`, `croston`, `sba`, `tsb`, dict `MODELOS`), mesma assinatura dos baselines (`f(treino, h) -> [id, periodo, yhat]`) e usados direto em `rolling_origin`. Testes: `tests/test_estatisticos.py` (séries sintéticas sazonal, intermitente e curta; `python -m pytest`: 35 passed).

| Modelo | Biblioteca | Histórico mínimo (`min_obs`) | Observações |
|---|---|---|---|
| ETS | statsmodels `ExponentialSmoothing` (aditivo, tendência amortecida; sazonal m=12 só com ≥ 24 meses) | 8 | |
| Theta | statsmodels `ThetaModel` (dessazonaliza com ≥ 24 meses) | 8 | |
| Croston, SBA, TSB | numpy puro (α=0,1; β=0,1 no TSB) | 3 | sem dependência extra |

- **Dependências:** extra opcional `stats` no `pyproject.toml` (`statsmodels>=0.14`, `scipy`); `pip install -e .[stats]`. Testado com statsmodels 0.14.6. `statsforecast` não foi adotado (puxa numba; statsmodels basta e já roda no Fabric).
- **Fallback:** série com menos de `min_obs` meses, ajuste que levanta exceção ou previsão não finita → média dos últimos 3 meses (mesma regra da `media_movel`), sem erro. Previsões são truncadas em 0.
- **Custo observado** (máquina local, 200 séries sintéticas de 36 meses, h=3, 1 núcleo): ETS 78,7 s (~0,4 s/série), Theta 7,5 s (~0,04 s/série), Croston 0,8 s, SBA 0,6 s, TSB 0,7 s. Extrapolação linear: ETS em ~10 mil séries ≈ 1 h por origem do backtest; para esse volume paralelizar por `id` ou restringir ETS aos níveis agregados. Medição sintética, a repetir com dados reais (G3).

**Protocolo de avaliação (a fixar aqui, usado na etapa 4):**
- Backtest com origem móvel (*rolling origin*), sem embaralhar o tempo.
- Horizontes: 1, 3 e 6 meses (a confirmar).
- Métricas: WAPE/MAE por nível, viés, cobertura do intervalo.
- Dados de teste nunca entram em ajuste de hiperparâmetro.

---

## Etapa 4 — Começo dos notebooks de teste dos modelos

Pré-requisito: etapa 1 liberada para os dados que o notebook usa. Notebooks são laboratório; só o que passa em teste vai para `src/`.

| Notebook | Conteúdo | Depende de |
|---|---|---|
| `00_validacao/00_cobertura_tabelas` | Roda a matriz da etapa 1 sobre os dados reais e gera o perfil de qualidade | Acesso ao Fabric |
| `00_validacao/01_gates_g0_g1` | Rascunho das expectations (Great Expectations) | Etapa 1 |
| `10_preprocessamento/10_base_amostras` | Limpeza, joins S360 × Protheus × Zoho, tabela-base por entidade e mês | Etapas 1 e 2 |
| `10_preprocessamento/11_features` | Lags, sazonalidade, segmento, status de cliente; teste de vazamento | Regras RN aprovadas |
| `20_kpi1_consumo/20_baselines` | Ingênuo sazonal e regra da Calculadora, reproduzindo a planilha | Etapa 2 |
| `20_kpi1_consumo/21_modelos_estatisticos` | ETS/Theta/Croston por nível | Etapa 3 |
| `20_kpi1_consumo/22_modelo_ml_global` | LightGBM com quantis | Etapa 3 |
| `30_kpi2_vendas/30_baselines` | Reprodução do Forecast 27 | Etapa 2 |
| `30_kpi2_vendas/31_modelos` | Modelos por composição de receita (recorrente, novos, churn…) | Etapa 3 |
| `40_backtest/40_avaliacao_comum` | Harness único de backtest: mesma função para todos os modelos | Protocolo da etapa 3 |

**Convenções:** um notebook por pergunta; parâmetros no topo; funções reutilizáveis já nascem como módulos (`src/`) com teste; resultados de cada experimento registrados em MLflow com versão dos dados.

**Ordem sugerida do primeiro ciclo:** `00_cobertura_tabelas` → `20_baselines` e `30_baselines` (provam que entendemos as regras) → `40_avaliacao_comum` → primeiros modelos.

**Critério de saída:** harness de backtest funcionando e baselines reproduzindo as planilhas dentro da tolerância definida. A partir daí, os modelos candidatos entram em ciclos de comparação.

---

## Dependências e riscos

```
Acesso Fabric ──► Etapa 1 ─────────────┐
                                     ├──► Etapa 4
Reuniões Bahia/Keli ──► Etapa 2 ─────┤
                                     │
Etapa 1 + 2 ──► Etapa 3 ─────────────┘
```

| Risco | Impacto | Mitigação |
|---|---|---|
| Horímetro ausente ou irregular | KPI 1 real perde a base determinística | Estimar uso por intervalo entre coletas; marcar confiança |
| Annual Sample Potential sem origem | Visão Potencial bloqueada | Derivar de benchmark por segmento; decidir com o negócio |
| Regras não aprovadas a tempo | Retrabalho de features | Implementar por parâmetro; congelar só após aprovação |
| Histórico curto por cliente/equipamento | Modelos individuais instáveis | Modelo global + hierárquico |
| Custo de CU acima do orçamento F8 | Inviabiliza a produção | Medir CU desde os primeiros experimentos |
| Amostras avulsas sem equipamento; frota em sistema externo; frota superdeclarada | KPI 1 subestima ou superestima o potencial desses clientes | Identificar e limpar avulsas no pré-processamento; medir cobertura por cliente |
| Equipamentos cadastrados já inativos | Potencial superestimado | Engenharia reversa: coluna de ativo, intervalos entre coletas, vida útil por família |

## Pontos em aberto para a próxima rodada

- Metas numéricas de acurácia por KPI.
- Horizontes de previsão e frequência de atualização por KPI.
- Hierarquia matriz/filial do Zoho utilizável para agrupar clientes.
- Janela de CU livre na F8.
