> **Versão de escopo atual (27/10/2026), em markdown.** Reflete as decisões D1–D12 e as hipóteses H1–H4 de [13](13_revisao_alinhamento_reuniao_2026-10-21.md). O `.pptx` e o `.pdf` ainda trazem a versão anterior à reunião de 21/10/2026 até serem regerados (ver 13 §4).

<!-- Slide number: 1 -->

PROJETO DE CIÊNCIA DE DADOS — ALS / LS
Forecast de Consumo de Amostras e Vendas no Microsoft Fabric
Plano de Execução sobre as Camadas Bronze/Silver Existentes, FinOps (Capacidade F8) e Acurácia em Produção
Reunião de Alinhamento e Validação Técnica  |  Ecossistema Azure / OneLake

<!-- Slide number: 2 -->

## 1. Visão Geral e Escopo da Fase 1

Mudança de paradigma: projetar vendas a partir do consumo real dos equipamentos (~5 milhões de amostras/ano).

**KPI 1 — Forecast de Consumo de Amostras**

- Ordem de dependência: consumo puxa a venda (horímetro → coleta → pedido).
- **Visão Real:** baseada em horas trabalhadas, meses/ano e intervalo por compartimento (motor 250h, hidráulico 500h, arrefecimento 1000h; preventiva vs. meia preventiva).
- **Visão Potencial:** **% Achieved = amostras realizadas ÷ potencial anual** (D6), com benchmark de clientes similares do mesmo segmento. O potencial vale para a frota conhecida (cadastrada + benchmark), sem filiais não cadastradas (D10).
- Granularidade: cliente → equipamento → compartimento (agregável por setor/segmento).
- Sinais de ação: queda >20% no volume do cliente e "compartimento churn".
- Horímetro: uma leitura por coleta (`horas_oleo`, `horimetro_equipado` em `amostra`), não série contínua (D8).
- Amostras avulsas (sem equipamento): apenas identificar e limpar no pré-processamento (D9).

**KPI 2 — Forecast de Vendas (derivado do consumo)**

- Deriva do KPI 1: quantifica a correlação amostra processada → faturamento.
- **Targets separados:** faturamento e EBIT são previstos como targets distintos (D2). Não são uma parte única do KPI 2.
- **Escopo da Fase 1 (D3):** recorrentes e não recorrentes ativos, mais churn e variável de mercado.
- **Fora do escopo por ora:** novos clientes e reativados.
- **Recorrente (D5):** compras em ≥6 meses distintos dos últimos 12 **e** última compra há menos de 90 dias (regra E, H4).
- **Fora do forecast de receita:** taxa de conversão de 70% (D4).
- **Cross-check automatizado:** desconta quem já faturou no Protheus, tem pedido pendente ou oportunidade aberta no Zoho CRM, para evitar dupla contagem. O papel das oportunidades >80% do Zoho segue em aberto (H1).
- **Saída padronizada:** previsão pontual + intervalo de incerteza calibrado.

<!-- Slide number: 3 -->

## 2. Arquitetura Existente e Entregáveis

A arquitetura medallion já existe (D7): camadas `bronze_*` e `silver_*` de Protheus, S360 e Zoho no `LakehouseOel`. A camada Gold atual é exclusiva de um agente específico e não será usada.

1. **Pipeline de pré/pós-processamento (sobre Bronze/Silver)**
   - Consome diretamente as camadas Bronze e Silver existentes, sem interferir na Gold do agente atual.
   - Executa joins em SQL (faturamento × amostras) e testes Great Expectations / pytest.
2. **Modelos preditivos no MLflow (Fabric)**
   - Modelos encadeados (KPI 1 → KPI 2) versionados no MLflow nativo.
   - Previsões de Real, Potencial, faturamento, EBIT, faixa de confiança e flags de churn gravadas em tabelas dedicadas de saída do Forecast.
3. **Entrega: protótipos para escolha (H3)**
   - Três alternativas a prototipar e comparar: (a) dashboard HTML + acesso SQL às tabelas de saída; (b) modelo semântico (DirectLake); (c) API/MCP.
   - Critérios: acurácia (backtest) e custo (CU na F8). O cliente escolhe a melhor.
   - A entrega não está decidida. Modelo semântico e MCP deixam de ser premissa fixa.
4. **Governança de acurácia (snapshots + backtesting)**
   - Reconstrução retroativa sobre o histórico desde 2022 (linha de base imediata).
   - Tabela de snapshot mensal congelando previsto vs. realizado (MAPE e MAE por mês, segmento e cliente + convergência semanal).

<!-- Slide number: 4 -->

## 3. Restrição Crítica 1: Proteção do Custo Computacional (FinOps F8)

Como processar ~5 milhões de amostras/ano sem competir com o Agente na capacidade F8.

**Reuso de Bronze/Silver e SQL**

- Reaproveitamento total: leitura direta das camadas Bronze e Silver já existentes no OneLake (zero custo de reingestão).
- Isolamento da Gold atual: não sobrecarrega nem altera a camada Gold dedicada ao agente em operação.
- Joins em SQL (pushdown): cruzamento entre faturamento e amostras feito no SQL Endpoint sobre a Silver/Bronze.

**Modelagem econômica (ML clássico)**

- Foco em algoritmos leves: statsforecast, LightGBM, XGBoost e scikit-learn, em vez de arquiteturas pesadas.
- Matriz custo × acurácia: todo candidato a modelo é avaliado pelo consumo de CUs versus ganho real de MAPE.
- Treino e inferência em batch: execução agendada na madrugada (fora do horário comercial). A janela de CU livre na F8 segue em aberto (§5 de 13).

**Consumo leve (protótipos de entrega)**

- Pré-materialização: nenhuma previsão é calculada ao vivo durante o uso de Power BI ou de agentes.
- Cada alternativa de entrega (H3) lê apenas as tabelas de saída já calculadas. O custo de consulta deve ser quase zero, e isso é medido no protótipo.

<!-- Slide number: 5 -->

## 4. Restrição Crítica 2: Garantia de Acurácia em Produção

Como tratar limitações dos dados reais nas camadas Bronze/Silver e superar a convergência tardia (dia 20).

**Engenharia de atributos do domínio LS**

- Inferência de máquinas paradas/vendidas (limitação S360): como o S360 é só envio, o modelo lê o histórico cru na Bronze/Silver e detecta inatividade pela derivada do horímetro e quebras de coleta. A regra de equipamento ativo segue em descoberta (R3, T05).
- Sazonalidade específica por segmento: parada da cana (nov–mar), safra/safrinha no MT (algodão ~500h/ano, milho, soja), indústria (mensal/bimestral) e locomotiva (semanal).
- Atualização dinâmica de parâmetros: substitui ticket médio (R$ 1.950) e conversão (5%) fixos de out/2022 pelo comportamento faturado real do Protheus na Silver. Ticket e conversão atuais seguem em descoberta (R7).
- Cross-check Zoho + Protheus: elimina dupla contagem no fechamento semanal/mensal.

**Validação científica e qualidade de dados**

- Reconstrução retroativa (backtesting): aplicação da regra atual sobre o histórico desde 2022 para estabelecer o MAPE de referência antes do deploy.
- Acompanhamento de convergência semanal: monitoramento do erro semana a semana para antecipar a previsibilidade antes do dia 20.
- Snapshot mensal imutável: congelamento das previsões emitidas a cada ciclo para auditoria (previsto × realizado).
- Travas com Great Expectations + pytest: bloqueio automático de registros com horímetro inválido, timestamps corrompidos ou chaves órfãs.

<!-- Slide number: 6 -->

## 5. Plano de Execução e Estimativa de Esforço

Prazo estimado na versão anterior: ~21 a 30 dias (integral) ou ~42 a 60 dias úteis / 8 a 12 semanas (4–6h/dia). **A revisar** com o escopo atual (novos e reativados saíram; EBIT virou target próprio; entrega passou para protótipos).

| Fase do Projeto | Entregas e Atividades Principais | Integral | Parcial (4–6h/d) |
| --- | --- | --- | --- |
| Fase 0 — Descoberta e Auditoria | Mapear tabelas nas camadas Bronze e Silver (S360/ERP/Zoho); validar chaves e auditar horímetro. | 3–4 dias | 6–8 dias úteis |
| Fase 1 — Pipeline Pré-Processamento | Conectar às camadas Bronze/Silver existentes; criar joins SQL (faturamento × amostras) e features (sem tocar na Gold atual). | 4–6 dias | 8–12 dias úteis |
| Fase 2 — KPI 1: Consumo | Modelos de previsão Real (horímetro/sazonalidade) e Potencial (% Achieved e benchmark de similares); alertas >20% e churn. | 4–6 dias | 8–12 dias úteis |
| Fase 3 — KPI 2: Vendas e EBIT | Correlação consumo → venda; targets separados de faturamento e EBIT; recorrentes, não recorrentes ativos, churn e variável de mercado; cross-check Zoho/Protheus; previsão semanal/mensal. | 4–6 dias | 8–12 dias úteis |
| Fase 4 — Validação e Snapshots | Reconstrução retroativa (baseline); cálculo de MAPE/MAE; snapshot mensal; testes pytest / Great Expectations. | 3–4 dias | 6–8 dias úteis |
| Fase 5 — Entrega por protótipos e FinOps | Prototipar as alternativas de entrega (H3: dashboard + SQL, modelo semântico, API/MCP) e medir acurácia e custo; o cliente escolhe; auditoria F8 e handoff. | 3–4 dias | 6–8 dias úteis |

Novos e reativados não entram nas fases acima. Ficam para uma etapa posterior.

<!-- Slide number: 7 -->

## 6. Decisões Tomadas e Pendências

**Decisões já tomadas** (detalhe em [13](13_revisao_alinhamento_reuniao_2026-10-21.md) §1)

- D1 — Projeto prevê consumo de amostras e vendas derivadas do consumo. TAT fora.
- D2 — Faturamento e EBIT são targets separados do KPI 2.
- D3 — Novos e reativados fora do escopo por ora.
- D4 — Taxa de conversão de 70% fora do forecast de receita.
- D5 — Recorrente: ≥6 meses distintos dos últimos 12 e última compra <90 dias.
- D6 — % Achieved = realizadas ÷ potencial anual.
- D7 — Medallion já existe; novas camadas só se o escopo exigir.
- D8 — Horímetro é uma leitura por coleta.
- D9 — Amostras avulsas: identificar e limpar no pré-processamento.
- D10 — Potencial sobre a frota conhecida.
- D11 — Classificação de clientes entra como Fase 1b.
- D12 — Acesso ao lakehouse resolvido.

**Hipóteses a validar por protótipo** (detalhe em 13 §2)

- H1 — Papel das oportunidades >80% do Zoho: somam ao forecast ou só descontam no cross-check.
- H2 — O que a receita representa: venda de kit/pacote ou análise processada.
- H3 — Formato de entrega: dashboard + SQL, modelo semântico ou API/MCP.
- H4 — Regra de recorrência com última compra <90 dias: resolvida como E.

**Pendências abertas** (detalhe em 13 §3 e §5)

- Fórmulas do Annual Sample Potential e cobertura das famílias da Calculadora (R1, R2).
- Confiabilidade do equipamento ativo vida útil por família (R3); retorno kit → amostra (R4); campo-chave do equipamento no S360 (R5); recorrência de amostras (R6); ticket médio e conversão atuais (R7).
- Meta numérica de acurácia (MAPE) por KPI e horizonte.
- Cadência exigida: semanal é requisito ou desejável?
- Hierarquia matriz/filial do Zoho para agrupar clientes.
- Janela de CU livre na F8 para agendar pipelines.
