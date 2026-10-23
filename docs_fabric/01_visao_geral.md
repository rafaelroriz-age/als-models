# Visão Geral do Projeto

## Resumo em uma linha

Construir um modelo de previsão para a área comercial — **consumo de amostras** e **faturamento (vendas) derivado do consumo** — entregue como modelo semântico no Fabric ou API/endpoint, treinado e servido no ecossistema Azure (Microsoft Fabric).

## Os dois KPIs (em ordem de dependência)

| KPI | Definição | Referência |
|-----|-----------|------------|
| 1. Consumo de amostras | Volume de amostras (análises de óleo) que cada cliente/equipamento vai gerar em um período | Duas visões: Real e Potencial |
| 2. Vendas | Faturamento previsto (predict revenue), derivado do consumo | Idealmente semanal, mira o EBIT |

## Contexto de negócio

- **Consumo puxa a venda**: o pedido de compra nasce do consumo do equipamento (horas trabalhadas → necessidade de coleta de óleo). A direção quer projetar **pelo consumo**, não pela compra.
- **Limitação-chave**: a integração S360 é só de envio, sem retorno — não há feedback automático se a máquina foi vendida, parou ou mudou de área. O modelo infere pelo histórico do equipamento.
- **Volume**: ~5 milhões de amostras/ano; base no Power BI desde 2022. Cálculos ao vivo são pesados → mover a inteligência para modelo/pipeline.

## Lógica de negócio (ponto de partida)

O projeto não começa do zero: três planilhas já carregam a regra de negócio e servem de referência.

1. **Calculadora de amostras** — amostras/ano por tipo de equipamento, a partir de horas trabalhadas (horímetro), meses/ano e intervalo de coleta por compartimento.
2. **Customer Status 2026** — base de clientes (2.388; 1.479 ativos; 233 recorrentes), cruzando venda × amostra × equipamento × potencial.
3. **Forecast (Keli/Diego)** — receita mensal estimada por componente (recorrente, não recorrente ativa, novos, reativados, churn, variável de mercado).

## Arquitetura alvo (Azure / Microsoft Fabric)

```
S360 (LIMS, espelhado) ─┐
ERP / Proteus (faturamento) ─┼─► Lakehouse (OneLake) ─► Camada Silver/Gold ─► Modelo ─► Modelo Semântico (DirectLake) ou API
Zoho CRM (oportunidades) ─┘        (medallion, Delta)     (joins/features)   (MLflow)          (consumo no Power BI / agente)
```

- **Ingestão**: espelhamento do S360 (botão nativo do Fabric) + conectores/pipelines para ERP e Zoho.
- **Armazenamento/computação**: Lakehouse no OneLake (tabelas Delta, arquitetura medallion bronze→silver→gold).
- **Modelagem**: notebooks Spark para treino/teste; MLflow para rastreamento e registro.
- **Entrega**: modelo semântico do Fabric (DirectLake) para consumo no Power BI, e/ou API/endpoint para consulta sob demanda.
- **FinOps**: capacidade F8 compartilhada com o agente — preferir ML clássico, mensurar custo × acurácia.

## Forma do entregável

- **Modelo consumível pelo ambiente** (modelo semântico ou API/endpoint) — não um notebook; notebook é só para testes.
- Pipeline própria com pré e pós-processamento; joins (faturamento × amostras) no pré-processamento (SQL).
- Transparência sobre ferramentas e metodologia.
