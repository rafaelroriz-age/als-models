<!-- Slide number: 1 -->

PROJETO DE CIÊNCIA DE DADOS — ALS / LS
Forecast de Consumo de Amostras e Vendas no Microsoft Fabric
Plano de Execução sobre as Camadas Bronze/Silver Existentes, FinOps (Capacidade F8) e Acurácia em Produção
Reunião de Alinhamento e Validação Técnica  |  Ecossistema Azure / OneLake

<!-- Slide number: 2 -->
1. Visão Geral e Escopo da Fase 1
Mudança de paradigma: projetar vendas a partir do consumo real dos equipamentos (~5 milhões de amostras/ano)
KPI 1 — Forecast de Consumo de Amostras
• Ordem de dependência: Consumo puxa a venda (horímetro -> coleta -> pedido).
• Visão Real: Baseada em horas trabalhadas, meses/ano e intervalo por compartimento (motor 250h, hidráulico 500h, arrefecimento 1000h; preventiva vs. meia preventiva).
• Visão Potencial: Cobertura (% Achieved = monitorados vs. cadastrados) + benchmark de clientes similares do mesmo segmento.
• Granularidade: Cliente -> Equipamento -> Compartimento (agregável por setor/segmento).
• Sinais de Ação: Queda >20% no volume do cliente e 'compartimento churn'.
KPI 2 — Forecast de Vendas (Predict Revenue)
• Derivado do Consumo: Quantifica a correlação amostra processada -> faturamento.
• Foco Executivo: Atualização semanal e mensal mirando o EBIT (não apenas preço).
• Composição (6 blocos): Recorrente (>=6m/12 e <90d sem redutor de 70%), Não Recorrente Ativa, Novos, Reativados (+1 ano), Churn (>6m) e Variável de Mercado.
• Cross-Check Automatizado: Desconta quem já faturou no Protheus, tem pedido pendente ou oportunidade aberta no Zoho CRM (evita dupla contagem).
• Saída Padronizada: Previsão pontual + intervalo de incerteza calibrado.

<!-- Slide number: 3 -->
2. Arquitetura Existente e Entregáveis em Produção
A Arquitetura Medallion já existe (a camada Gold atual é exclusiva de um agente específico; consumiremos Bronze e Silver)
1. Pipeline de Pré/Pós-Processamento (sobre Bronze/Silver)
• Consome diretamente as camadas Bronze e Silver já existentes (S360, Protheus e Zoho), sem interferir na camada Gold do agente atual.
• Executa joins em SQL (faturamento x amostras) e testes Great Expectations / pytest.
2. Modelos Preditivos no MLflow (Fabric)
• Modelos encadeados (KPI 1 -> KPI 2) versionados no MLflow nativo.
• Geração de previsão Real, Potencial, EBIT, faixa de confiança e flags de churn gravados em tabelas dedicadas de saída do Forecast.
3. Modelo Semântico (DirectLake) e/ou API + Ponte MCP
• Modelo Semântico em DirectLake e/ou API conectados às tabelas de saída do Forecast.
• Integração via MCP (Fabric-Analytics-MCP / Data Agent) para consulta imediata pelo Power BI e agentes sem tocar na Gold antiga.
4. Governança de Acurácia (Snapshots + Backtesting)
• Reconstrução retroativa sobre o histórico desde 2022 (linha de base imediata).
• Tabela de Snapshot Mensal congelando previsto vs. realizado (MAPE e MAE por mês, segmento e cliente + convergência semanal).

<!-- Slide number: 4 -->
3. Restrição Crítica 1: Proteção do Custo Computacional (FinOps F8)
Como processar ~5 milhões de amostras/ano sem competir com o Agente na capacidade F8
Reuso de Bronze/Silver & SQL
• Reaproveitamento Total: Leitura direta das camadas Bronze e Silver já existentes no OneLake (zero custo de reingestão).
• Isolamento da Gold Atual: Não sobrecarrega nem altera a camada Gold dedicada ao agente em operação.
• Joins em SQL (Pushdown): Cruzamento entre faturamento e amostras feito no SQL Endpoint sobre a Silver/Bronze.
Modelagem Econômica (ML Clássico)
• Foco em Algoritmos Leves: Uso de statsforecast, LightGBM, XGBoost e scikit-learn em vez de arquiteturas pesadas.
• Matriz Custo x Acurácia: Todo candidato a modelo será avaliado pelo consumo de CUs versus ganho real de MAPE.
• Treino e Inferência Batch: Execução agendada na madrugada (fora do horário comercial).
Consumo Leve (DirectLake + MCP)
• Pré-Materialização: Nenhuma previsão é calculada 'ao vivo' durante o uso do Power BI ou de agentes.
• DirectLake: Lê as tabelas de saída do Forecast diretamente do OneLake sem carga de importação.
• Cache no MCP: Consultas via MCP leem apenas os resultados pré-calculados do Forecast (custo de CU quase zero).

<!-- Slide number: 5 -->
4. Restrição Crítica 2: Garantia de Acurácia em Produção
Como tratar limitações de dados reais nas camadas Bronze/Silver e superar a convergência tardia (dia 20)
Engenharia de Atributos do Domínio LS
• Inferência de Máquinas Paradas/Vendidas (Limitação S360): Como o S360 é só envio, o modelo lê o histórico cru na Bronze/Silver e detecta inatividade pela derivada do horímetro e quebras de coleta.
• Sazonalidade Específica por Segmento: Incorpora parada da Cana (nov-mar), safra/safrinha no MT (algodão ~500h/ano, milho, soja), Indústria (mensal/bimestral) e Locomotiva (semanal).
• Atualização Dinâmica de Parâmetros: Substitui ticket médio (R$ 1.950) e conversão (5%) fixos de out/2022 pelo comportamento faturado real do ERP Protheus na Silver.
• Cross-Check Zoho + Protheus: Elimina dupla contagem no fechamento semanal/mensal.
Validação Científica e Qualidade de Dados
• Reconstrução Retroativa (Backtesting): Aplicação da regra atual sobre o histórico desde 2022 para estabelecer o MAPE de referência antes do deploy.
• Acompanhamento de Convergência Semanal: Monitoramento do erro semana a semana para antecipar a previsibilidade antes do dia 20.
• Snapshot Mensal Imutável: Congelamento das previsões emitidas a cada ciclo para auditoria transparente (Previsto x Realizado).
• Travas com Great Expectations + pytest: Bloqueio automático de registros com horímetro inválido, timestamps corrompidos ou chaves órfãs.

<!-- Slide number: 6 -->
5. Plano de Execução e Estimativa de Esforço
Prazo total estimado: ~21 a 30 dias (integral) ou ~42 a 60 dias úteis / 8 a 12 semanas (4-6h/dia)
| Fase do Projeto | Entregas e Atividades Principais | Integral | Parcial (4-6h/d) |
| --- | --- | --- | --- |
| Fase 0 — Descoberta e Auditoria | Mapear tabelas nas camadas Bronze e Silver existentes (S360/ERP/Zoho); validar chaves e auditar horímetro. | 3–4 dias | 6–8 dias úteis |
| Fase 1 — Pipeline Pré-Processamento | Conectar às camadas Bronze/Silver existentes; criar joins SQL (faturamento x amostras) e features (sem tocar na Gold atual). | 4–6 dias | 8–12 dias úteis |
| Fase 2 — KPI 1: Consumo | Modelos de previsão Real (horímetro/sazonalidade) e Potencial (benchmark similares); alertas >20% e churn. | 4–6 dias | 8–12 dias úteis |
| Fase 3 — KPI 2: Vendas / EBIT | Correlação consumo->venda; 6 componentes do Forecast; cross-check Zoho/Protheus; previsão semanal/mensal. | 4–6 dias | 8–12 dias úteis |
| Fase 4 — Validação e Snapshots | Reconstrução retroativa (baseline); cálculo de MAPE/MAE; Snapshot Mensal; testes pytest / Great Expectations. | 3–4 dias | 6–8 dias úteis |
| Fase 5 — Entrega, FinOps e MCP | Publicação do Modelo Semântico (DirectLake) / API sobre as saídas do Forecast; integração MCP; auditoria F8 e handoff. | 3–4 dias | 6–8 dias úteis |

<!-- Slide number: 7 -->
6. Pauta de Validação para Destravar a Fase 0 Hoje
Confirmações necessárias com Negócio (Bahia / Keli) e TI/Dados
Bloco A — Acesso às Camadas Bronze/Silver (TI / Dados)
• 1. Liberação de Leitura (Bronze e Silver): Liberar acesso às camadas Bronze e Silver já existentes (S360, Protheus e Zoho) para o usuário Rafael Roriz, mantendo a camada Gold atual isolada para o agente específico.
• 2. Mapeamento no Dicionário de Dados: Confirmar os nomes exatos das tabelas nas camadas Bronze e Silver (preenchimento das células em amarelo).
• 3. Chave de Equipamento (S360): Qual é o campo exato na Bronze/Silver do S360 que faz o join com a Calculadora de Amostras?
• 4. Janela da Capacidade F8: Qual o horário de menor carga do Agente atual para agendarmos a nossa pipeline de pré-processamento e inferência?
Bloco B — Regras de Negócio e Entregável (Bahia / Keli)
• 5. Origem do Annual Sample Potential: No Customer Status 2026 está colado como valor fixo — vem da Calculadora ou de benchmark de similares? Quais parâmetros?
• 6. Ticket Médio e Conversão: Atualização dos parâmetros de out/2022 (R$ 1.950 e 5%) ou cálculo dinâmico direto pelos dados do ERP na Silver?
• 7. Regra de Recorrência e Histórico: Confirmada a regra (>=6m/12 e <90d, sem os 70%)? Existem forecasts anteriores salvos para compararmos no backtesting?
• 8. Aprovação do Entregável: Confirmar Modelo Semântico (DirectLake) e/ou API sobre as tabelas de saída do Forecast + integração via MCP.