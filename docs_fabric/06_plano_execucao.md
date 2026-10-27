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
- [ ] Validar chaves (CNPJ, ERP ID, ID equipamento, setor/segmento): mapeadas em [14](14_fase0_engenharia_reversa_e_base_de_codigo.md) §2, falta confirmar no perfil de dados.
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
- Modelo de vida útil/abandono de equipamento por período e segmento, para filtrar cadastrados inativos.

### Fase 2 — KPI 1: consumo de amostras
- Features: horímetro, meses/ano, intervalo de coleta, tipo de equipamento, segmento, sazonalidade.
- Modelo de volume por cliente/equipamento/compartimento (Real).
- Modelo de **Potencial** via benchmark de clientes similares e % achieved.
- Sinais de ação: queda >20%, compartimento churn.

### Fase 3 — KPI 2: vendas (faturamento)
- Quantificar a correlação consumo→venda (projeção por amostra).
- Modelar componentes (recorrente, não recorrente ativa, churn; novos e reativados fora do escopo por ora).
- Cross-check Zoho (evitar dupla contagem).
- Forecast semanal + mensal de faturamento e de EBIT (targets separados).

### Fase 4 — Validação (snapshot + reconstrução retroativa)
- Snapshot mensal do forecast × realizado.
- Reconstrução retroativa sobre o histórico do Fabric (linha de base).
- MAPE por mês/segmento/cliente; convergência ao longo do mês.
- Great Expectations / pytest nos pipelines.

### Fase 5 — Entrega e handoff
- Protótipos de entrega (HTML + SQL, semântico, API/MCP) e escolha do cliente; pipeline agendada.
- FinOps: custo × acurácia dos modelos escolhidos.
- Documentação de premissas/limitações e handoff.

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
