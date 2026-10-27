# Decisões e Hipóteses: alinhamento com a reunião de 21/10/2026

> **Hierarquia de fontes:** o material mais novo é a verdade de referência: [documentacao-tecnica.md](documentacao-tecnica.md) e a transcrição da reunião de 21/10/2026 ([Revisando KPIs e métricas…](Revisando%20KPIs%20e%20métricas%20para%20Projeção%20de%20consumo%20de%20amostras.md)). Onde outro documento divergir deles, vale o mais novo. Este arquivo registra o que foi decidido, o que será testado por protótipo e o que será descoberto nos dados.

## 1. Decisões fechadas

| # | Decisão | Origem |
|---|---------|--------|
| D1 | O projeto prevê **consumo de amostras** e **vendas derivadas do consumo**. TAT do laboratório não faz parte do projeto | documentacao-tecnica |
| D2 | **Faturamento e EBIT são targets separados** do KPI 2 | Decisão do time (26/10) |
| D3 | **Novos clientes e reativados ficam fora do escopo por ora.** Fase 1 do KPI 2: recorrentes e não recorrentes ativos (+ churn e variável de mercado) | Reunião (Diego) + decisão do time |
| D4 | **Taxa de conversão de 70% fora** do forecast de receita | Reunião (Diego, Keli) |
| D5 | **Recorrente** = compras em ≥6 meses distintos dos últimos 12 e última compra <90 dias. Comprador de alto volume e poucas compras = não recorrente ativo | Reunião (Keli, Diego) |
| D6 | **% Achieved = amostras realizadas ÷ potencial anual** (não é cadastrados ÷ monitorados) | Reunião (Caio, Keli) + dicionário 08 |
| D7 | **O medallion já existe** (`bronze_*` e `silver_*` de protheus, s360 e zoho no `LakehouseOel`). O probe foi refeito com sucesso. Novas camadas só se o escopo exigir no futuro | Decisão do time (26/10) |
| D8 | **Horímetro é uma leitura por coleta** (`horas_oleo`, `horimetro_equipado` em `amostra`), não uma série contínua | Confirmado (26/10) |
| D9 | **Amostras avulsas (sem equipamento):** apenas identificar e limpar no pré-processamento. Tratamento adicional é descoberta futura | Decisão do time (26/10) |
| D10 | Potencial = sobre a frota conhecida (cadastrada + benchmark); não inclui filiais não cadastradas | Reunião (Keli, Diego) |
| D11 | **Etapa de classificação de clientes** entra no plano (Fase 1b), por proposta do Rafael | Reunião |
| D12 | Acesso ao lakehouse resolvido (Rafael já acessa) | Reunião (Caio) |

## 2. Hipóteses a testar por protótipo

Todas as hipóteses abaixo serão prototipadas e comparadas por acurácia (backtest) e custo (CU na F8). O cliente escolhe a melhor.

| # | Hipótese | Alternativas a comparar |
|---|----------|-------------------------|
| H1 | Papel das oportunidades >80% do Zoho no forecast | (a) somam ao forecast, como no Power BI atual; (b) só descontam, no cross-check |
| H2 | O que a receita representa | (a) venda de kit/pacote; (b) análise processada |
| H3 | Formato de entrega | (a) dashboard HTML + acesso SQL às tabelas de saída; (b) modelo semântico (DirectLake); (c) API/MCP |
| H4 | Regra de recorrência: última compra <90 dias é E ou OU | **Resolvida: E** (texto do Forecast 27; Customer Status dá 233 só com ≥6 meses vs 231 com E). Ver [14](14_fase0_engenharia_reversa_e_base_de_codigo.md) |

## 3. Descobertas por dados (engenharia reversa)

Não dependem de resposta do negócio; saem das planilhas, artefatos e tabelas.

| # | O que descobrir | Onde olhar |
|---|-----------------|------------|
| R1 | Fórmulas do Annual Sample Potential (segundo o Bahia: segmento, perfil, família de equipamento, pontos de coleta e similares, sem regressão) | Customer Status, "planilhão", Calculadora. **27/10:** no Customer Status é valor colado (1.314 clientes); fórmula de origem segue com o Bahia. **T05:** sem coluna no S360/Zoho e não reproduzível pelos dados; proposta frota ativa × taxa da família (abaixo) |
| R2 | Quais famílias a Calculadora cobre (Bahia estima 20–30 de mais de 400) | Calculadora × `equipamento.familia_equipamento_id`. **27/10:** 22 famílias em 3 setores, regra reproduzida em Python (48/50 blocos); falta o de-para com `familia_equipamento_id` |
| R3 | Confiabilidade da coluna de equipamento ativo e vida útil por família/segmento | `equipamento`, intervalos entre coletas. **T05:** flag sozinha não serve (96% "ativo"); regra flag = 1 + coleta em 12 meses → 85,9% do cadastro inativo (abaixo) |
| R4 | Taxa de retorno kit→amostra (histórico informal de 70–80%) | Protheus (vendas) × S360 (amostras) |
| R5 | Campo-chave do equipamento no S360 | Candidato: `equipamento_id` |
| R6 | Definição operacional de recorrência de **amostras** (distinta da de faturamento) | `amostra` × `cliente` × Protheus |
| R7 | Ticket médio e conversão atuais da Calculadora | Faturamento Protheus |
| R8 | Classificação de clientes antes da previsão (Fase 1b): recorrente, não recorrente ativo, menor atividade, churn | **Hipótese validada por dados parciais (27/10).** Protótipo em [classificacao.py](../src/features/classificacao.py) e [notebook 12](../notebooks/10_preprocessamento/12_classificacao_clientes.py), sobre os 2.388 clientes do Customer Status (ref. 10/08/2026). Regra: churn se sem venda/amostra há >180 dias; recorrente se compra em ≥6 dos 12 meses; senão "não recorrente ativo" se atinge ≥1 de 3 pontos da pirâmide (faturamento 12m ≥ R$ 10 mil, ≥10 máquinas testadas, potencial ≥500 amostras/ano), senão "menor atividade". Distribuição: recorrente 233 (9,8% dos clientes, 59,2% do faturamento 12m), não recorrente ativo 824 (34,5%; 35,5%), menor atividade 690 (28,9%; 3,1%), churn 641 (26,8%; 2,2%). Concordância com o `Real Status` manual (churn × não churn): 93,2%; os 162 divergentes (6,8%) são todos manual Churn com atividade ≤180 dias (34 na classe não recorrente ativo, 128 na menor atividade); a regra nunca marca churn onde o manual diz ativo. Árvore (profundidade 3, CV 5) prevendo o status manual: acurácia 93,8%, só usa recência (corte ~62 dias, 175 dias e meses de compra), sem ganho sobre a regra; não adotada. Limiares da pirâmide são palpite inicial (percentis), a calibrar com o Bahia/Diego; falta validar se as classes têm comportamento temporal distinto (série mensal) |
| R9 | Casamento das chaves entre S360, Protheus e Zoho (ponte para KPI 2 e cross-check) | **T03 (27/10):** Protheus ↔ S360 casa 40,1% por `id_cigam` e 50,5% com a regra de grupo (código `A`+5 dígitos ↔ 6 dígitos do S360, inferida, não confirmada); `codigo_legado` não é o ERP ID (0,3%). Cadeia amostra → compartimento → equipamento fecha em 97,7%. Só 44,8% do faturamento Protheus tem cliente no S360; 49,5% dos grupos Protheus não têm par no S360 (55,2% do faturamento). Detalhes em [14](14_fase0_engenharia_reversa_e_base_de_codigo.md) §2 |

### T05 (27/10/2026): origem do Annual Sample Potential e equipamento ativo

Leitura somente leitura do LakehouseOel pela 1433 (`bronze_s360.amostra/compartimento/equipamento/cliente`, `bronze_zoho.accounts`, `silver_zoho.accounts`) cruzada com `data/planilhas/customer_status.parquet`. Data de corte das coletas: 27/10/2026. Coletas com data fora de 2000–27/10/2026 descartadas (há datas de 0001 e 2115).

**Origem do potencial (R1, RN-07): não há fonte rastreável nos dados.**

- Não existe coluna de potencial no S360 nem no Zoho. Os campos mais próximos do Zoho estão vazios ou quase: `average_samples_per_month_last_6_months_trend` e `evolution_of_monitoring_coverage` têm 0 de 9.843 contas preenchidas, e `equipment_monitored_in_the_last_24_months_active` tem 3. `initial_quantity_of_active_equipment` tem 5.630 contas preenchidas, mas não explica o potencial: Spearman 0,39 e razão potencial/equipamentos com mediana 2,9 (p10 0,15, p90 35). O potencial vem de outro lugar.
- No Customer Status o potencial é um inteiro colado (1.314 clientes, 100% inteiros). Nenhum candidato derivado dos dados o reproduz. A tabela mostra Spearman e quanto dos 1.314 fica a até 10% do valor:

  | Candidato (por ERP, S360) | Spearman | Até 10% | Potencial ÷ candidato (mediana) |
  |---|---|---|---|
  | Amostras FY25 (abr/24–mar/25) | **0,75** | 16% | 1,39 |
  | Média FY24–FY26 | 0,72 | 11% | 1,31 |
  | Máximo anual FY22–FY26 | 0,70 | 10% | 0,91 |
  | Frota ativa 12m × taxa anual mediana da família | 0,58 | 11% (20% de tolerância) | 0,81 |
  | Equipamentos com coleta nos últimos 24 meses | 0,67 | 5% | 3,55 |

  O melhor preditor é o realizado do FY25 multiplicado por cerca de 1,4, o que sugere uma meta posta sobre o histórico. Ainda assim, 343 dos 1.314 clientes (26%) têm potencial **abaixo** do que já coletaram no FY25, ou seja, valores defasados. Exemplos de ERP (segmento, potencial, amostras FY25, equipamentos ativos 12m, frota × taxa): 194063 (Generators, 38, 43, 35, 116); 193023 (Preparation, 164, 240, 250, 3.000); 102017 (Mobile, 661, 714, 29, 309).
- O `% Achieved` da planilha é `Current Samples (abr–jul FY26/27) ÷ Annual Sample Potential` em 86,7% das 1.139 linhas, isto é, 4 meses de realizado contra um potencial anual. Isso confirma a decisão D6 de unificar a definição.
- **Proposta para RN-07:** não depender do valor colado. A base derivável é **frota ativa (regra abaixo) × taxa anual da família** (12 ÷ intervalo mediano entre coletas da família, no máximo 12 por ano). Essa base é calibrada pelo benchmark de similares na T16. O valor do Customer Status fica só como referência de comparação. Falta o Bahia confirmar a fórmula original (§5).
- **Chave S360 → ERP:** é `cliente.id_cigam`, não `codigo_legado`. `id_cigam` cobre 2.339 dos 2.388 ERP IDs do Customer Status; `codigo_legado` cobre 1.328. Os totais de abr–jul FY25/26 batem (279.416 na planilha contra 285.276 no S360), mas por cliente só 37% batem exatamente. Uma hipótese é a planilha agrupar contas de outro jeito (filiais, Raiz CNPJ); falta testar.

**Equipamento ativo (R3, RN-08): regra proposta.**

> Um equipamento está **ativo** na data D se `equipamento.ativo = 1` **e** tem coleta válida (amostra não excluída, via compartimento) nos 12 meses até D. Equipamento sem nenhuma coleta é inativo. Só entra na frota do **potencial** como "novo" se `ativo = 1` e foi cadastrado há no máximo 12 meses.

Evidências:

- **Flag `ativo` sozinha não serve.** Marca 1.022.906 dos 1.063.706 equipamentos (96,2%) como ativos, e 463.941 deles nunca tiveram coleta. Os cadastros sem coleta se concentram em 2023 (269.399), o que indica carga em massa. Por outro lado, `ativo = 0` é confiável: de 22.348 equipamentos com flag 0 e histórico, só 392 (1,8%) voltaram a coletar em 12 meses.
- **Tempo desde a última coleta.** No backtest em 31/07/2025, a chance de coletar nos 12 meses seguintes cai com o tempo parado:

  | Meses parado | Chance de voltar a coletar |
  |---|---|
  | ≤3 | 72% |
  | 3–6 | 46% |
  | 6–9 | 27% |
  | 9–12 | 20% |
  | 12–15 | 12% |
  | 15–18 | 8% |
  | 18–24 | 6% |
  | 24–36 | 3% |
  | >60 | 0,4% |

  O corte de 12 meses mantém 88,9% dos equipamentos que voltaram, com precisão de 51,9%. O de 18 meses mantém 93,3%, com precisão de 43,6%.
- **Família não ajuda; vida útil não serve como critério.** Um corte por família (2× o p75 do intervalo da família, entre 12 e 36 meses) chega a precisão 0,480 e recall 0,908, praticamente igual ao corte global de 15 meses (0,475 e 0,916). Há 515 famílias, e o intervalo mediano entre coletas varia de 0,4 a 8,4 meses nas 12 maiores. A "vida" observada (da 1ª à última coleta, equipamentos com 3 ou mais coletas e parados há mais de 24 meses) tem mediana de 0,9 ano e p90 de 3,9 anos. Isso mede a duração do monitoramento, não a vida mecânica, então os ~7 anos da colhedora de cana não são verificáveis com estes dados.

**Inativos sobre o cadastro (1.063.706 equipamentos):**

| Corte | Data | Inativos |
|---|---|---|
| 12 meses | 27/10/2026 | **913.280 (85,9%)** |
| 12 meses | 31/07/2026 | 892.595 (83,9%) |
| 18 meses | 27/10/2026 | 82,2% |

Composição dos inativos em 27/10/2026: 40.800 com flag 0, 463.941 com flag 1 e nunca coletados, e 408.539 com flag 1 e coleta há mais de 12 meses. Restam 150.426 ativos. Somando os 20.706 novos sem coleta ao potencial, os inativos caem para 83,9%.

**Exemplos numéricos** (D = 27/10/2026, `equipamento_id`):

1. **1026195** (família 4552, flag 1): 19 coletas, a última em 11/09/2026 (1,5 mês), intervalo médio de 1,0 mês. **Ativo.**
2. **1005786** (família 4751, flag 1): 6 coletas com intervalo médio de 4,7 meses, a última em 07/02/2025 (20,6 meses). Passou de 12 meses, e equipamentos parados entre 18 e 24 meses voltam só em 6% dos casos. **Inativo.**
3. **1247857** (família 1938, flag 0): 1 coleta em 20/08/2026 (2,2 meses). A flag 0 prevalece, porque só 1,8% dos equipamentos com flag 0 voltam a coletar. **Inativo.** Há 431 casos assim no cadastro, a revisar com o negócio.

## 4. Correções feitas na documentação

| Problema | Correção |
|----------|----------|
| `AGENTS.md`, `MEMORY.md`, `README_AGENTES.md`, `SETUP_AGENTES_SUMMARY.md`, `AGENTS_QUICK_START.md`, `AGENT_ARCHITECTURE.md`, `.claude/agents_config.json` e memórias dos agentes descreviam o projeto como forecast de TAT | Reescritos para consumo de amostras + vendas |
| Cinco arquivos de agentes repetiam o mesmo conteúdo (~52 KB) e a documentação não era atualizada ao concluir tarefas | Consolidados em um `AGENTS.md` enxuto com regra de documentação (27/10); hook em `.claude/settings.json` lembra a regra após editar código ou rodar scripts |
| Backlog espalhado em listas de fases (06) e etapas (12), sem prompts nem ordem de execução | `BACKLOG.md` na raiz com 24 tarefas (T01–T24), dependências, arquivos tocados e prompt copiável; `scripts/backlog.py` lista, mostra o próximo lote paralelo seguro e atualiza status; `scripts/run_backlog.py run` dispara sessões `claude --bg` em worktree isolado; `PROGRESSO.md` é gerado a partir do backlog; operação PC/celular em `AUTOMATIZACAO.md` (27/10) |
| Agentes podiam alterar dados já existentes no Fabric de produção; regra de confirmação genérica | Decisão do usuário (27/10): agentes executam o Fabric por API e publicam objetos novos (`Files/als_oilmodel/`, notebooks `als_*`); só alterar dado existente exige pessoa. Barreira em `scripts/fabric_guard.py` (hook + `fabric_deploy.py`), liberação só com `ALS_FABRIC_ESCRITA=1`. Limite: inspeciona texto, não pega escrita montada dinamicamente |
| Sessões do backlog paravam em prompts de permissão, terminavam sem integrar na main e usavam um modelo só | `run_backlog.py` (27/10): campo `Dificuldade` roteia modelo/esforço/teto de gasto; `colher` commita, faz merge e marca `done`; `auto` repete colher + disparo; sessões em `bypassPermissions` com o hook `fabric_guard` mantido |
| Doc 12 dizia que o probe falhou e que Protheus e Zoho não apareciam | Estado atual atualizado: probe refeito, tudo no `LakehouseOel` |
| Doc 04 mandava desenhar o medallion; doc 06 dizia que já existe | Alinhados: medallion existente |
| % Achieved com duas definições (02/01/apresentação × 08) | Unificado (D6) |
| Novos/reativados e EBIT tratados como parte única do KPI 2 | Ajustados (D2, D3) |
| Entrega tratada como modelo semântico + MCP já decididos | Marcada como hipótese a prototipar (H3) |
| Perguntas "ao cliente" já respondidas ou viradas em descoberta | Removidas dos docs 03, 06, 10 e 12 |
| Grafia "Proteus" | Unificada para "Protheus" (exceto doc 00, fiel ao PDF) |
| `LEIA-ME` desatualizado | Índice completo |

**Mantidos como estão:** `documentacao-tecnica.md` e `00_escopo_original.md` (fiéis à fonte), planilhas convertidas e a transcrição.
**27/10 (T24):** o `.md` da apresentação foi reescrito com o escopo atual (KPI 1 Real/Potencial; KPI 2 com faturamento e EBIT separados; novos e reativados fora; % Achieved de D6; entrega por protótipos H3; decisões D1–D12).
**Pendente (binários):** `Apresentacao_Executiva…v2.pptx` e `Plano_Executivo…v2.pdf` continuam na versão anterior (6 componentes, EBIT único, % Achieved antigo, entrega via semântico + MCP) até serem regerados a partir do `.md`.

## 5. Pontos ainda sem resposta (não bloqueiam a Fase 0)

- Meta numérica de acurácia (MAPE) por KPI e horizontes de previsão.
- Cadência exigida: semanal é requisito ou desejável?
- Hierarquia matriz/filial do Zoho utilizável para agrupar clientes (ex.: 8 usinas de um grupo)?
- Janela de CU livre na F8 para agendar pipelines.
- Fórmula original do Annual Sample Potential (R1): os dados não a reproduzem; o potencial de Customer Status é valor colado, com 26% dos clientes abaixo do realizado de FY25. Confirmar com o Bahia.
- Regra de grupo do ERP ID (R9): o código de 6 dígitos do S360/Zoho seria o código Protheus + 1 dígito de filial (`A19129` + `5`). Confirmar com o time de dados.
- Por que 49,5% dos grupos Protheus (55,2% do faturamento) não têm cliente no S360 (R9): venda de peças, intercompany, cliente sem coleta ou código guardado de outro jeito. Não apurado.
- Por que `id_protheus` do Zoho está 100% nulo e o CNPJ falta em S360 e Protheus (R9). Pedir ao time de dados.
- Equipamentos com `ativo = 1` e sem coleta (463.941) e com flag 0 mas coleta recente (431 casos, classificados como inativos pela flag): a revisar com o negócio (R3).
