# Integração via MCP (Model Context Protocol)

> Como conectar o "agente" da ALS ao modelo entregue no Microsoft Fabric, usando MCP como camada fina de integração.
>
> **Status:** o MCP é uma das hipóteses de entrega a prototipar, junto de dashboard HTML + SQL e modelo semântico. O cliente escolhe após os protótipos (ver [13](13_revisao_alinhamento_reuniao_2026-10-21.md)).

## Contexto

Se o cliente escolher a entrega via MCP, o modelo de forecast (consumo + vendas) ficará disponível como **modelo semântico do Fabric** e/ou **API/endpoint**. O agente precisa consultá-lo sob demanda e devolver um número + intervalo de confiança. O **MCP (Model Context Protocol)** é o protocolo padrão que permite ao agente chamar "ferramentas" externas — no caso, consultar o Fabric.

**Princípio**: o MCP é "cola", não o core. Primeiro define-se o entregável (semântico vs endpoint); depois adiciona-se o MCP por cima.

## Arquitetura alvo

```
Usuário ──► Agente (Foundry/Semantic Kernel)
                 │  (MCP client)
                 ▼
        MCP Server (Fabric)
                 │  tools: query_semantic_model (DAX), query_lakehouse (SQL), run_pipeline, list_items
                 ▼
   ┌─────────────────────────────────────┐
   │ Microsoft Fabric (workspace)        │
   │  · Modelo Semântico (DirectLake)    │
   │  · Lakehouse Gold (tabelas Delta)   │
   │  · SQL analytics endpoint           │
   │  · Pipelines (agendadas)            │
   └─────────────────────────────────────┘
```

## Opções de MCP para Fabric

| MCP | Tipo | Foco | Quando usar |
|-----|------|------|-------------|
| `microsoft/fabric-rti-mcp` | Oficial | Real-Time Intelligence / Eventhouse (KQL) | alertas, eventos, monitoramento em tempo real |
| Fabric **data agent** (nativo) | Nativo Fabric | Q&A em linguagem natural sobre semântico/lakehouse | se o agente já estiver dentro do ecossistema Fabric |
| `santhoshravindran7/Fabric-Analytics-MCP` | Comunidade | Modelo semântico / analytics (DAX) | consumo de previsões já materializadas no semântico |
| `Augustab/microsoft_fabric_mcp` | Comunidade | Wrapper da Fabric REST API (workspaces, itens, pipelines) | orquestração/disparo de pipeline via agente |
| `ksylvan/fabric-mcp` | Comunidade | AI Skills do Fabric | expor skills/agentes do Fabric |

## Critérios de escolha (recomendado)

Decidir na reunião de validação o formato de entrega, depois escolher:

| Entrega final | MCP recomendado | Por quê |
|---------------|-----------------|---------|
| Modelo semântico (Power BI/DirectLake) | `Fabric-Analytics-MCP` **ou** Fabric data agent nativo | consulta DAX direto sobre métricas prontas |
| API/endpoint sob demanda | `microsoft_fabric_mcp` (REST) + endpoint próprio | controle fino, menos acoplamento |
| Alertas/eventos (Eventhouse) | `microsoft/fabric-rti-mcp` | KQL/streaming |

**Se o MCP for escolhido:** modelo semântico (DirectLake) com as previsões materializadas + Fabric data agent nativo (ou `Fabric-Analytics-MCP`) é o caminho de menor custo e manutenção; MCP próprio (FastMCP) é a opção para contrato estável (ver [09](09_conexao_e_consumo_fabric.md)).

## Exemplo de configuração (MCP client → servidor)

Configuração típica de um cliente MCP (formato JSON, `stdio`):

```json
{
  "mcpServers": {
    "fabric-analytics": {
      "command": "npx",
      "args": ["-y", "fabric-analytics-mcp"],
      "env": {
        "FABRIC_TENANT_ID": "<tenant-id>",
        "FABRIC_CLIENT_ID": "<service-principal-id>",
        "FABRIC_CLIENT_SECRET": "<client-secret>",
        "FABRIC_WORKSPACE_ID": "<workspace-id>",
        "FABRIC_SEMANTIC_MODEL_ID": "<model-id>"
      }
    }
  }
}
```

## Segurança e governança

- Autenticar via **service principal** (Entra ID) com escopo mínimo (leitura do semântico/lakehouse).
- Nunca expor segredos no repo; usar cofre/segredo do agente.
- MCP só lê as **tabelas de saída do Forecast** (`lh_forecast`; nunca Bronze/Silver nem a Gold do agente atual), limitando superfície de dados sensíveis. Detalhes em [09_conexao_e_consumo_fabric.md](09_conexao_e_consumo_fabric.md).
- Contrato estável: MCP fino próprio (FastMCP) com tools de leitura parametrizada ([09](09_conexao_e_consumo_fabric.md)).
- O MCP só entra se o cliente o escolher após a prototipagem ([13](13_revisao_alinhamento_reuniao_2026-10-21.md)).
- Auditar chamadas (quem consultou o quê) via logs do agente/Fabric.

## FinOps (capacidade F8)

- Consultas DAX/SQL sobre DirectLake consomem CU da capacidade F8, compartilhada com o agente.
- Preferir **agregados pré-calculados na Gold** (evitar DAX pesado em tempo real).
- Cachear resultados de previsão (o forecast não muda entre execuções de pipeline).
- MCP em si tem custo ~zero; o custo está nas consultas — manter leves e esparsas.

## Integração ao plano de execução (novo item)

Se o MCP for escolhido, adicionar à **Fase 5 — Entrega e handoff**:

1. Comparar os protótipos de entrega com o cliente e registrar a escolha.
2. Escolher o MCP correspondente (tabela acima).
3. Provisionar service principal + escopos mínimos no Fabric.
4. Configurar o MCP client no agente (arquivo de configuração + segredos).
5. Testar o fluxo ponta-a-ponta: pergunta do usuário → DAX/SQL → previsão + intervalo.
6. Validar custo (CU) das consultas na F8 e ajustar agregações se necessário.

## Protótipo H3a: dashboard HTML + SQL (T20, 27/10)

- **Gerador:** `python -m src.serving.dashboard [--forecast f.csv --alertas a.csv] [--saida x.html]`; sem argumentos usa dados **sintéticos** (aviso fixo no HTML) e grava os CSVs em `src/serving/exemplo/`.
- **Contrato:** `COLUNAS_FORECAST` (nível segmento/cliente/equipamento × mês/semana: `realizado`, `prev_p10/p50/p90`, `potencial`) e `COLUNAS_ALERTAS` (queda RN-05 e churn RN-06) em `src/serving/dashboard.py`; aceita CSV ou parquet.
- **SQL:** `src/serving/sql/01_forecast_consumo.sql` (T-SQL de leitura; tabelas `als_*` de entrada são propostas, ainda inexistentes no Fabric).
- **Testes:** `tests/test_serving.py`. Pendente: ligar à saída real da T15/T16 quando existir.

### T32 · Dashboard com saídas do contrato e SQL sobre `v_als_*` (28/10)

- **Saídas reais:** `data/forecast` (T29) estava vazio neste worktree. Sem Fabric, as saídas do contrato foram geradas **da base real** `data/base/base_cliente_mes.parquet` (T14) com o baseline ingênuo sazonal de `src/pipeline/dev.py` (`src/serving/local.py`): níveis segmento e cliente, corte 2026-10-01, horizonte 12 meses. Resultado em `data/serving/` (fora do git): `forecast_consumo.parquet` (247 920 linhas), `pct_achieved.parquet` (5 662), `alertas.parquet` (203 quedas), `relatorio_dev.json` (G4 aprovado) e `dashboard.html`. Sem equipamento, potencial nem churn (não estão na base). Quando a T29 gravar `saida/`, basta `--pasta`.
- **Gerador:** `python -m src.serving.dashboard --pasta data/serving` (parquet do contrato) ou `--base data/base/base_cliente_mes.parquet` (gera, grava e monta). **G4 roda antes de gerar** (`validar_contrato`): saída reprovada não vira HTML; alertas vazio é válido. Sem argumentos continua o exemplo sintético.
- **Contrato:** `COLUNAS_FORECAST`/`COLUNAS_ALERTAS` agora derivam de `src/serving/contrato.py`; o contrato ganhou `potencial_p10/potencial_p90`, então o exemplo sintético (CSV e HTML) foi regenerado.
- **SQL:** `src/serving/consultas.py` gera 4 pré-consultas (`dashboard_forecast`, `dashboard_alertas`, `resumo_entidade` = % Achieved + previsão do horizonte, `consumo_segmento_mes`) sobre `v_als_*`, em dialeto comum a Spark SQL e T-SQL (sem LIMIT/TOP/funções de data/crases). Nome e prefixo configuráveis: `consultas(prefixo="fct_", nomes={"alertas": "..."})`. O arquivo `src/serving/sql/01_pre_consultas.sql` é gerado delas e substitui `01_forecast_consumo.sql`, que lia as tabelas `als_*` inexistentes.
- **Testes:** `tests/test_serving.py` (20 casos): consultas rodam em DuckDB sobre parquet gerado de uma base pequena **e** sobre `data/serving` real (pula se ausente), com totais iguais aos do parquet; prefixo trocado; dialeto; arquivo SQL em dia. `python -m pytest`: 309 passed, 2 skipped (`duckdb` entrou nos extras `dev`).

## Comparativo das três opções de entrega (T21, 27/10)

- Quadro (a) dashboard HTML + SQL, (b) modelo semântico, (c) API/MCP, com esforço, manutenção, latência, aderência ao agente do CRM e riscos: [13 §2, H3](13_revisao_alinhamento_reuniao_2026-10-21.md).
- Recomendação: (b) como entrega principal, sobre as tabelas `als_*` da Gold; (c) na fase do agente, por cima do semântico (data agent ou `Fabric-Analytics-MCP`). CU e latência reais ainda não medidos (T22).

## Modelo semântico H3b: definição TMDL (T34, 28/10)

- **Onde:** `src/serving/semantico/als_oilmodel.SemanticModel/` (PBIP/TMDL, compatibilityLevel 1604), gerado de `src/serving/contrato.py` por `python -m src.serving.semantico.gerar`; detalhes em `src/serving/semantico/README.md`.
- **Tabelas:** as 5 saídas do contrato T28 (`forecast_consumo`, `pct_achieved`, `alertas`, `forecast_vendas`, `backtest_metricas`) com as mesmas colunas e tipos, mais 3 chaves derivadas ocultas (`entidade_chave`, `cliente_chave`, `segmento_chave`); 4 dimensões (`dim_entidade`, `dim_cliente`, `dim_segmento`, `dim_periodo`) e a tabela `Medidas`.
- **Relacionamentos:** 14, todos fato → dimensão (entidade, cliente, segmento, período), sem ligação entre dimensões.
- **Medidas DAX (32, 3 auxiliares ocultas):** consumo realizado, previsto p50 e Real; p10/p90 do forecast e do potencial (só por linha: quantis não somam); potencial e gap; % Achieved pela D6 (Σ realizado_12m ÷ Σ potencial_12m com potencial > 0); alertas de queda e churn; faturamento e EBIT p10/p50/p90; WAPE, viés e cobertura do backtest. Uma medida de "nível ativo" impede somar segmento + cliente + equipamento, e `discourageImplicitMeasures` bloqueia somas implícitas.
- **Fonte (D14):** modo Import, Power Query lê os parquet de `Files/als_oilmodel/saida/` no OneLake por `AzureStorage.DataLake` + `Parquet.Document`, com parâmetros `Workspace`, `Lakehouse` e `PastaSaida` (valores `<...>` no git; nenhum id, endpoint ou credencial versionado).
- **DirectLake:** só se a T26 liberar tabelas `als_dev_*`. `--modo directlake` gera a variante em `data/` (fora do git): partições `entity` sobre `als_dev_<tabela>` e `als_dev_dim_*`, e `DatabaseQuery` com o endpoint SQL preenchido só localmente. Exige gravar as chaves derivadas e as dimensões como Delta, porque DirectLake não aceita Power Query. Passo a passo no README.
- **Testes:** `tests/test_semantico.py` (11 testes, verdes; a suíte completa tem 1 falha pré-existente, `tests/test_comparacao.py::test_g3_oraculo_bate_baselines_e_tem_cobertura`, que já falha no `main` f8a4c12 sem a T34): tabelas e colunas do TMDL = contrato, tipos, partições lendo o parquet certo, parâmetros sem valor real, relacionamentos entre colunas existentes, medidas referenciando só colunas e medidas existentes, drift gerador × arquivos versionados e variante DirectLake.
- **Não validado:** o modelo não foi aberto no Power BI Desktop nem publicado (sem acesso e sem confirmação; D13), e as saídas reais em `saida/` ainda não existem. Validação no serviço, refresh, CU e latência ficam para a T35.
- **Limitações:** `pct_achieved` no nível equipamento não tem `cliente_id` (o filtro de cliente só pega as linhas de nível cliente); `forecast_vendas` no nível cliente não tem segmento (filtrar segmento e cliente juntos zera as vendas por cliente). As duas se resolvem acrescentando a coluna no contrato.
