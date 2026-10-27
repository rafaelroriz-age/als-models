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

Teste em aberto (não causado por esta tarefa, que só adiciona docs): `tests/test_comparacao.py::test_g3_oraculo_bate_baselines_e_tem_cobertura` falha em `python -m pytest` (177 passed, 1 failed em 27/10/2026): a asserção de que a cobertura dos modelos sem intervalo é NaN não vale, coerente com o achado abaixo. Corrigir em `tabela_comparativa`/`resumir` antes de ler cobertura do G3.

Achado de método (de [12](12_plano_trabalho_esboco.md)): `resumir` calcula cobertura = 0 para modelo sem intervalo quando resumido junto com modelo que tem `yhat_lo/yhat_hi`. A cobertura só é lida dos modelos com intervalo.

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
