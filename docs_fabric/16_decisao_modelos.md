# 16 · Decisão de modelos (T19)

Fecha a Etapa 3 de [12](12_plano_trabalho_esboco.md): critérios, candidatos por problema, protocolo de avaliação e experimentos seguintes. Escopo: KPI 1 (real e potencial), KPI 2 (faturamento e EBIT separados, D2) e alertas. TAT fora do escopo.

## 0. Status da evidência (leia primeiro)

Esta decisão foi escrita em 27/10/2026 com o que o repositório sustenta. O que existe e o que não existe:

| Insumo | Estado | Consequência |
|---|---|---|
| T15, backtest do KPI 1 em dados reais | Código pronto (`notebooks/20_kpi1_consumo/20_series_kpi1.py`, `src/backtest/comparacao.py` com `tabela_comparativa`, `avaliar_g3`, `resumo_g3`). **Nenhuma tabela modelo × nível × segmento com WAPE, viés e cobertura está registrada** nos docs, e `data/` e `mlruns/` não existem neste checkout | Não há ranking em dados reais. Nenhum candidato "bate os baselines" por dado real |
| T17, KPI 2 | `src/features/receita.py` e testes prontos; doc 13 H2 diz "falta rodar a correlação e o backtest do Forecast 27"; EBIT sem fonte na tabela-base | Não há erro do Forecast 27 reproduzido nem modelo de KPI 2 avaliado |
| T16, potencial | Código pronto (`src/models/potencial.py`); distribuição de % Achieved e sensibilidade não estão nos docs consultados | Escolha de "similar" continua por critério, não por medição |
| T10/T11, T13 | Resultados **sintéticos** e de custo local em [12](12_plano_trabalho_esboco.md) | São a única evidência numérica de acurácia/custo; valem como indício, não como decisão |

**Regra deste documento:** as escolhas abaixo são **provisórias** e se baseiam em propriedades do problema e em testes sintéticos. Cada uma traz o critério numérico que a confirma ou derruba (§3). Quando a tabela do G3 em dados reais existir, a coluna "Evidência real" da §1 é preenchida e as escolhas são revistas; nada aqui deve ser citado como "o modelo X vence".

## 1. Modelo × critério

Legenda: ✅ sustentado por teste/medição citado; 🔶 só sintético ou só por desenho do método; ❓ sem evidência ainda.

| Modelo | Acurácia por nível e segmento | Calibração do intervalo | Série curta/esparsa | Explicabilidade | Custo em CU | Operação no Fabric |
|---|---|---|---|---|---|---|
| **Baselines** (ingênuo sazonal, média móvel 3/12, regra Calculadora/Forecast 27) | ❓ real. 🔶 sintético: ingênuo sazonal WAPE 0,134–0,138; média móvel 3 de 0,263–0,275 | Sem intervalo | Média móvel é estável; ingênuo sazonal exige ≥12 meses | ✅ total | ✅ desprezível (pandas) | ✅ já no harness |
| **ETS** (statsmodels) | ❓ real | Sem intervalo no wrapper atual (só `yhat`) | Fallback p/ média 3m abaixo de 8 obs; sazonal só com ≥24 meses | ✅ alta (nível, tendência, sazonalidade) | 🔶 ~0,4 s/série (sintético, 1 núcleo); ~1 h por origem em ~10 mil séries | ✅ roda no Fabric (statsmodels); paralelizar por `id` |
| **Theta** | ❓ real | Sem intervalo | Fallback abaixo de 8 obs | ✅ alta | 🔶 ~0,04 s/série (10× mais barato que ETS) | ✅ |
| **Croston / SBA / TSB** | ❓ real | Sem intervalo | 🔶 desenhados p/ demanda intermitente; mín. 3 obs | ✅ alta | ✅ ~0,004 s/série (numpy) | ✅ sem dependência extra |
| **Hierárquico** (bottom-up / top-down, `hierarquia.py`) | ❓ real | n/a | Top-down ajuda série curta por herdar proporção | ✅ alta | ✅ desprezível | ✅ |
| **LightGBM global com quantis** (`ml_global.py`) | ❓ real. 🔶 sintético: WAPE 0,114–0,117 contra 0,134–0,138 do ingênuo sazonal | 🔶 cobertura p10–p90 0,72–0,77 (nominal 0,80): leve subcobertura | 🔶 modelo global compartilha dados entre séries; sem teste em série esparsa real | 🔶 média (importância de features; sem decomposição simples) | 🔶 ~14 s por ajuste com 300 séries/36 mil linhas; backtest de 3 origens ≈ 46 s (local, 1 núcleo) | ✅ extra `ml`; MLflow via `registrar_mlflow_tabela` |
| **Probabilístico/sobrevivência, changepoint** | ❓ | ❓ | Desenhado p/ eventos raros | 🔶 média | ❓ | ❓ não implementado |
| **Deep learning / foundation models** | ❓ | ❓ | ❓ | ✅ baixa (por desenho) | ❓ maior (por desenho) | ❓ não implementado |

Pontos não medidos que a tabela não pode preencher: acurácia por nível (cliente/equipamento/compartimento) e por segmento em dados reais, calibração em dados reais, custo em CU real (T22 mede; o proxy atual é tempo × 1 núcleo local) e robustez a dado faltante.

O teste `tests/test_comparacao.py::test_g3_oraculo_bate_baselines_e_tem_cobertura` foi **corrigido na T29 (28/10/2026)**.
- **Causa:** `rolling_origin` empilha as previsões de todos os modelos num só DataFrame. Como o oráculo tem `yhat_lo/yhat_hi`, as colunas também existem nas linhas dos baselines, com NaN. `resumir` então passa o intervalo para `metricas`, e `(y >= NaN) & (y <= NaN)` dá `False`: a cobertura de um modelo sem intervalo saía 0 em vez de NaN.
- **Correção:** em `src/backtest/harness.py::metricas`, a cobertura só conta as linhas com `yhat_lo` e `yhat_hi` preenchidos e fica NaN quando não há nenhuma.

Achado de método (de [12](12_plano_trabalho_esboco.md)): `resumir` calculava cobertura = 0 para modelo sem intervalo quando resumido junto com modelo que tem `yhat_lo/yhat_hi`. Resolvido na T29 (ver acima).

## 2. Candidatos por problema (além dos baselines)

Escolha provisória, com o motivo e o que ainda falta provar.

### KPI 1 real (amostras por cliente / equipamento / compartimento)
1. **LightGBM global com quantis (p10/p50/p90).** Motivo: único candidato com intervalo nativo e com ganho sobre o ingênuo sazonal nos testes sintéticos; modelo global é a mitigação prevista para histórico curto (risco em [12](12_plano_trabalho_esboco.md)). Falta: ganho em dados reais e recalibrar a subcobertura (ex.: conformal).
2. **Theta** (níveis cliente e equipamento). Motivo: custo ~10× menor que ETS e estatístico simples; serve de segundo nível de comparação barato. Falta: WAPE real.
3. **TSB** (nível compartimento e equipamentos esparsos). Motivo: família desenhada para demanda intermitente, e o compartimento é o nível mais esparso (5,5 mi linhas esparsas na T14). Falta: confirmar a esparsidade por nível e que bate a média móvel.
- **ETS** fica como reserva: só entra se o Theta mostrar espaço, pelo custo (~1 h por origem em ~10 mil séries).
- **Reconciliação bottom-up/top-down** é camada sobre qualquer escolha acima para os níveis somarem; MinT não está implementado.

### KPI 1 potencial
O problema é benchmark, não série temporal. Candidatos:
1. **Benchmark por similares** (`src/models/potencial.py`, segmento × porte × tipo). É a definição adotada (D6, D10, RN-07).
2. **Frota ativa × taxa anual da família**, proposta da T05 (doc 13 §3). Ela mede que a regra "flag + coleta em 12 meses" deixa 85,9% do cadastro inativo; a taxa por família só vale sobre a frota ativa assim definida.
3. **Modelo supervisionado de taxa por cliente** (LightGBM sobre atributos de frota/segmento), só como experimento se (1) e (2) divergirem muito.
Falta: distribuição do % Achieved por segmento e sensibilidade a "similar" (pedidas na T16, não registradas). A decisão final do critério é do negócio (Bahia).

### KPI 2 (faturamento e EBIT, targets separados)
1. **Forecast 27 reproduzido** (`componentes_forecast27`): é o baseline obrigatório; ainda sem erro medido.
2. **Decomposição recorrente + não recorrente ativo + churn** com previsão por componente (D3, D5): recorrente por média/ETS/Theta, não recorrente por TSB/Croston (compras esparsas), churn por taxa histórica (`churn_mensal`).
3. **Receita = amostras previstas (KPI 1) × R$/amostra** por tipo (kit vs análise, `receita_por_amostra`), só se a correlação defasada consumo × receita for significativa. Hoje só se sabe que apenas 1.315 de 7.424 entidades têm amostras e faturamento (doc 13 H2) e que x933, x949 e x102 somam R$ 83,1, 55,1 e 31,4 mi; a correlação **não foi rodada**.
EBIT não tem fonte na tabela-base: sem avaliação possível até haver fonte.

### Alertas (queda >20%, compartimento churn)
1. **Regra** (RN-05 e RN-06, `src/features/alertas.py`): é o ponto de partida e já existe.
2. **Regra com limiar calibrado pela previsão** (alerta quando o realizado cai abaixo do p10 do LightGBM): só depois de o intervalo estar calibrado.
3. **Classificador/sobrevivência** (vida útil por segmento, proposta de 21/10) só se a taxa de falso positivo da regra for alta; essa taxa **não foi medida**. A base de comparação da RN-05 segue decisão pendente com o negócio.

## 3. Protocolo de avaliação fechado

Consolida o rascunho de [12](12_plano_trabalho_esboco.md) com o que o harness já implementa (`rolling_origin`, `metricas`, `tabela_comparativa`, `avaliar_g3`).

1. **Origem móvel** sem embaralhar o tempo. O treino de cada origem só usa linhas até a origem (teste de vazamento em `tests/test_ml_global.py`).
2. **Horizontes 1, 3 e 6 meses** (os da T15; confirmação com o negócio e atualização/frequência por KPI seguem em aberto, doc 12).
3. **Níveis:** cliente (todas as entidades), equipamento e compartimento (amostra determinística `equipamento_id % ALS_AMOSTRA_MOD == 0`, mesma nos dois níveis). A conclusão do nível equipamento/compartimento vale para a amostra, e isso deve constar em todo resultado.
4. **Segmentos:** os do Customer Status, mais `sem_segmento` e a linha `TODOS`.
5. **Métricas:** WAPE (primária), viés (`bias_pct`), MAE, sMAPE e cobertura p10–p90 (só modelos com intervalo). MAPE secundário (ignora y=0, enganoso em série esparsa).
6. **Gate G3:** candidato passa em um recorte se WAPE < melhor baseline (ingênuo sazonal, média móvel 3, média móvel 12) no mesmo recorte; passa no nível se vencer em todos os horizontes no recorte `TODOS` (`resumo_g3.passa_g3`). Um candidato só é recomendado para um nível se passar G3 e **também** não piorar o viés absoluto em mais que o do baseline.
7. **Calibração:** cobertura aceitável = 0,80 ± 0,05 por nível; fora disso, recalibrar (conformal) antes de usar o intervalo. O ± 0,05 é critério proposto aqui, ainda a validar com o negócio (metas de acurácia seguem em aberto no doc 12).
8. **Hiperparâmetros:** tuning só em origens de validação anteriores às de teste, nunca nas de teste.
9. **Ativos:** conjunto de ids avaliados fixado por `ids_ativos` na primeira origem (consumo > 0 nos 12 meses anteriores), para não vazar o futuro.
10. **Registro:** um run MLflow por nível × modelo × horizonte (`registrar_mlflow_tabela`), com `versao_dados` (hash de `versao_dados()`) e snapshots em `Files/als_oilmodel/` ou `data/` (T12), nunca sobre tabelas existentes.
11. **KPI 2:** mesmo esqueleto (rolling origin por corte), erro de faturamento e de EBIT reportados separados (D2), novos e reativados fora do realizado em escopo (D3).
12. **Custo:** reportar tempo e, quando houver acesso, CU por modelo (T22); sem acesso, tempo × núcleos dizendo que é proxy.

## 4. Próximos experimentos (prioridade)

| # | Experimento | Por que nessa ordem | Critério de sucesso |
|---|---|---|---|
| 1 | **Rodar T15 em dados reais e registrar a tabela do G3** (baselines + Theta + TSB + LightGBM, 3 níveis, 3 horizontes) | Sem isso nada acima sai de "provisório"; destrava T20, T22 e a revisão deste doc | Tabela publicada em [12](12_plano_trabalho_esboco.md) e nos runs MLflow |
| 2 | **Calibrar o intervalo do LightGBM** (conformal sobre origens de validação) | Cobertura sintética já abaixo do nominal (0,72–0,77 vs 0,80) | Cobertura real em 0,80 ± 0,05 |
| 3 | **KPI 2: rodar correlação defasada consumo × receita e o erro do Forecast 27** (notebook 30_kpi2_vendas) | Define se a receita é derivada do consumo (H2) ou modelada direto | Correlação por lag e erro do baseline registrados; escolha entre candidatos 2 e 3 do KPI 2 |
| 4 | **Medir CU por candidato** (T22) e fixar a janela da F8 | Custo é critério do doc 12 sem medida real; ETS é o mais caro | Custo × acurácia por modelo |
| 5 | **Potencial: registrar % Achieved por segmento e sensibilidade a "similar"** (T16) e levar ao negócio | Critério de "similar" é decisão do negócio | Decisão registrada em [13](13_revisao_alinhamento_reuniao_2026-10-21.md) |
| 6 | **Medir falso positivo das regras RN-05/RN-06** no histórico | Só se justifica classificador de alertas com falso positivo alto | Taxa de falso positivo por regra |
| 7 | **Cross-check Zoho >80% (T18)** somando vs descontando no erro do KPI 2 | Decide H1 | Erro das duas variantes |
| 8 | Reconciliação MinT e changepoint de receita (PELT) | Só após 1 e 3, se os níveis não somarem bem ou houver mudança de regime | Ganho de WAPE sobre bottom-up |
| 9 | Deep learning / foundation models | Só se os candidatos acima não baterem as metas (metas numéricas ainda em aberto) | Ganho que justifique custo e perda de explicabilidade |

## 5. Pendências que bloqueiam o fechamento

- Tabela do G3 em dados reais (experimento 1); este doc deve ser revisado quando existir.
- Metas numéricas de acurácia por KPI (doc 12, pontos em aberto): sem elas "bate o baseline" é o único critério.
- Fonte do EBIT (D2) e confirmação da origem de `receita_valor`.
- Janela de CU da F8.

## 6. Saídas reais do KPI 1 (T29, 28/10/2026)

Esta seção implementa os modelos escolhidos na §2 para gerar `data/forecast/` no contrato da T28 (`src/serving/contrato.py`).

### Código

**Notebooks em `notebooks/20_kpi1_consumo/`**
- `23_potencial.py`: calcula o potencial por benchmark de similares e o % Achieved (D6). Grava em `data/potencial/` os arquivos `potencial_cliente`, `potencial_linhas`, `equipamentos_ativos`, `distribuicao_segmento` e `sensibilidade` (parquet) e um `relatorio.json`.
- `24_saidas_forecast.py`: gera as quatro saídas do contrato.
  - Forecast Real com o LightGBM global com quantis (§2), nos níveis cliente e equipamento.
  - Nível segmento: p50 = soma dos p50 dos clientes (bottom-up). A largura relativa do intervalo vem de um LightGBM direto nas séries de segmento.
  - Potencial lido da 23, mais % Achieved, alertas e um holdout contra os baselines.
  - Valida cada saída com `contrato.validar` e grava `data/forecast/{forecast_consumo,pct_achieved,alertas,backtest_metricas}.parquet` e um `relatorio.json` com contagens, cobertura e tempos.
  - Variáveis de ambiente (padrão entre parênteses): `ALS_PASTA_DADOS`, `ALS_MOD_TREINO` (50), `ALS_AMOSTRA_MOD` (100), `ALS_N_JOBS` (4), `ALS_LOTE` (20000).

**Módulos**
- `src/serving/saidas.py` (novo): monta cada saída no contrato (`forecast_consumo`, `segmento_bottom_up`, `pct_achieved`, `alertas_queda`, `alertas_churn`, `backtest_metricas`) e tem `grade_mensal`, que completa os meses de forma vetorizada. Testes em `tests/test_saidas.py` (7).
- `src/models/ml_global.py`: `treinar` e `prever` agora são funções separadas, para treinar numa amostra e prever toda a frota em lotes. `ml_global` dá o mesmo resultado de antes. Teste novo em `tests/test_ml_global.py`.
- `src/models/potencial.py`: novos `benchmark(..., ref=)`, `benchmark_bootstrap` e `potencial_intervalo`.
  - `potencial_p10/p90` = percentis 10 e 90 do potencial recalculado em 200 reamostras dos clientes do benchmark. Medem a incerteza de ter poucos similares no grupo.
  - O valor central fica sempre dentro da faixa.
- `src/backtest/comparacao.py::rotular_segmento`: agora tira o ponto final e trata `--` como `sem_segmento`. Antes, `Consumer products.` (1.661 linhas) contava como um segmento à parte de `Consumer products`, e `--` (1.076 linhas) virava um segmento próprio.

**Testes:** `python -m pytest` deu **265 passed, 2 skipped** (28/10/2026).

### Escolhas e limitações (dados locais da T14)

- **Corte e horizonte.** O último mês fechado é 2026-09, então `data_corte` = 2026-10-01. O horizonte é de 6 meses (2026-10 a 2027-03).
- **Séries previstas.** Só as ativas, isto é, com consumo nos 12 meses até o corte (`ids_ativos`).
- **Frota e família.** A tabela-base não tem a família do equipamento nem a flag `ativo`.
  - A frota é a dos equipamentos com coleta nos últimos 12 meses (regra da T05, sem a flag).
  - Todos ficam na família `todas`, então "similar" vira, na prática, segmento × porte.
  - Se existir `data/potencial/bruto/equipamento_familia.parquet` [equipamento_id, familia], a 23 usa a família.
- **Churn (RN-06) com proxy de calendário.** A tabela-base não tem horímetro nem compartimento.
  - Alerta por equipamento ativo com pelo menos 3 meses coletados.
  - Intervalo esperado = mediana dos meses entre coletas × 730 h.
  - Horas sem coleta = do 1º dia do último mês coletado até o corte, com fator 1,0 (padrão da RN-06).
  - Não substitui a RN-06 por horímetro, que exige leitura no Fabric.
- **Queda (RN-05).** Base `ano_anterior`, mês 2026-09, limiar acima de 20%. Mês com zero amostras é tratado como mês sem coleta e não gera alerta.
- **Potencial mensal.** No `forecast_consumo` é o potencial anual vigente no corte ÷ 12, repetido também nas linhas de histórico. Não é reconstruído para o passado.

### Resultados do potencial (`23_potencial.py`, executado em 39,6 s)

| Medida | Valor |
|---|---|
| Clientes com frota ativa / equipamentos ativos | 1.996 / 166.600 |
| Realizado 12m (out/25–set/26) | 907.016 amostras |
| Potencial anual (p10 – central – p90) | 839.215 – 1.080.580 – 1.316.082 |
| % Achieved (D6) por cliente: p25 / mediana / p75 / >100% | 0,486 / 0,578 / 1,000 / 22,6% |
| Nível de similaridade usado | segmento×família×porte 1.909; segmento×família 74; global 13 |
| Mediana do % Achieved por porte | 1–5: 0,500 (756 clientes); 6–20: 0,601 (454); 21–100: 0,666 (439); >100: 0,671 (347) |
| Largura relativa (p90 − p10) ÷ potencial por cliente | mediana 0,34; p25 0,20; p75 0,65 |

Os valores concentrados em 0,5 e 1,0 vêm de clientes pequenos com taxa inteira: 1 ou 2 amostras por equipamento por ano contra um benchmark de 2. O grupo `sem_segmento` tem 908 clientes (45% dos clientes com frota) e mediana exatamente 0,500.

**Sensibilidade à definição de "similar"** (Spearman do potencial por cliente contra a variante padrão):

| Variante | Potencial total | Mediana % Achieved | Spearman |
|---|---|---|---|
| segmento×família×porte q75 (padrão) | 1.080.580 | 0,578 | 1,000 |
| segmento×família q75 (sem porte) | 772.382 | 0,592 | 0,988 |
| família×porte q75 (sem segmento) | 1.033.550 | 0,500 | 0,984 |
| segmento×família×porte q50 | 653.612 | 1,000 | 0,997 |
| segmento×família×porte q90 | 1.577.120 | 0,323 | 0,995 |
| segmento×família×porte, mín. 10 clientes | 1.062.608 | 0,574 | 0,999 |

- A ordem dos clientes quase não muda entre as variantes (Spearman ≥ 0,98).
- O nível absoluto do potencial e do % Achieved depende sobretudo do quantil (de 0,65 mi em q50 para 1,58 mi em q90) e do uso do porte (−29% sem ele).
- A escolha cabe ao negócio (Bahia). Vai para o doc 13 §3 no fechamento de lote.

### Geração das saídas de forecast (`24_saidas_forecast.py`): interrompida, `data/forecast/` vazio

A primeira execução, em 28/10/2026, foi encerrada pelo Claude Code porque a máquina ficou sem memória (cerca de 0,9 GB livres de 16 GB, com outros jobs rodando em paralelo). Não houve erro do notebook. Etapas concluídas antes da parada:

| Etapa | Tempo |
|---|---|
| Cliente: treino do LightGBM (clientes com consumo em 36 meses, desde 2019) e previsão dos ativos | 146,4 s |
| Segmento: LightGBM direto (largura do intervalo) | 3,5 s |
| Equipamento: montagem das séries (treino na amostra `% 50`, previsão dos 166.600 ativos) | 15,2 s |
| Equipamento: treino e previsão em lotes | interrompido |

**Ainda não há** contagens finais, cobertura do holdout nem resultado de `contrato.validar` em dados reais. Nos testes sintéticos (`tests/test_saidas.py`), as quatro saídas passam no G4.

Para reexecutar, com a máquina livre (pelo menos 4 GB disponíveis; se faltar memória, use `ALS_LOTE=5000`):

```text
ALS_PASTA_DADOS=<repo>/data python notebooks/20_kpi1_consumo/24_saidas_forecast.py
```

O `relatorio.json` gerado traz:
- `series`: quantas séries foram treinadas e previstas por nível;
- `holdout.lgbm_todos`: WAPE, viés e cobertura por nível e horizonte;
- `contagens`: linhas e entidades por saída;
- `validacao`: resultado de G4/G5 por saída;
- `tempos_s`: tempo de cada etapa.

Esses números entram nesta seção quando a execução terminar.
