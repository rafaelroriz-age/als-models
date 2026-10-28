# Conexão e Consumo no Fabric

> Como o projeto lê Bronze/Silver, grava o Forecast e como o resultado é consumido (Power BI, Data Agent, MCP). Complementa [07_integracao_mcp.md](07_integracao_mcp.md).

## 0. Fase de desenvolvimento (Fase 5b, 28/10/2026): notebooks em lakehouses existentes

Resposta do Caio ([13](13_revisao_alinhamento_reuniao_2026-10-21.md) D13): desenvolver em **notebook**, escolhendo o lakehouse; usar os **lakehouses já existentes**; criar **só tabelas temporárias ou pré-consultas**. Por isso a topologia da §1 (novo `lh_forecast`, tabelas Delta de saída) **não é pré-requisito** nesta fase e fica como alvo de produção a rediscutir (T36).

- **Leitura:** Silver do `LakehouseOel`, somente leitura (parâmetro de lakehouse nos notebooks `notebooks/50_dev`, T30).
- **Pré-consultas:** temp views Spark `v_als_*` (vivem só na sessão do notebook; nome e colunas no contrato da T28).
- **Saída persistente:** arquivos em `Files/als_oilmodel/saida/` (parquet), baixados por `scripts/fabric_run.py`. É o que o dashboard (a) e o semântico (b, modo Import) consomem.
- **Guard:** liberar `CREATE TEMP VIEW`/`createOrReplaceTempView` e fechar `CREATE TABLE/VIEW` permanentes é a T27. `als_dev_*` Delta só com `ALS_FABRIC_DEV=1` e depois da resposta do Caio (T26).
- **Publicação:** o único workspace acessível é `O&L Global - Prod - DA`; cada publicação exige confirmação explícita do usuário (AGENTS.md). Estado em 28/10: 10 notebooks e nenhum `als_*` no workspace; `Files/als_oilmodel/` não existe.

## 1. Topologia (isolamento da Gold do agente atual; alvo de produção, não da Fase 5b)

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

As formas abaixo são **hipóteses a prototipar**; o cliente escolhe (ver [13](13_revisao_alinhamento_reuniao_2026-10-21.md)). Inclui-se o acesso direto por SQL às tabelas Delta de `lh_forecast` e um dashboard HTML.

1. **Modelo semântico DirectLake** sobre as tabelas de saída (DAX simples). Base do Power BI.
2. **Fabric Data Agent** nativo sobre o semântico — perguntas em linguagem natural, menor manutenção.
3. **MCP fino próprio** (Python/FastMCP, para contrato estável): tools `get_forecast_consumo`, `get_forecast_vendas`, `get_backtest_mape`, com SQL parametrizado somente-leitura no SQL endpoint de `lh_forecast` (ou DAX no semântico). Retorno: `{valor, p10, p90, data_ref, snapshot}`.
   - Alternativas: `Fabric-Analytics-MCP` (comunidade, DAX) ou Data Agent como ponte.
   - **A verificar (Fase 0/5):** existência de MCP oficial Microsoft atual para semantic models que dispense servidor próprio.

**Segurança:** SP com leitura só em `lh_forecast`; MCP nunca lê Bronze/Silver; segredos em cofre; log de chamadas.
**FinOps:** previsões pré-materializadas em batch; consumo lê só resultados prontos; cache por `snapshot`; medir CU na F8 no handoff.

## 4. Executar notebooks pela API (sem a porta 1433): `scripts/fabric_run.py` (T25)

Com o SQL endpoint (1433) bloqueado, o código roda **dentro do Fabric** e só a API (443) sai da máquina.

```text
python scripts/fabric_run.py als_00_perfil_qualidade            # executa e baixa Files/als_oilmodel/perfil/ → data/perfil/
python scripts/fabric_run.py als_00_perfil_qualidade --publicar # antes roda fabric_deploy.py --aplicar (publica em produção: só com confirmação)
ALS_AUTH=device python scripts/fabric_run.py als_00_...         # login por device code: abrir o link no celular e digitar o código
```

| Passo | Chamada | Observação |
|---|---|---|
| Localizar | `GET /workspaces`, `/lakehouses`, `/notebooks` | workspace padrão `O&L Global - Prod - DA` (`ALS_WORKSPACE` ou `--workspace`); lakehouse por nome, sem diferenciar maiúsculas |
| Barreira | `POST /notebooks/{id}/getDefinition?format=ipynb` (202 → `Location` → `/result`) | recusa nome sem `als_` antes de qualquer chamada, e definição publicada que `fabric_guard.violacoes` bloqueie |
| Executar | `POST /items/{id}/jobs/instances?jobType=RunNotebook` → 202 + `Location` | consulta o `Location` a cada `Retry-After` (máx. 30 s) até `Completed/Failed/Cancelled/Deduped`; `--timeout` (padrão 3600 s) devolve `Timeout`; imprime status, tempo e `failureReason`; código de saída 0 só com `Completed` |
| Baixar | OneLake DFS `GET ?resource=filesystem&recursive=true&directory=<lh>/Files/als_oilmodel/<pasta>` + `GET` por arquivo | só leitura; pasta por notebook (`perfil`, `planilhas`) ou `--pasta`; segue `x-ms-continuation`; 404 = nada a baixar; recusa caminho que saia de `data/` |

Autenticação: o padrão é o `InteractiveBrowserCredential` em cache de `src/pipeline/fabric.py`. `ALS_AUTH=device` usa `DeviceCodeCredential` com o mesmo cache (`als_oilmodel`) e o mesmo `~/.als_oilmodel/auth_record.json`: o token salvo é reaproveitado e o código só aparece quando o cache expira. Testes: `tests/test_fabric_run.py`, 17 casos com sessão `requests` falsa (rotas, operação longa, barreira, falha/timeout, HTTP 403, paginação, 404, caminho fora de `data/`, device code).

**Validação real (27/10/2026, rede do usuário, porta 443):**

- Login em cache sem interação: credencial pronta em 3,1 s; workspace e `LakehouseOeL` resolvidos, localização completa em ~10 s.
- **O notebook de perfil não está publicado:** o workspace tem 10 notebooks e nenhum `als_*`, e `Files/als_oilmodel/` não existe no lakehouse (o OneLake devolve 404). O executor respondeu `notebook não publicado: als_00_perfil_qualidade` e o download tratou a pasta ausente sem erro (17 s no total, só leitura). `python scripts/fabric_run.py perfil` foi recusado sem autenticar.
- Execução do job e tempo do perfil: **pendentes**. Publicar (`python scripts/fabric_deploy.py --aplicar --workspace "O&L Global - Prod - DA"`) cria os 3 notebooks `als_*` e grava o wheel em `Files/als_oilmodel/wheels/` do workspace de produção. Pelo AGENTS.md isso exige confirmação explícita, então não foi feito nesta tarefa. Depois de publicar, rodar `python scripts/fabric_run.py als_00_perfil_qualidade` e registrar aqui o status e o tempo (caminho da T02).

## 5. Barreira de escrita: `scripts/fabric_guard.py` (T27)

O guard inspeciona o texto de comandos e arquivos (hook `.claude/hooks/fabric_guard_hook.py`, `fabric_deploy.py` e `fabric_run.py`). Comportamento desde a T27 (testes novos em `tests/test_fabric_guard.py`, 58 casos no arquivo):

| Texto | Resultado |
|---|---|
| `CREATE [OR REPLACE] [GLOBAL] TEMP[ORARY] VIEW`, `createOrReplaceTempView`, `createTempView`, `createOrReplaceGlobalTempView` | **livre** (a view some com a sessão) |
| `CREATE [OR REPLACE] [EXTERNAL] TABLE/VIEW` permanentes | bloqueado |
| DDL de schema/database (create, drop, alter) e `CREATE OR REPLACE` de outros objetos (ex.: função) | bloqueado |
| `INSERT INTO`, `UPDATE … SET`, `DELETE FROM`, `DROP/ALTER TABLE/VIEW`, `TRUNCATE`, `MERGE INTO`, `saveAsTable`, `insertInto` | bloqueado |
| Operação Delta de escrita e gravação em `/Tables/` | bloqueado, mesmo para `als_dev_*` |

**Liberações (variáveis de ambiente da sessão, definidas por uma pessoa; valem só com o valor `1`):**

- `ALS_FABRIC_ESCRITA=1`: libera tudo, como antes.
- `ALS_FABRIC_DEV=1`: libera criar, gravar e apagar **apenas** tabelas/views cujo nome (último trecho de `schema.nome`, sem aspas, sem diferenciar maiúsculas) começa com `als_dev_`, nos padrões que têm nome: `CREATE TABLE/VIEW`, `INSERT INTO`, `UPDATE`, `DELETE FROM`, `DROP/ALTER/TRUNCATE`, `MERGE INTO`, `saveAsTable`, `insertInto`. Num texto com várias instruções, uma só fora do prefixo mantém o bloqueio. É independente de `ALS_FABRIC_ESCRITA`: uma não ativa a outra.

**Limites (o guard só lê texto):**

- Nome montado em tempo de execução (variável) não é verificável e continua bloqueado; `f'als_dev_{x}'` passa porque o prefixo é literal.
- Não vê escrita por outro caminho (API REST direta, outra linguagem, SQL montado em string e executado depois); a revisão humana antes de publicar notebook continua necessária.
- `ALS_FABRIC_DEV` não impede o uso de um nome `als_dev_x` que já exista com dado de outra pessoa: usar o prefixo só em tabelas criadas por nós e limpar ao fim.
- Gravação em `Files/als_oilmodel/` segue livre; `/Tables/` segue bloqueado, também para `als_dev_`.
