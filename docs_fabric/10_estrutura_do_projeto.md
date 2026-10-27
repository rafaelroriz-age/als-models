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
| 10 | Exposição | `src/serving/` | Fase 5 | **Entregável 3** protótipos de entrega (HTML + SQL, semântico, MCP) |

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
| RN-03 | Recorrente: compras em ≥6 meses distintos dos últimos 12 **e** última compra <90 dias (sem redutor de 70%). Comprador de alto volume e poucas compras = não recorrente ativo | Confirmada (Diego, Keli); E/OU da última compra conferido nos dados (H4) |
| RN-04 | Churn: >6 meses sem compra. Reativado: volta após >1 ano | Churn: a validar. Reativados: fora do escopo da fase 1 |
| RN-05 | Alerta de queda: amostras do cliente caem >20% | Implementada em `src/features/alertas.py` (`alertar_queda`, T08). **Base de comparação: decisão pendente com o negócio** (Negócio, doc 12). Padrão adotado: `ano_anterior` (mesmo mês do ano anterior), com `mm3` e `mm12` disponíveis. Queda exatamente 20,0% não alerta; mês sem coleta fica NaN e não alerta |
| RN-06 | Compartimento churn: compartimento deixa de ser coletado dentro do intervalo esperado | Implementada em `src/features/alertas.py` (`compartimento_churn`, T08). Padrão adotado: churn se horas desde a última coleta > `fator` × `intervalo_h` (fator = 1,0, ou seja, mais que um intervalo). Ainda a validar com o negócio e depende de RN-01 e de leitura atual do horímetro |
| RN-07 | Potencial = benchmark de similares do mesmo segmento; % Achieved = realizado ÷ potencial | Sem fonte rastreável: valor colado no Customer Status, sem coluna no S360/Zoho. Proposta T05: frota ativa × taxa anual da família, calibrada por similares (T16). Ver doc 13 §3 |
| RN-08 | Inatividade do equipamento inferida por engenharia reversa: coluna de ativo do S360, intervalos entre coletas e vida útil por família/segmento (ex.: colhedora de cana ~7 anos). O horímetro é uma leitura por coleta, não série contínua | Proposta T05: ativo = `equipamento.ativo = 1` e coleta nos últimos 12 meses (recall de 88,9% no backtest); família e vida útil não melhoram a regra. Ver doc 13 §3 |
| RN-09 | Sazonalidade: Cana (parada nov-mar), MT (soja/milho/algodão), Indústria (mensal/bimestral), Locomotiva (semanal) | Parcial (item 7) |
| RN-10 | Cross-check: descontar faturado no mês (Protheus), pedidos pendentes e oportunidades ativas (Zoho). Hipótese a testar: oportunidades >80% somam ao forecast vs só descontam | Em teste por protótipo (H1) |
| RN-11 | Ticket médio R$ 1.950 e conversão 5% (out/2022) | **Defasado** (item 4) |
| RN-12 | Recorrência de amostras distinta da recorrência de faturamento (cliente compra e distribui a unidades/concessionárias que processam) | A descobrir nos dados (R6) |
| RN-13 | Calculadora cobre ~20–30 famílias (estimativa do Bahia) de >400 no S360 | Cobertura exata a descobrir (R2) |
| RN-14 | Taxa de retorno kit→amostra (histórico informal ~70–80%) como elo venda→consumo | A derivar dos dados (R4) |
| RN-15 | Potencial é sobre a frota conhecida (cadastrada + benchmark); não inclui filiais não cadastradas | Nova (Keli, Diego, 21/10) |
| RN-16 | Amostra avulsa (sem equipamento): identificar e limpar no pré-processamento; tratamento adicional é descoberta futura | Definida (D9) |
| RN-17 | Faturamento e EBIT são targets separados. Receita como venda de kit vs análise processada: testar ambas | Em teste por protótipo (H2) |

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

### 3.1 Contrato implementado em `src/gates/checks.py` (T06)

Pandas puro, sem acesso ao Fabric; cada função devolve `list[dict]` com `gate, checagem, alvo, ok, detalhe` (grava em `dq_resultados`). Testes: `tests/test_gates.py` (30 casos: um válido e um que falha por verificação).

| Função | Entrada | Regras (falha quando) |
|---|---|---|
| `avaliar_g0(perfis, hoje)` | lista de perfis `{tabela, n_linhas, nulos_pct{col}, datas{col:(min,max)}}` | tabela de `CHAVES_OBRIGATORIAS` sem perfil; `n_linhas == 0`; `% nulos` da chave > limite (ou coluna sem perfil); data mín < 2010-01-01 ou máx > hoje+1 dia (ou ilegível) |
| `avaliar_g1(base, chave, valor)` | tabela entidade × mês (`periodo` = `Timestamp` do 1º dia) | chave duplicada; `valor` negativo; `valor` nulo; mês faltando dentro do intervalo de uma entidade |
| `avaliar_g1_limpo(df, chaves_nao_nulas, unico, datas, hoje)` | tabela limpa | nulo em qualquer chave obrigatória; duplicatas em `unico`; datas < 2010-01-01 ou > hoje+1 dia; coluna ausente conta como falha |
| `cobertura_join(esq, dir, chave, minimo_pct=90)` | duas tabelas com a coluna-chave | % de `esq[chave]` não nulo presente em `dir[chave]` < `minimo_pct` (esquerda vazia = 0%) |

`minimo_pct` e os limites de nulos são provisórios até a T03 medir as taxas reais de casamento. Pendentes (não cobertos aqui): frescor da carga, tipos de coluna, horímetro não decrescente/saltos (G1 aviso), G2–G5.

### 3.2 Tabela-base entidade × mês (T14, 2026-10-27)

Notebook `notebooks/10_preprocessamento/10_base_amostras.py`, com a lógica testada em `src/features/base.py` (`tests/test_base.py`, 10 casos). Ele lê o LakehouseOel em modo somente leitura, com 8 consultas SELECT agregadas no endpoint, e o cache fica em `<dados>/base/bruto/`. Saídas em `data/base/`, fora do git:

| Arquivo | Conteúdo |
|---|---|
| `base_cliente_mes.parquet` | 482.744 linhas, 7.424 entidades, de 2010-01 a 2026-09 (último mês completo). Colunas: `amostras` (alvo do KPI 1, sem avulsas), `avulsas`, `faturamento`, `faturamento_servico` (CFOP x933), `oport_abertas_n/valor/valor_ponderado`, `oport_ganhas_n/valor`, `oport_perdidas_n`, `tem_*`, `segmento` (moda Zoho, 2.689 entidades) |
| `base_equipamento_mes.parquet` | 2.681.891 linhas esparsas, uma por equipamento × mês com coleta. 619.270 equipamentos, `amostras` e `compartimentos` por linha; a entidade é a do cliente que mais coletou (4 equipamentos têm mais de uma) |
| `mapa_s360.parquet`, `mapa_protheus.parquet` | ponte `cliente_id` → entidade e `cod_cliente` → entidade, com a regra usada em cada linha |
| `relatorio.json` | descartes, cobertura e as 24 checagens G1 |

**Entidade = raiz do CNPJ** (8 dígitos, via Zoho `accounts.cnpj`). A ponte foi descoberta nos dados e substitui a hipótese "`codigo_legado` = ERP ID" da §2 do [14](14_fase0_engenharia_reversa_e_base_de_codigo.md):
- S360 `cliente.id_cigam`/`codigo_legado` = Zoho `erp_id`, que guarda o código legado CIGAM (`192936`) ou o código Protheus (`A63989`);
- Protheus `notassaida.cod_cliente` = Zoho `erp_id` no formato `A99999`, **ou o sufixo do nome da conta** (`"RUMO - MALHA NORTE - SAO PAULO/SP - A19079"`, às vezes com a loja, `A5680901`). O `id_protheus` do Zoho está 100% nulo;
- o Protheus sem código no Zoho cai na razão social: `contasreceber.nome_cliente` = Zoho `razao_social`, normalizada (sem acento, pontuação e sufixo societário). O casamento só é aceito quando o nome aponta para uma única entidade;
- sem ponte, a entidade fica `s360:<id>`, `protheus:<cod>` (S360 e Protheus com o mesmo código `A99999` caem juntos) ou `zoho:<id>`, este para conta sem CNPJ válido.

**Cobertura de join:**

| Ponte | Chaves com ponte | Peso coberto | Por regra (% do peso) |
|---|---|---|---|
| S360 cliente → Zoho | 5.400/8.567 clientes com amostra (63,0%) | **93,0% das amostras** | `zoho_erp` 93,0; `protheus_direto` 0,01; sem ponte 7,0 |
| Protheus → entidade | 2.573/2.822 códigos (91,2%) | **87,7% do faturamento** | `zoho` 41,4; `nome_zoho` 46,3; `s360` 0,07; sem ponte 12,3 |

Na janela comum (2024-08 a 2026-09), 80,0% das amostras estão em entidades com faturamento e 82,9% do faturamento em entidades com amostras. São 1.315 entidades com as duas fontes. Só código ou só nome não bastam: o casamento direto `cod_cliente` ↔ `erp_id` cobre 12,5% do faturamento, e a razão social sozinha, 50,8%.

**Amostras descartadas** (8.665.715 linhas brutas):

| Motivo | Linhas | Regra |
|---|---|---|
| sem data de coleta **e** de entrada no laboratório | 1.905.116 | não consumida: 1,80 mi têm `status_amostra = 1`, sem coleta nem entrada (pré-registro/kit não usado, **hipótese a confirmar**) |
| data fora de 2010-01-01..hoje | 1.549 | anos 1, 19, 201, 2115... quando a entrada também é implausível |
| mês corrente (2026-10, incompleto) | 56.100 | fora da base até fechar o mês |
| `id` duplicado | 143 | mantida uma |
| `excluido = 1` | 60 | — |
| cliente inexistente no cadastro | 13 | — |
| **avulsas (D9)** | **235.995** | sem compartimento ou com compartimento/equipamento inexistente: ficam fora de `amostras` e só são contadas em `avulsas` |
| mantidas em `amostras` | **6.466.739** | 328.794 delas datadas pela entrada no laboratório (coleta nula/implausível) |

**Faturamento:** Protheus `silver_protheus.notassaida` desde 2024-08. Ficam de fora R$ 6,33 mi de CFOP x554 (remessa de ativo), x557 (uso e consumo) e x922 (simples faturamento de entrega futura, que reaparece em x116/x117). Sobram R$ 179,1 mi até 2026-09; na base entram R$ 176,7 mi, porque 2026-10 está incompleto. Antes do 1º mês de cada fonte (faturamento 2024-08, oportunidades 2024-01) as colunas são **NaN, não zero**. O CFOP x949 ("outra saída", R$ 54 mi) continua dentro e deve ser examinado na T17.

**Oportunidades:** `silver_zoho.deals` por `conta_id` → conta Zoho → entidade. Todas as contas casaram. Ganhas e perdidas vão pelo mês do fechamento real; abertas, pelo previsto. O valor ponderado usa `probabilidade/100`. Os deals vêm em `moeda = USD`, e `Closed Won` soma US$ 1,2 bi contra R$ 179 mi faturados: o campo `valor` não é comparável ao faturamento sem validação (T18).

**G1 (22/24):** passam as checagens de chave única, ausência de negativos, ausência de nulos e meses contínuos em `amostras`, `faturamento` e `oport_ganhas_valor`, cada uma na janela da sua fonte. Passam também as chaves sem nulos e sem duplicatas dos mapas e da tabela de equipamento, e as datas no intervalo. **Falham as duas `cobertura_join` com mínimo de 90%**, medidas em linhas agregadas: S360 → ponte 86,1% e Protheus → ponte 89,7%. A cobertura ponderada (93,0% das amostras e 87,7% do faturamento) é a medida a usar.

**Limites e próximos passos:** a base de compartimento × mês não foi gerada (5,5 mi linhas esparsas); a T15 pode derivá-la com a mesma consulta trocando o nível. Faltam a confirmação do significado de `status_amostra = 1` com o time do S360, a lista de intercompany (ex.: `A58483` ALS Tribology, R$ 0,92 mi) e o resíduo de 12,3% do faturamento sem ponte, cujo maior código é `ZOAG81`, com R$ 3,99 mi e sem nome no `contasreceber`.

## 4. Plano de testes (resumo para `specs/04_plano_testes.md`)

- **Unitários (pytest):** cada regra RN-xx com casos de borda (ex.: exatamente 6 meses, exatamente 90 dias, queda de 20,0% vs. 20,1%).
- **Contrato:** schema das tabelas de saída e das entradas (G0, G4).
- **Leakage:** reconstruir uma data passada e provar que nenhuma feature enxerga o futuro.
- **Regressão numérica:** reproduzir a Calculadora e o Forecast 27 em amostra conhecida (dourada) com tolerância definida.
- **Backtest:** MAPE/MAE por mês, segmento e cliente desde 2022 vs. baselines; curva de convergência semanal.
- **FinOps:** CU por execução e por consulta MCP/DirectLake.

### 4.1 Features de série por entidade × mês (T07, `src/features/series.py`)

`gerar_features(mensal, ate=None, p=ParametrosSeries())` recebe `entidade, periodo, valor[, segmento]`, completa os meses sem registro com 0 (`completar_meses`) e devolve `valor` (alvo) mais: `lag_1/2/3/12`, `mm_3/mm_12`, `tendencia_6` (inclinação OLS dos 6 meses anteriores), `mes_sin/mes_cos`, `segmento` (último conhecido) e `status` (`classificar_clientes` de `regras.py` com corte no fim do mês anterior; `sem_historico` na 1ª observação).

- **Sem vazamento:** toda janela parte de `valor.shift(1)`; lags usam só `shift(k≥1)`.
- **Parâmetros (RN não aprovada):** `ParametrosSeries` expõe lags, janelas, janela da tendência, `janela_completa` (False aceita média móvel parcial), `incluir_status` (RN-03/RN-04, churn "a validar") e `recorrencia` (`ParametrosRecorrencia`: 6 meses/90 dias/6 meses de churn).
- **Testes** (`tests/test_series.py`, dados sintéticos, 7 casos): valores conhecidos de lags/MM/tendência, janela parcial vs. cheia, sazonalidade/segmento/zeros, status, e dois testes de vazamento: (1) somar 1e6 a um mês não altera nenhuma feature de meses ≤ ele; (2) truncar o histórico antes do mês alvo (`ate=alvo`) reproduz as mesmas features. `python -m pytest`: 31 passed.
- **Limite conhecido:** o status roda `classificar_clientes` uma vez por mês (custo ~ meses × clientes); medir no volume real (T14).

## 5. Ordem de execução

1. Fase 0: `scripts/fabric_probe.py` → preencher `specs/01_origens_dados.md` e [08](08_dicionario_de_dados.md); notebooks `00_validacao` definem os G0/G1 reais.
2. Fechar `specs/02` e `03` a partir das planilhas, artefatos e dados (descoberta); levar ao Bahia/Keli apenas o que os dados não resolverem.
3. Fases 1-3: notebook → função testada em `src/` → pipeline. Nada vai para `src/` sem teste e gate.
4. Fases 4-5: backtest, snapshots, semântico/MCP, medição de CU.

## Pendências

- Acesso de leitura e nomes das tabelas: resolvidos pelo probe (ver [discovery](08_dicionario_de_dados_discovery.md)).
- Campo do ID de equipamento, origem do Annual Sample Potential e parâmetros de ticket/conversão: serão descobertos por engenharia reversa na Fase 0.
