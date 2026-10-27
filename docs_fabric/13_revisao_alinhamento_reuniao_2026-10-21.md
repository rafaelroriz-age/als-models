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
| R1 | Fórmulas do Annual Sample Potential (segundo o Bahia: segmento, perfil, família de equipamento, pontos de coleta e similares, sem regressão) | Customer Status, "planilhão", Calculadora. **27/10:** no Customer Status é valor colado (1.314 clientes); fórmula de origem segue com o Bahia |
| R2 | Quais famílias a Calculadora cobre (Bahia estima 20–30 de mais de 400) | Calculadora × `equipamento.familia_equipamento_id`. **27/10:** 22 famílias em 3 setores, regra reproduzida em Python (48/50 blocos); falta o de-para com `familia_equipamento_id` |
| R3 | Confiabilidade da coluna de equipamento ativo e vida útil por família/segmento | `equipamento`, intervalos entre coletas |
| R4 | Taxa de retorno kit→amostra (histórico informal de 70–80%) | Protheus (vendas) × S360 (amostras) |
| R5 | Campo-chave do equipamento no S360 | Candidato: `equipamento_id` |
| R6 | Definição operacional de recorrência de **amostras** (distinta da de faturamento) | `amostra` × `cliente` × Protheus |
| R7 | Ticket médio e conversão atuais da Calculadora | Faturamento Protheus |
| R8 | Classificação de clientes antes da previsão (Fase 1b): recorrente, não recorrente ativo, menor atividade, churn | **Hipótese validada por dados parciais (27/10).** Protótipo em [classificacao.py](../src/features/classificacao.py) e [notebook 12](../notebooks/10_preprocessamento/12_classificacao_clientes.py), sobre os 2.388 clientes do Customer Status (ref. 10/08/2026). Regra: churn se sem venda/amostra há >180 dias; recorrente se compra em ≥6 dos 12 meses; senão "não recorrente ativo" se atinge ≥1 de 3 pontos da pirâmide (faturamento 12m ≥ R$ 10 mil, ≥10 máquinas testadas, potencial ≥500 amostras/ano), senão "menor atividade". Distribuição: recorrente 233 (9,8% dos clientes, 59,2% do faturamento 12m), não recorrente ativo 824 (34,5%; 35,5%), menor atividade 690 (28,9%; 3,1%), churn 641 (26,8%; 2,2%). Concordância com o `Real Status` manual (churn × não churn): 93,2%; os 162 divergentes (6,8%) são todos manual Churn com atividade ≤180 dias (34 na classe não recorrente ativo, 128 na menor atividade); a regra nunca marca churn onde o manual diz ativo. Árvore (profundidade 3, CV 5) prevendo o status manual: acurácia 93,8%, só usa recência (corte ~62 dias, 175 dias e meses de compra), sem ganho sobre a regra; não adotada. Limiares da pirâmide são palpite inicial (percentis), a calibrar com o Bahia/Diego; falta validar se as classes têm comportamento temporal distinto (série mensal) |

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
**Pendente (binários):** `Apresentacao_Executiva…v2.pptx`, `Plano_Executivo…v2.pdf` e o `.md` da apresentação ainda trazem o escopo anterior (6 componentes, EBIT único, % Achieved antigo, entrega via semântico + MCP). Regerar quando o escopo estiver estável.

## 5. Pontos ainda sem resposta (não bloqueiam a Fase 0)

- Meta numérica de acurácia (MAPE) por KPI e horizontes de previsão.
- Cadência exigida: semanal é requisito ou desejável?
- Hierarquia matriz/filial do Zoho utilizável para agrupar clientes (ex.: 8 usinas de um grupo)?
- Janela de CU livre na F8 para agendar pipelines.
