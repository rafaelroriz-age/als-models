# Conexão e Consumo no Fabric

> Como o projeto lê Bronze/Silver, grava o Forecast e como o resultado é consumido (Power BI, Data Agent, MCP). Complementa [07_integracao_mcp.md](07_integracao_mcp.md).

## 1. Topologia (isolamento da Gold do agente atual)

- Novo lakehouse **`lh_forecast`** (idealmente em workspace próprio, mesma capacidade F8).
- Bronze/Silver (S360, Protheus, Zoho) entram por **OneLake Shortcuts** somente leitura: zero cópia, sem tocar na Gold existente.
- Tabelas Delta de saída em `lh_forecast`:
  - `fct_forecast_consumo` — cliente → equipamento → compartimento; real/potencial; p50/p10/p90; flags queda >20% e churn.
  - `fct_forecast_vendas` — 6 componentes + incerteza.
  - `snapshot_mensal` — previsões congeladas.
  - `backtest_metrics` — MAPE/MAE por mês/segmento/cliente.
  - `dq_resultados` — resultados do Great Expectations.

## 2. Como conectar

| Contexto | Caminho | Autenticação |
|----------|---------|--------------|
| Produção (pipeline/notebooks no Fabric) | Spark lê shortcuts/tabelas (`spark.read.table`), joins em Spark SQL, grava Delta em `lh_forecast`; Data Pipeline agendado fora do pico | identidade do workspace |
| Desenvolvimento local (VS Code) | (1) SQL analytics endpoint via `pyodbc` + ODBC Driver 18 (somente leitura; exploração/Fase 0). (2) OneLake `abfss://<ws>@onelake.dfs.fabric.microsoft.com/<lh>.Lakehouse/Tables/<tabela>` com `deltalake` / `azure-storage-file-datalake` | Entra ID: interativo (dev) / service principal (CI) via `azure-identity` |
| Consumo | seção 3 | service principal de leitura |

**Pré-requisitos (TI):** leitura em Bronze/Silver; tenant setting "Service principals can use Fabric APIs"; SP com role mínima apenas no workspace do forecast; janela de CU da F8.

## 3. Como consumir

Contrato: `entidade, data_ref, período → previsão + incerteza`.

1. **Modelo semântico DirectLake** sobre as tabelas de saída (DAX simples). Base do Power BI.
2. **Fabric Data Agent** nativo sobre o semântico — perguntas em linguagem natural, menor manutenção.
3. **MCP fino próprio** (Python/FastMCP, recomendado para contrato estável): tools `get_forecast_consumo`, `get_forecast_vendas`, `get_backtest_mape`, com SQL parametrizado somente-leitura no SQL endpoint de `lh_forecast` (ou DAX no semântico). Retorno: `{valor, p10, p90, data_ref, snapshot}`.
   - Alternativas: `Fabric-Analytics-MCP` (comunidade, DAX) ou Data Agent como ponte.
   - **A verificar (Fase 0/5):** existência de MCP oficial Microsoft atual para semantic models que dispense servidor próprio.

**Segurança:** SP com leitura só em `lh_forecast`; MCP nunca lê Bronze/Silver; segredos em cofre; log de chamadas.
**FinOps:** previsões pré-materializadas em batch; consumo lê só resultados prontos; cache por `snapshot`; medir CU na F8 no handoff.
