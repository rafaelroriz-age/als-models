# Conexão e Consumo no Fabric

> Como o projeto lê Bronze/Silver, grava o Forecast e como o resultado é consumido (Power BI, Data Agent, MCP). Complementa [07_integracao_mcp.md](07_integracao_mcp.md).

## 0. Fase de desenvolvimento (Fase 5b, 28/10/2026): notebooks em lakehouses existentes

Resposta do Caio ([13](13_revisao_alinhamento_reuniao_2026-10-21.md) D13): desenvolver em **notebook**, escolhendo o lakehouse; usar os **lakehouses já existentes**; criar **só tabelas temporárias ou pré-consultas**. Por isso a topologia da §1 (novo `lh_forecast`, tabelas Delta de saída) **não é pré-requisito** nesta fase e fica como alvo de produção a rediscutir (T36).

- **Leitura:** Silver do `LakehouseOel`, somente leitura (parâmetro de lakehouse nos notebooks `notebooks/50_dev`, T30; fluxo na §6).
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
| Baixar | OneLake DFS `GET ?resource=filesystem&recursive=true&directory=<lh>/Files/als_oilmodel/<pasta>` + `GET` por arquivo | só leitura; pasta por notebook (`perfil`, `planilhas`; nos `als_*` descobertos por convenção, `PASTA_FABRIC` ou `saida`, §6) ou `--pasta`; segue `x-ms-continuation`; 404 = nada a baixar; recusa caminho que saia de `data/` |

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

## 6. Fluxo de desenvolvimento: `notebooks/50_dev` (T30, 28/10/2026)

Implementa a §0: notebooks `als_*` que leem o lakehouse escolhido só com SELECT, montam as pré-consultas como temp views e gravam as saídas do contrato da T28 em `Files/als_oilmodel/saida/`. **Nada foi publicado**: validado só em modo simulação e em testes locais.

```text
python scripts/fabric_deploy.py                                    # simulação: dist/fabric/*.ipynb, nada sai da máquina
python scripts/fabric_deploy.py --notebooks als_50_pre_consultas   # simula só um notebook
python scripts/fabric_deploy.py --aplicar --workspace "<nome>"     # publica (produção: só com confirmação explícita, T31)
python scripts/fabric_run.py als_50_pre_consultas                  # executa e baixa Files/als_oilmodel/saida/ → data/saida/
python scripts/fabric_run.py als_50_pre_consultas --param lakehouse=OutroLH --param horizonte=6
```

| Notebook | Faz | Grava (Files do lakehouse padrão) |
|---|---|---|
| `als_50_pre_consultas` (`notebooks/50_dev/als_50_pre_consultas.py`) | temp views `v_als_src_amostra`, `_compartimento`, `_equipamento`, `_cliente`, `_zoho_accounts` (projeção das tabelas de origem) → `v_als_amostras_mes` (cliente S360 × equipamento × mês, regras de data/exclusão da T14, sem avulsas) → séries mensais por segmento, cliente (ponte S360 → Zoho da T14) e equipamento → `v_als_forecast_consumo`, `v_als_pct_achieved`, `v_als_alertas` | `saida/forecast_consumo.parquet`, `pct_achieved.parquet`, `alertas.parquet` (só as aprovadas no G4) e `relatorio_dev.json` (gates); falha o job se alguma saída for reprovada |
| `als_51_views_saida` | recarrega os parquets de `saida/` como temp views `v_als_*` numa sessão nova e roda `validar_todas` (G4/G5) | `saida/relatorio_views.json` |

**Parâmetros** (célula `# %% [parameters]` do .py, que o deploy marca com a tag `parameters` do Fabric; local: variáveis de ambiente): `lakehouse` (padrão `LakehouseOel`, `ALS_LAKEHOUSE`; só identificador simples, vai qualificado como `` `lakehouse`.schema.tabela ``), `data_corte` (vazio = 1º dia do mês corrente), `horizonte` (1–12, padrão 12), `meses_historico` (padrão 36), `base_alerta` (`ano_anterior`, `mm3`, `mm12`). Origem: S360 em `bronze_s360` (no `LakehouseOel` a S360 só existe na Bronze, como na T14) e Zoho em `silver_zoho`; `sql_fontes(lh, schemas)` aceita outros schemas. O `lakehouse` do parâmetro é a **origem da leitura**; as saídas vão para o Files do lakehouse **anexado no deploy** (`--lakehouse` do `fabric_deploy.py`), que é o mesmo de onde o `fabric_run.py` baixa.

**Conteúdo das saídas (versão de desenvolvimento, `src/pipeline/dev.py`):** forecast = baseline ingênuo sazonal (`p50 = y(t−12)`; série com menos de 12 meses repete o último valor), `p10/p90 = p50 +` quantis 10/90 dos resíduos sazonais da própria entidade (truncado em 0), `versao_modelo = ingenuo_sazonal_dev+<hash dos dados>`. O modelo escolhido entra na T15. Potencial (T16), `porte`, churn de compartimento (RN-06, depende de horímetro), `forecast_vendas` e `backtest_metricas` ficam de fora: colunas anuláveis saem vazias e as duas últimas saídas não são geradas (o `als_51` acusa `saida_presente` no G4). Alertas: só queda > 20% do cliente no último mês fechado (mês sem coleta não alerta, RN-05).

**Registro por convenção (`fabric_deploy.py` e `fabric_run.py`):**

- `descobrir_notebooks()` = os 3 legados de `NOTEBOOKS` (nomes fixos, sem mudança) + todo `notebooks/**/als_*.py`, publicado com o nome do arquivo; nome repetido é erro. `--notebooks` filtra; nome sem `als_` ou bloqueado pelo guard é recusado antes de gerar o .ipynb.
- Células: linhas `# %%` separam células e `# %% [parameters]` vira a célula de parâmetros; .py sem marcador continua numa célula única (legados idênticos ao que era gerado antes).
- Pasta baixada pelo `fabric_run.py`: `SAIDAS` para os legados (`perfil`, `planilhas`; `als_40` sem pasta, como antes); para os descobertos, a constante `PASTA_FABRIC = "..."` do .py (lida por AST) ou `saida`.
- `--param chave=valor` (repetível) vai no corpo do job (`executionData.parameters`, tipo `string`); sem `--param` o POST segue sem corpo, como antes. O notebook converte os numéricos com `int()`.
- Workspace e lakehouse por argumento ou ambiente: `ALS_WORKSPACE` (deploy: sem padrão, continua obrigatório com `--aplicar`; run: padrão `O&L Global - Prod - DA`) e `ALS_LAKEHOUSE` (padrão `LakehouseOel` nos dois).

**Garantias verificadas:** os 5 notebooks registrados passam no guard sem `ALS_FABRIC_ESCRITA`/`ALS_FABRIC_DEV`; os de `50_dev` não contêm `saveAsTable` nem `/Tables/` e só criam objetos por `createOrReplaceTempView`; as consultas são todas `SELECT`. Simulação de 28/10: `python scripts/fabric_deploy.py` gerou `dist/fabric/` com `als_00_perfil_qualidade`, `als_01_engenharia_reversa_planilhas`, `als_40_backtest_baselines`, `als_50_pre_consultas` e `als_51_views_saida` (o `als_50` com 6 células de código, uma marcada `parameters`). Num conjunto sintético (3 clientes S360, 2 entidades Zoho, 4 equipamentos, 36 meses) o pipeline gerou 270 linhas de série, 390 de `forecast_consumo` (h = 12), 10 de `pct_achieved` e 1 alerta, todas aprovadas no G4.

**Testes:** `tests/test_dev.py` (9 casos: lakehouse por parâmetro/ambiente/padrão e recusa de nome inválido, SQL só leitura e qualificado, janela, níveis e somas da série, contrato G4 das 3 saídas, ingênuo sazonal e fallback, % Achieved com e sem potencial, alerta, gravação só das aprovadas) e `tests/test_fabric_run.py` (29 casos, 12 novos: descoberta e duplicidade, filtro, células e tag `parameters`, guard nos notebooks reais, simulação do deploy sem API, workspace/lakehouse por ambiente, pasta por convenção, `--param` no corpo do job, `main` do run com ambiente e convenção). `python -m pytest` em 28/10: 277 passaram, 2 pulados e 1 falha anterior à T30, fora dos arquivos desta tarefa (`tests/test_comparacao.py::test_g3_oraculo_bate_baselines_e_tem_cobertura`: cobertura não nula em modelo sem intervalo, em `src/backtest/comparacao.py`).

**Pendente para a T31 (execução real):** confirmar no Fabric que a tag `parameters` do .ipynb é reconhecida pela célula de parâmetros, que a leitura `` `LakehouseOel`.bronze_s360.amostra `` resolve no Spark (lakehouse com schemas) e medir tempo/CU do `als_50`.
