# Modelo semântico `als_oilmodel` (entrega b, T34)

Definição TMDL do modelo semântico do Power BI/Fabric (D13/D14 em [13](../../../docs_fabric/13_revisao_alinhamento_reuniao_2026-10-21.md)), gerada a partir do contrato das saídas da T28 (`src/serving/contrato.py`). Não editar os `.tmdl` à mão: mude o contrato ou `gerar.py` e rode

```bash
python -m src.serving.semantico.gerar            # regrava als_oilmodel.SemanticModel/ (modo Import)
python -m pytest tests/test_semantico.py         # estrutura × contrato e drift gerador × arquivos
```

## Estrutura

```
als_oilmodel.SemanticModel/
  definition.pbism
  definition/
    database.tmdl            compatibilityLevel 1604
    model.tmdl               pt-BR, discourageImplicitMeasures
    expressions.tmdl         parâmetros, LerSaida e uma consulta base_* por saída
    relationships.tmdl       14 relacionamentos fato → dimensão
    tables/*.tmdl            5 fatos do contrato, 4 dimensões, Medidas
```

| Tabela | Origem | Chave |
|---|---|---|
| `forecast_consumo`, `pct_achieved`, `alertas`, `forecast_vendas`, `backtest_metricas` | parquet de `Files/als_oilmodel/saida/` (mesmos nomes de colunas e tipos do contrato) | a do contrato + colunas derivadas ocultas `entidade_chave`, `cliente_chave`, `segmento_chave` |
| `dim_entidade` | união de forecast_consumo, alertas e pct_achieved | `entidade_chave` = `nivel\|entidade_id` |
| `dim_cliente` | linhas de nível cliente + donos citados nas demais | `cliente_id` |
| `dim_segmento` | segmentos citados nas saídas | `segmento` |
| `dim_periodo` | calendário diário do 1º ao último mês das saídas (tabela de datas) | `data` |

Relacionamentos só de fato para dimensão (muitos-para-um, filtro num sentido), sem ligação entre dimensões, então não há caminho ambíguo. `backtest_metricas` fica solta (métricas já agregadas).

## Medidas (tabela `Medidas`)

| Pasta | Medidas | Regra |
|---|---|---|
| Consumo Real | Consumo realizado, Consumo previsto p50, Consumo Real | soma no **nível ativo** e na **granularidade ativa** (mês por padrão); Real = realizado (passado) + p50 (futuro) |
| Intervalo p10-p90 | Consumo previsto p10/p90, Amplitude do intervalo | só com **uma linha** no contexto (uma entidade × um período): quantis não somam |
| Potencial | Consumo potencial, Potencial p10/p90, Gap para o potencial | mesma regra; potencial p10/p90 também só por linha |
| % Achieved | Realizado 12m, Potencial 12m, % Achieved | D6: Σ realizado_12m ÷ Σ potencial_12m das entidades com potencial > 0 (razão das somas, não média dos %) |
| Alertas | Alertas abertos/de queda/de churn, Queda média, Clientes em queda, Equipamentos em churn | contagem sobre `alertas` (RN-05, RN-06) |
| Vendas (KPI 2) | Faturamento p10/p50/p90, EBIT p10/p50/p90 | nível cliente se houver filtro de cliente, senão segmento, senão total |
| Backtest | WAPE, Viés, Cobertura p10-p90 (ponderados por `n`), Cobertura declarada (0,8) | |

**Nível ativo:** o nível filtrado em `dim_entidade[nivel]`; senão `cliente` se houver filtro em `dim_cliente`; senão `segmento`. Assim um total nunca soma segmento + cliente + equipamento (as fatos têm os três níveis empilhados, e as colunas estão com `summarizeBy: none`).

**Limitações conhecidas:** `pct_achieved` não tem `cliente_id` no nível equipamento, então o filtro de cliente só alcança as linhas de nível cliente; `forecast_vendas` não tem segmento no nível cliente, então filtrar segmento e cliente juntos zera as vendas por cliente; a semana pertence ao mês da sua segunda-feira em `dim_periodo`.

## Fonte em modo Import (padrão, D14)

Parâmetros em `expressions.tmdl`: `OneLake` (host público), `Workspace`, `Lakehouse` e `PastaSaida` (`Files/als_oilmodel/saida`). Workspace e lakehouse ficam com valor `<...>` no git e são preenchidos no serviço (Configurações do modelo → Parâmetros) ou no Power BI Desktop; aceitam nome (`NomeDoLakehouse.Lakehouse`) ou GUID. `LerSaida(arquivo)` lista a pasta com `AzureStorage.DataLake` e lê o parquet (arquivo único do pandas ou pasta de partes do Spark). Credencial: conta organizacional (OAuth) definida no serviço ao configurar a atualização, nunca no repositório.

Para abrir: Power BI Desktop com o recurso PBIP/TMDL habilitado (criar um `.pbip` apontando para esta pasta) ou Tabular Editor. Publicar no workspace exige confirmação explícita do usuário (AGENTS.md); este repositório não publica nada.

## Trocar para DirectLake (só se o Caio autorizar `als_dev_*`, T26)

DirectLake só lê tabelas Delta persistidas, que D13 não permite hoje. Se a T26 liberar tabelas descartáveis `als_dev_*` num lakehouse existente:

1. No notebook de saída, gravar cada saída também como Delta `als_dev_<nome>` (com `ALS_FABRIC_DEV=1`, que a barreira `scripts/fabric_guard.py` exige), **já com as colunas derivadas** (`entidade_chave`, `cliente_chave`, `segmento_chave`, regras em `DERIVADAS` de `gerar.py`): DirectLake não aceita transformação Power Query nem coluna calculada.
2. Materializar também as dimensões `als_dev_dim_entidade`, `als_dev_dim_cliente`, `als_dev_dim_segmento` e `als_dev_dim_periodo`, com as mesmas regras das consultas M de `DIMENSOES`.
3. Gerar a variante fora do git: `python -m src.serving.semantico.gerar --modo directlake` (grava em `data/semantico_directlake/`). Ela troca os parâmetros e `LerSaida` por `DatabaseQuery` (`Sql.Database` do endpoint SQL do lakehouse) e as partições por `entity` + `mode: directLake` apontando para `als_dev_*`; a tabela `Medidas` vira tabela calculada.
4. Preencher `<endpoint-sql-do-lakehouse>` e `<id-do-lakehouse>` só na cópia local (o repositório é público) e publicar após confirmação.

Tabelas, colunas, relacionamentos e medidas são os mesmos nos dois modos; o teste `test_variante_directlake` garante isso.
