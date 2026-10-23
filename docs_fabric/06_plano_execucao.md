# Plano de Execução

> Abordagem proposta, ferramentas e estimativa de esforço para o Forecast de Amostras e Vendas, no ecossistema Azure (Microsoft Fabric).

## Abordagem proposta (resumo)

Dois modelos encadeados, atrás de uma camada de dados medallion no lakehouse:

1. **Consumo de amostras** — previsão de volume por cliente/equipamento/compartimento, a partir de horas trabalhadas (horímetro), meses/ano e intervalos de coleta, com sazonalidade por segmento. Entrega as visões **Real** e **Potencial**.
2. **Vendas** — previsão de faturamento **derivada do consumo**, composta pelos componentes da planilha Forecast (recorrente, não recorrente ativa, novos, reativados, churn, variável de mercado) e com cross-check Zoho.

Ambos com **intervalos de incerteza**, validados por **snapshot mensal + reconstrução retroativa**, e entregues como **modelo semântico do Fabric (DirectLake) e/ou API/endpoint**.

## Arquitetura no Fabric

```
S360 (espelhado) ─┐
ERP/Proteus ───────┼─► Lakehouse OneLake ─► Bronze ─► Silver ─► Gold ─► Modelo (MLflow) ─► Modelo Semântico / API
Zoho CRM ──────────┘    (Delta)              (bruto)   (limpo)   (fato/dim)                    (Power BI / agente)
```

## Ferramentas / bibliotecas

| Preocupação | Escolha | Por quê |
|-------------|---------|---------|
| Ingestão | Espelhamento S360 + conectores/pipelines do Fabric | espelhamento nativo; sem pipeline de cópia |
| Armazenamento | OneLake Lakehouse (tabelas Delta) | camada única, DirectLake |
| Arquitetura | Medallion (bronze → silver → gold) | dados brutos → limpos → pronto para consumo |
| Transformação | Spark (PySpark) + SQL (analytics endpoint) | joins faturamento × amostras no pré-processamento |
| Séries temporais (consumo/vendas) | `statsforecast` / `prophet` / `scikit-learn` + `XGBoost`/`LightGBM` | ML clássico de menor custo (FinOps) |
| Sazonalidade/features | pandas, numpy, `holidays` (feriados BR) | sazonalidade por segmento |
| Rastreamento/registro | MLflow (nativo no Fabric) | experimentos e registro de modelos |
| Validação de dados | Great Expectations + pytest | parte da metodologia |
| Entrega | Modelo semântico (DirectLake) e/ou API/endpoint | consumível pelo Power BI / agente |
| Orquestração | Data pipelines do Fabric (agendamento) | automação |

## Fases e tarefas

### Fase 0 — Descoberta e auditoria de dados (antes de comprometer)
- Confirmar espelhamento do S360 e conectores ERP/Zoho no lakehouse.
- Mapear schemas/tabelas; validar chaves (CNPJ, ERP ID, ID equipamento, setor/segmento).
- Revisar as 3 planilhas + dicionário de dados; levantar pontos em aberto.
- Relatório de qualidade (missingness, outliers, sanidade de horímetro/timestamps).
- **Saída:** mapa de dados + perguntas resolvidas.

### Fase 1 — Pipeline de pré-processamento (sobre Bronze/Silver existentes)
- Medallion já existe: **não** recriar ingestão nem alterar a Gold do agente atual.
- Criar `lh_forecast` com shortcuts somente leitura para Bronze/Silver (ver [09](09_conexao_e_consumo_fabric.md)).
- Limpeza complementar, joins em SQL (faturamento × amostras) e tabelas de features; Great Expectations + pytest.

### Fase 2 — KPI 1: consumo de amostras
- Features: horímetro, meses/ano, intervalo de coleta, tipo de equipamento, segmento, sazonalidade.
- Modelo de volume por cliente/equipamento/compartimento (Real).
- Modelo de **Potencial** via benchmark de clientes similares e % achieved.
- Sinais de ação: queda >20%, compartimento churn.

### Fase 3 — KPI 2: vendas (faturamento)
- Quantificar a correlação consumo→venda (projeção por amostra).
- Modelar componentes (recorrente, não recorrente, novos, reativados, churn).
- Cross-check Zoho (evitar dupla contagem).
- Forecast semanal + mensal mirando EBIT.

### Fase 4 — Validação (snapshot + reconstrução retroativa)
- Snapshot mensal do forecast × realizado.
- Reconstrução retroativa sobre o histórico do Fabric (linha de base).
- MAPE por mês/segmento/cliente; convergência ao longo do mês.
- Great Expectations / pytest nos pipelines.

### Fase 5 — Entrega e handoff
- Modelo semântico (DirectLake) e/ou endpoint; pipeline agendada.
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

**Premissas:**
- Acesso ao lakehouse (S360 espelhado, ERP, Zoho) liberado no início.
- Histórico de amostras desde 2022 e faturamento disponíveis; ≥ 12 meses para backtesting.
- Dicionário de dados entregue; chave de equipamento confirmada.
- Capacidade F8 disponível sem competir com o agente.
- Integração final é modelo semântico e/ou endpoint simples (request/response).

**Riscos que elevam o prazo:**
- Descoberta de dados difícil (sem dicionário, chaves ambíguas, horímetro sujo).
- Histórico fino ou sazonalidade mal documentada por segmento.
- Entrega exigir API real-time em vez de semântico.
- FinOps: necessidade de otimizar/reduzir modelo por custo.

## Perguntas para o cliente

1. Annual Sample Potential vem da calculadora ou do benchmark de similares? Quais parâmetros?
2. Ticket médio e conversão atuais (vs. R$ 1.950 / 5% de 2022)?
3. Regra do recorrente confirmada (≥6 meses/12, <90 dias, sem a taxa de 70%)?
4. Composição do forecast de vendas continua a mesma?
5. Existe histórico de forecasts salvos para medir acurácia retroativa?
6. Acesso ao lakehouse (S360, ERP, Zoho) — quais schemas/tabelas?
7. Chave de equipamento (S360) para o join — qual campo exato?
8. Sazonalidade por segmento: há curva/dados além de "meses trabalhados/ano"?
9. Entrega final: modelo semântico, API/endpoint, ou ambos?
10. Capacidade F8: há headroom de CU para os pipelines/modelo?
