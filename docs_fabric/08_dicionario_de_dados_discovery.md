# Descoberta de Dados do Fabric

**Endpoint**: `j2qfysdun5iebf3ezw2l7ke4eu-vpyatc664ptezeejap7oap22qu.datawarehouse.fabric.microsoft.com`

## Perfil de qualidade das tabelas-chave (T02, 2026-10-27)

> Seção escrita à mão. `scripts/fabric_probe.py` regera este arquivo e **apaga esta seção**: copie-a antes de rodar o probe. O dicionário de colunas gerado começa em "LakehouseOel", mais abaixo.

Origem: `notebooks/00_validacao/01_perfil_qualidade.py` via SQL endpoint (porta 1433 liberada na rede de execução; só leitura). Saída em `data/perfil/` (fora do git): `perfil.json`, `gates_g0.json` e 10 parquets de agregados. 0 erros de leitura. As consultas extras (duplicatas, horímetro) são agregados rodados com o mesmo cliente `Fabric`.

### Volume, período e chaves

| Tabela | Linhas | Período (coluna) | Chaves distintas |
|---|---|---|---|
| `bronze_s360.amostra` | 8.663.147 (60 `excluido=1`) | `data_criacao` 2016-11-28 → 2026-10-27; `data_coleta` ver abaixo | id 8.662.997; cliente_id 8.566; compartimento_id 1.488.955 |
| `bronze_s360.cliente` | 10.231 | `data_registro` 2016-11 → 2026-10 | id 10.231; id_cigam 7.463; codigo_legado 5.701; sam_id 1.167 |
| `bronze_s360.equipamento` | 1.063.584 | `data_registro` 2016-11 → 2026-10 | familia_equipamento_id 515; obra_id 54.482 |
| `bronze_s360.compartimento` | 3.478.165 | `data_registro` 2016-11 → 2026-10 | equipamento_id 1.053.566 |
| `silver_protheus.notassaida` | 58.666 | `emissao` 2024-08-01 → 2026-10-09 | numero 21.705; cod_cliente 2.850; cod_produto 575 |
| `silver_protheus.contasreceber` | 58.531 | `emissao` 2018-11-01 → 2026-10-09 | numero 16.141; cliente 2.456 |
| `silver_zoho.accounts` | 9.840 | `data_criacao` 2026-01-20 → 2026-10-27 | zoho_id 9.840; cnpj 7.434; erp_id 7.879; id_protheus 0 |
| `silver_zoho.deals` | 22.213 | `data_criacao` 2026-01-23 → 2026-10-27; `data_fechamento_prevista` 2024-01-02 → 2027-03-31 | zoho_id 22.213; conta_id 4.215 |

Amostras por ano de `data_coleta` (não excluídas, 2022+): 2022 615.810 · 2023 827.348 · 2024 908.585 · 2025 933.772 · 2026 (até out) 749.958. Faturamento mensal Protheus: ~R$ 6,9–8,6 mi/mês, 400–550 clientes/mês; out/2026 parcial (até 09/10).

### Nulos relevantes (% das linhas)

- `amostra`: `data_coleta` **25,81%** (2.235.900); `compartimento_id` 24,72%; `horimetro_equipado` 41,78%; `horas_oleo` 59,08%; `valor_servico_valor/moeda` 48,95%; `data_entrada_laboratorio` 23,18%. `data_impressao` e `versao` 100% nulos.
- `cliente`: `codigo_legado` 40,56%; `id_cigam` 26,81%; `sam_id` 88,59%; `razao_social` 25,37%.
- `equipamento`: `saude` 45,29%; `setor` 32,43%. `compartimento`: `horas_oleo` 89,88%; `oleo_trocado` 35,81%.
- `silver_zoho.accounts`: `id_protheus` **100%**; `vendas_ttm` 100%; `status_real` 77,76%.
- `silver_zoho.deals`: `motivo_perda` 84,05%; `tipo_oportunidade` 75,06%.
- `notassaida` e `contasreceber`: nenhuma coluna acima de 20% nula.

### Duplicatas

| Verificação | Resultado |
|---|---|
| `amostra.id` repetido | 145 ids, 150 linhas extra (0,002%) |
| `amostra` mesmo (compartimento, data_coleta), não excluídas | 80.687 grupos, 163.522 linhas extra (pode ser coleta legítima de vários ensaios; precisa de regra) |
| `notassaida` repetida em (numero, item) | 1.626 grupos, 1.652 linhas extra (2,8%) |
| `cliente.id_cigam` repetido | 23 valores em 48 clientes |
| `accounts.cnpj` repetido | 421 CNPJs em 1.052 contas (filiais ou cadastro duplicado) |

### Datas fora do intervalo (`amostra.data_coleta`, não excluídas)

| Faixa | Linhas |
|---|---|
| Nula | 2.235.900 (2.020.720 também sem `compartimento_id`; 215.180 só data nula) |
| Antes de 2015 (inclui anos 0001, 0201, 1920, 1969…) | 227.852 |
| Futuro (> 2026-10-28; chega a 2115-09-16) | 37 |
| Válidas (2015-01-01 → 2026-10-28) | 6.199.298 |

Picos suspeitos: 1969-12 (87 amostras, época Unix zero) e ano 0201 (centenas, erro de digitação). `data_entrada_laboratorio` e `data_finalizacao` têm mínimo 2005-05-11, antes do início do S360 (2016).

### Horímetro (`amostra`, não excluídas)

| Medida | `horimetro_equipado` | `horas_oleo` |
|---|---|---|
| Preenchidos | 5.043.997 | 3.545.334 |
| Negativos | 85 | 4 |
| Zero | 273.049 | n/d |
| > 100.000 (equip.) / > 50.000 (óleo) | 275.190 | 161.217 |
| > 1.000.000 | 21.159 | n/d |
| Máximo | 2.100.607.054 | 2.113.521.135 |
| P50 / P99 / P99,9 | 5.865 / 618.773 / 5.082.653 | n/d |

- `horas_oleo` > `horimetro_equipado` em 240.871 linhas.
- Regressão do horímetro por compartimento (valor menor que o da coleta anterior, 2015–2026): 260.538 ocorrências em 149.085 compartimentos.
- P99 de 618 mil indica unidade ou escala inconsistente: o horímetro bruto não serve como feature sem saneamento.

### Achados que afetam KPI 1 (consumo de amostras)

1. **25,81% das amostras sem `data_coleta`**: não entram na série mensal. Decidir a data de referência (`data_criacao`, 100% preenchida, ou `data_entrada_laboratorio`) e medir o desvio entre elas.
2. Datas impossíveis (227 mil < 2015, 37 futuras) contaminam a série: filtrar 2015-01-01 ≤ `data_coleta` ≤ hoje, registrando o descarte.
3. Duplicatas de `id` (150) e de (compartimento, data) (163 mil) inflam a contagem sem regra de deduplicação.
4. Avulsas (sem compartimento): 2.141.200 (24,7%); exigem tratamento na RN de recorrência (Real x Potencial).
5. Horímetro e `horas_oleo` com outliers e regressão afetam a feature de intervalo de troca e o % Achieved.
6. Crescimento 2022→2025 de +51%: série com tendência, não estacionária.

### Achados que afetam KPI 2 (vendas/faturamento)

1. **Histórico curto**: `notassaida` cobre só 2024-08 → 2026-10 (27 meses); `contasreceber` vai a 2018-11. Backtest sazonal tem poucos pontos por mês.
2. Out/2026 é parcial (até 09/10): excluir da avaliação ou marcar como incompleto.
3. 1.652 linhas duplicadas por (numero, item) e 46 itens com quantidade ≤ 0 distorcem o faturamento.
4. Chaves S360 ↔ Protheus: `codigo_legado` 40% e `id_cigam` 27% nulos, `id_cigam` repetido em 23; `accounts.id_protheus` 100% nulo (Zoho liga só por `erp_id`/`cnpj`, com CNPJ repetido). Taxa de casamento fica para T03.
5. Zoho tem só ~10 meses de histórico (desde 2026-01): insuficiente para aprender conversão de deals sem Protheus.

### Rascunho dos gates G0/G1

G0 hoje (`src/gates/checks.py`): 22 de 27 checagens passam. As 5 falhas são achados reais: `amostra.data_coleta` com 25,81% de nulos (limite 5%); datas implausíveis em `amostra.data_coleta`, `data_entrada_laboratorio` e `data_finalizacao`; e `deals.data_fechamento_prevista` (2027-03), que é data prevista legítima, então o gate precisa de janela própria para datas previstas.

| Gate | Verificação proposta | Limiar inicial | Situação com os dados |
|---|---|---|---|
| G0 | Tabela-chave não vazia | > 0 linhas | passa |
| G0 | Nulos de `data_coleta` (ou data de referência alternativa) | ≤ 5% | **falha** 25,81% |
| G0 | `data_coleta` plausível (2015 → hoje) | 0 fora | **falha** (227.852 + 37) |
| G0 | Datas previstas (deals) com janela própria (hoje ± 2 anos) | 0 fora | ajustar regra; hoje falha |
| G0 | Frescor da carga (`MAX(data_criacao)` vs hoje) | ≤ 2 dias | passa |
| G0 | Cobertura de `notassaida`: meses fechados completos | mês corrente marcado parcial | out/2026 parcial |
| G0 (novo) | `amostra.id` sem duplicata | 0 | **falha** (150) |
| G0 (novo) | (numero, item) único em `notassaida` | 0 | **falha** (1.652) |
| G0 (novo) | Horímetro sem negativos e ≤ 1.000.000 | 0 negativos, outliers reportados | **falha** (85 negativos; 21.159 > 1 mi) |
| G1 | `chave_unica` (cliente_id, ano_mes) na tabela-base | sem repetição | validar na construção |
| G1 | `nao_negativo` e `sem_nulos` no alvo | 0 | validar |
| G1 | `meses_continuos` por entidade | 0 buracos após zeros | validar |
| G1 (novo) | Reconciliação: soma da tabela-base = fonte filtrada | diferença ≤ 0,1% | a criar |

---

## LakehouseOel

### Schema: `bronze_protheus`

#### Tabela: `contabil`

**Colunas**: 15

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `data` | `varchar` | ✓ |
| `lote` | `varchar` | ✓ |
| `sublote` | `varchar` | ✓ |
| `debito` | `varchar` | ✓ |
| `credito` | `varchar` | ✓ |
| `linha` | `varchar` | ✓ |
| `valor` | `varchar` | ✓ |
| `historico` | `varchar` | ✓ |
| `cc_debito` | `varchar` | ✓ |
| `cc_credito` | `varchar` | ✓ |
| `item_debito` | `varchar` | ✓ |
| `item_credito` | `varchar` | ✓ |
| `filial` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `contaspagar`

**Colunas**: 31

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `nota_eletronica` | `varchar` | ✓ |
| `prefixo` | `varchar` | ✓ |
| `parcela` | `varchar` | ✓ |
| `tipo` | `varchar` | ✓ |
| `fornecedor` | `varchar` | ✓ |
| `loja` | `varchar` | ✓ |
| `nome_fornecedor` | `varchar` | ✓ |
| `emissao` | `varchar` | ✓ |
| `numero` | `varchar` | ✓ |
| `vencimento` | `varchar` | ✓ |
| `vencimento_real` | `varchar` | ✓ |
| `valor` | `varchar` | ✓ |
| `filial` | `varchar` | ✓ |
| `iss` | `varchar` | ✓ |
| `irrf` | `varchar` | ✓ |
| `baixa` | `varchar` | ✓ |
| `historico` | `varchar` | ✓ |
| `contabilizado` | `varchar` | ✓ |
| `saldo` | `varchar` | ✓ |
| `desconto` | `varchar` | ✓ |
| `multa` | `varchar` | ✓ |
| `juros` | `varchar` | ✓ |
| `moeda` | `varchar` | ✓ |
| `inss` | `varchar` | ✓ |
| `cofins` | `varchar` | ✓ |
| `pis` | `varchar` | ✓ |
| `csll` | `varchar` | ✓ |
| `data_digitacao` | `varchar` | ✓ |
| `origem` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `contasreceber`

**Colunas**: 35

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `nota_eletronica` | `varchar` | ✓ |
| `prefixo` | `varchar` | ✓ |
| `parcela` | `varchar` | ✓ |
| `tipo` | `varchar` | ✓ |
| `cliente` | `varchar` | ✓ |
| `loja` | `varchar` | ✓ |
| `nome_cliente` | `varchar` | ✓ |
| `emissao` | `varchar` | ✓ |
| `numero` | `varchar` | ✓ |
| `vencimento` | `varchar` | ✓ |
| `vencimento_real` | `varchar` | ✓ |
| `valor` | `varchar` | ✓ |
| `filial` | `varchar` | ✓ |
| `iss` | `varchar` | ✓ |
| `irrf` | `varchar` | ✓ |
| `baixa` | `varchar` | ✓ |
| `historico` | `varchar` | ✓ |
| `contabilizado` | `varchar` | ✓ |
| `saldo` | `varchar` | ✓ |
| `desconto` | `varchar` | ✓ |
| `multa` | `varchar` | ✓ |
| `juros` | `varchar` | ✓ |
| `moeda` | `varchar` | ✓ |
| `inss` | `varchar` | ✓ |
| `cofins` | `varchar` | ✓ |
| `pis` | `varchar` | ✓ |
| `csll` | `varchar` | ✓ |
| `orcamento` | `varchar` | ✓ |
| `nome_vendedor` | `varchar` | ✓ |
| `forma_pagamento` | `varchar` | ✓ |
| `write_off` | `varchar` | ✓ |
| `cancelamento_adm` | `varchar` | ✓ |
| `origem` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `depreciacao`

**Colunas**: 15

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `codigo_base` | `varchar` | ✓ |
| `ocorrencia` | `varchar` | ✓ |
| `conta` | `varchar` | ✓ |
| `data` | `varchar` | ✓ |
| `valor` | `varchar` | ✓ |
| `item` | `varchar` | ✓ |
| `tipo` | `varchar` | ✓ |
| `serie` | `varchar` | ✓ |
| `nota` | `varchar` | ✓ |
| `centro_custo` | `varchar` | ✓ |
| `taxa_depreciacao` | `varchar` | ✓ |
| `contabilizado` | `varchar` | ✓ |
| `filial` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `devolucao`

**Colunas**: 15

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `data` | `varchar` | ✓ |
| `lote` | `varchar` | ✓ |
| `sublote` | `varchar` | ✓ |
| `debito` | `varchar` | ✓ |
| `credito` | `varchar` | ✓ |
| `linha` | `varchar` | ✓ |
| `valor` | `varchar` | ✓ |
| `historico` | `varchar` | ✓ |
| `cc_debito` | `varchar` | ✓ |
| `cc_credito` | `varchar` | ✓ |
| `item_debito` | `varchar` | ✓ |
| `item_credito` | `varchar` | ✓ |
| `filial` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `ferias`

**Colunas**: 6

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `periodo` | `varchar` | ✓ |
| `descricao` | `varchar` | ✓ |
| `valor` | `varchar` | ✓ |
| `filial` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `folhaantiga`

**Colunas**: 10

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `periodo` | `varchar` | ✓ |
| `codigo_verba` | `varchar` | ✓ |
| `descricao` | `varchar` | ✓ |
| `valor` | `varchar` | ✓ |
| `filial` | `varchar` | ✓ |
| `roteiro` | `varchar` | ✓ |
| `centro_custo` | `varchar` | ✓ |
| `departamento` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `movbancario`

**Colunas**: 24

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `filial` | `varchar` | ✓ |
| `data` | `varchar` | ✓ |
| `tipo` | `varchar` | ✓ |
| `moeda` | `varchar` | ✓ |
| `valor` | `varchar` | ✓ |
| `banco` | `varchar` | ✓ |
| `agencia` | `varchar` | ✓ |
| `conta` | `varchar` | ✓ |
| `recpag` | `varchar` | ✓ |
| `beneficiario` | `varchar` | ✓ |
| `historico` | `varchar` | ✓ |
| `contabilizado` | `varchar` | ✓ |
| `prefixo` | `varchar` | ✓ |
| `numero` | `varchar` | ✓ |
| `parcela` | `varchar` | ✓ |
| `data_digitacao` | `varchar` | ✓ |
| `mot_baixa` | `varchar` | ✓ |
| `data_disponibilizacao` | `varchar` | ✓ |
| `juros` | `varchar` | ✓ |
| `multa` | `varchar` | ✓ |
| `desconto` | `varchar` | ✓ |
| `taxa_moeda` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `notasentrada`

**Colunas**: 38

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `item` | `varchar` | ✓ |
| `cod_produto` | `varchar` | ✓ |
| `desc_produto` | `varchar` | ✓ |
| `unid_medida` | `varchar` | ✓ |
| `quantidade` | `varchar` | ✓ |
| `preco` | `varchar` | ✓ |
| `total` | `varchar` | ✓ |
| `num_pedido` | `varchar` | ✓ |
| `numero` | `varchar` | ✓ |
| `ipi` | `varchar` | ✓ |
| `item_pedido` | `varchar` | ✓ |
| `armazem` | `varchar` | ✓ |
| `filial` | `varchar` | ✓ |
| `icms` | `varchar` | ✓ |
| `cod_fornecedor` | `varchar` | ✓ |
| `loja_fornecedor` | `varchar` | ✓ |
| `centro_custo` | `varchar` | ✓ |
| `conta_contabil` | `varchar` | ✓ |
| `cfop` | `varchar` | ✓ |
| `emissao` | `varchar` | ✓ |
| `porc_icms` | `varchar` | ✓ |
| `data_digitacao` | `varchar` | ✓ |
| `serie` | `varchar` | ✓ |
| `tipo` | `varchar` | ✓ |
| `nota_origem` | `varchar` | ✓ |
| `serie_origem` | `varchar` | ✓ |
| `item_origem` | `varchar` | ✓ |
| `desconto` | `varchar` | ✓ |
| `icms_retido` | `varchar` | ✓ |
| `cofins` | `varchar` | ✓ |
| `pis` | `varchar` | ✓ |
| `iss` | `varchar` | ✓ |
| `ir` | `varchar` | ✓ |
| `seguro` | `varchar` | ✓ |
| `despesas` | `varchar` | ✓ |
| `inss` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `notassaida`

**Colunas**: 36

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `item` | `varchar` | ✓ |
| `cod_produto` | `varchar` | ✓ |
| `unid_medida` | `varchar` | ✓ |
| `quantidade` | `varchar` | ✓ |
| `preco` | `varchar` | ✓ |
| `total` | `varchar` | ✓ |
| `num_pedido` | `varchar` | ✓ |
| `numero` | `varchar` | ✓ |
| `ipi` | `varchar` | ✓ |
| `item_pedido` | `varchar` | ✓ |
| `armazem` | `varchar` | ✓ |
| `filial` | `varchar` | ✓ |
| `icms` | `varchar` | ✓ |
| `cod_cliente` | `varchar` | ✓ |
| `loja` | `varchar` | ✓ |
| `conta_contabil` | `varchar` | ✓ |
| `cfop` | `varchar` | ✓ |
| `emissao` | `varchar` | ✓ |
| `porc_icms` | `varchar` | ✓ |
| `data_digitacao` | `varchar` | ✓ |
| `serie` | `varchar` | ✓ |
| `nota_origem` | `varchar` | ✓ |
| `serie_origem` | `varchar` | ✓ |
| `item_origem` | `varchar` | ✓ |
| `desconto` | `varchar` | ✓ |
| `icms_retido` | `varchar` | ✓ |
| `cofins` | `varchar` | ✓ |
| `pis` | `varchar` | ✓ |
| `iss` | `varchar` | ✓ |
| `ir` | `varchar` | ✓ |
| `seguro` | `varchar` | ✓ |
| `despesas` | `varchar` | ✓ |
| `inss` | `varchar` | ✓ |
| `frete` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `pedcompras`

**Colunas**: 25

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `item` | `varchar` | ✓ |
| `cod_produto` | `varchar` | ✓ |
| `desc_produto` | `varchar` | ✓ |
| `unid_medida` | `varchar` | ✓ |
| `quantidade` | `varchar` | ✓ |
| `preco` | `varchar` | ✓ |
| `total` | `varchar` | ✓ |
| `num_solicitacao` | `varchar` | ✓ |
| `numero` | `varchar` | ✓ |
| `data_entrega` | `varchar` | ✓ |
| `item_solicitacao` | `varchar` | ✓ |
| `armazem` | `varchar` | ✓ |
| `filial` | `varchar` | ✓ |
| `observacao` | `varchar` | ✓ |
| `cod_fornecedor` | `varchar` | ✓ |
| `loja_fornecedor` | `varchar` | ✓ |
| `centro_custo` | `varchar` | ✓ |
| `conta_contabil` | `varchar` | ✓ |
| `cond_pagto` | `varchar` | ✓ |
| `emissao` | `varchar` | ✓ |
| `aprovacao` | `varchar` | ✓ |
| `especificacao` | `varchar` | ✓ |
| `quant_entregue` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `pedvendas`

**Colunas**: 23

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `item` | `varchar` | ✓ |
| `cod_produto` | `varchar` | ✓ |
| `desc_produto` | `varchar` | ✓ |
| `unid_medida` | `varchar` | ✓ |
| `quantidade` | `varchar` | ✓ |
| `preco` | `varchar` | ✓ |
| `total` | `varchar` | ✓ |
| `numero` | `varchar` | ✓ |
| `data_entrega` | `varchar` | ✓ |
| `armazem` | `varchar` | ✓ |
| `filial` | `varchar` | ✓ |
| `cod_fornecedor` | `varchar` | ✓ |
| `loja_fornecedor` | `varchar` | ✓ |
| `centro_custo` | `varchar` | ✓ |
| `conta_contabil` | `varchar` | ✓ |
| `pedido_compra` | `varchar` | ✓ |
| `item_pedido_compra` | `varchar` | ✓ |
| `perc_desconto` | `varchar` | ✓ |
| `valor_desconto` | `varchar` | ✓ |
| `nota_fiscal` | `varchar` | ✓ |
| `serie` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `provisao`

**Colunas**: 7

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `periodo` | `varchar` | ✓ |
| `descricao` | `varchar` | ✓ |
| `valor` | `varchar` | ✓ |
| `filial` | `varchar` | ✓ |
| `tipo` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `reajuste`

**Colunas**: 8

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `filial` | `varchar` | ✓ |
| `descricao` | `varchar` | ✓ |
| `data` | `varchar` | ✓ |
| `tipo` | `varchar` | ✓ |
| `valor` | `varchar` | ✓ |
| `valor_anterior` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `rescisao`

**Colunas**: 6

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `periodo` | `varchar` | ✓ |
| `descricao` | `varchar` | ✓ |
| `valor` | `varchar` | ✓ |
| `filial` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `solcompras`

**Colunas**: 25

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `item` | `varchar` | ✓ |
| `cod_produto` | `varchar` | ✓ |
| `desc_produto` | `varchar` | ✓ |
| `unid_medida` | `varchar` | ✓ |
| `quantidade` | `varchar` | ✓ |
| `num_pedido` | `varchar` | ✓ |
| `numero` | `varchar` | ✓ |
| `data_entrega` | `varchar` | ✓ |
| `item_pedido` | `varchar` | ✓ |
| `armazem` | `varchar` | ✓ |
| `filial` | `varchar` | ✓ |
| `observacao` | `varchar` | ✓ |
| `cod_fornecedor` | `varchar` | ✓ |
| `loja_fornecedor` | `varchar` | ✓ |
| `centro_custo` | `varchar` | ✓ |
| `conta_contabil` | `varchar` | ✓ |
| `emissao` | `varchar` | ✓ |
| `especificacao` | `varchar` | ✓ |
| `solicitante` | `varchar` | ✓ |
| `tipo_solicitacao` | `varchar` | ✓ |
| `comprador` | `varchar` | ✓ |
| `quant_entregue` | `varchar` | ✓ |
| `aprovacao` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

### Schema: `bronze_s360`

#### Tabela: `amostra`

**Colunas**: 64

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `comentario` | `varchar` | ✓ |
| `data_coleta` | `datetime2` | ✓ |
| `data_criacao` | `datetime2` | ✓ |
| `data_entrada_laboratorio` | `datetime2` | ✓ |
| `data_impressao` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `horas_oleo` | `int` | ✓ |
| `horimetro_equipado` | `int` | ✓ |
| `numero_amostra` | `varchar` | ✓ |
| `oleo_trocado` | `int` | ✓ |
| `versao` | `int` | ✓ |
| `volume_adicionado` | `real` | ✓ |
| `cliente_id` | `bigint` | ✓ |
| `produto_caixa_id` | `bigint` | ✓ |
| `programa_id` | `bigint` | ✓ |
| `tipo_amostra` | `bigint` | ✓ |
| `excluido` | `bit` | ✓ |
| `status_amostra` | `smallint` | ✓ |
| `compartimento_id` | `bigint` | ✓ |
| `controle_importacao_id` | `bigint` | ✓ |
| `fabricante_oleo_id` | `bigint` | ✓ |
| `viscosidade_oleo_id` | `bigint` | ✓ |
| `codigo_externo` | `varchar` | ✓ |
| `numero_laboratorio` | `bigint` | ✓ |
| `coleta_amostra_id` | `bigint` | ✓ |
| `ja_foi_segregada` | `bit` | ✓ |
| `descricao_oleo` | `varchar` | ✓ |
| `data_finalizacao` | `datetime2` | ✓ |
| `nome_compartimento` | `varchar` | ✓ |
| `tipo_compartimento_id` | `bigint` | ✓ |
| `tipo_coleta_amostra` | `bigint` | ✓ |
| `data_desegregacao` | `datetime2` | ✓ |
| `houve_pre_registro` | `bit` | ✓ |
| `data_registro_coleta` | `datetime2` | ✓ |
| `prazo_entrada_laboratorio` | `bigint` | ✓ |
| `prazo_entrega` | `bigint` | ✓ |
| `prazo_interpretacao` | `bigint` | ✓ |
| `prazo_laboratorio` | `bigint` | ✓ |
| `prazo_registro_coleta_laboratorio` | `bigint` | ✓ |
| `prazo_solucao_segregado` | `bigint` | ✓ |
| `obra_id` | `bigint` | ✓ |
| `fix_id` | `bigint` | ✓ |
| `pos_pago` | `bit` | ✓ |
| `data_processo` | `datetime2` | ✓ |
| `data_saida_laboratorio` | `datetime2` | ✓ |
| `data_atualizacao_finalizacao` | `datetime2` | ✓ |
| `laboratorio_id` | `bigint` | ✓ |
| `valor_servico_valor` | `decimal` | ✓ |
| `valor_servico_moeda` | `varchar` | ✓ |
| `operacao_id` | `varchar` | ✓ |
| `valido_no_programa` | `bit` | ✓ |
| `modelo_oleo_id` | `bigint` | ✓ |
| `rack_id` | `bigint` | ✓ |
| `agente_coleta` | `bigint` | ✓ |
| `responsavel_registro_id` | `bigint` | ✓ |
| `finished_sample_index_submission_date` | `datetime2` | ✓ |
| `responsible_to_close_data_entry_issue_id` | `bigint` | ✓ |
| `data_entry_activity` | `varchar` | ✓ |
| `numero_amostra_idx` | `varchar` | ✓ |
| `operation_id` | `int` | ✓ |
| `test_package_deadline` | `int` | ✓ |
| `laboratory_deadline` | `int` | ✓ |

#### Tabela: `amostra_plano_analise`

**Colunas**: 7

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `amostra_id` | `bigint` | ✓ |
| `plano_analise_id` | `bigint` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `fixo` | `bit` | ✓ |

#### Tabela: `analise_grupos_trabalho`

**Colunas**: 2

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `analise_id` | `bigint` | ✓ |
| `grupo_trabalho_id` | `bigint` | ✓ |

#### Tabela: `analise_traducao`

**Colunas**: 9

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `analise_id` | `bigint` | ✓ |
| `locale` | `varchar` | ✓ |
| `version` | `bigint` | ✓ |
| `abreviacao` | `varchar` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `metodo` | `varchar` | ✓ |
| `nome` | `varchar` | ✓ |
| `unidade_medida` | `varchar` | ✓ |

#### Tabela: `atividade_base`

**Colunas**: 5

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `data` | `datetime2` | ✓ |
| `tipo` | `int` | ✓ |
| `usuario_id` | `bigint` | ✓ |

#### Tabela: `atividade_resultado_analise`

**Colunas**: 2

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `entidade_referenciada_id` | `bigint` | ✓ |

#### Tabela: `cliente`

**Colunas**: 42

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `ativo` | `bit` | ✓ |
| `data_nascimento` | `datetime2` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `nome` | `varchar` | ✓ |
| `razao_social` | `varchar` | ✓ |
| `sexo_id` | `bigint` | ✓ |
| `tipo_cliente` | `int` | ✓ |
| `dealer` | `varchar` | ✓ |
| `envio_relatorio_sem_interpretacao` | `bit` | ✓ |
| `inadimplente` | `bit` | ✓ |
| `seguimento_cliente_id` | `bigint` | ✓ |
| `tipo_forma_pagamento_cliente` | `bigint` | ✓ |
| `tipo_conta_cliente_id` | `bigint` | ✓ |
| `grupo_clientes_id` | `bigint` | ✓ |
| `codigo_legado` | `varchar` | ✓ |
| `programa_padrao_id` | `bigint` | ✓ |
| `ordenar_por_horimetro_equipamentopdf` | `bit` | ✓ |
| `exibir_legendapdf` | `bit` | ✓ |
| `fazer_interpretacao_ativa` | `bit` | ✓ |
| `gerar_interpretacao` | `bit` | ✓ |
| `layout_importacao_coleta` | `varchar` | ✓ |
| `data_atualizacao_hubspot` | `datetime2` | ✓ |
| `identificador_hub_spot` | `bigint` | ✓ |
| `idioma_interpretacao` | `varchar` | ✓ |
| `operacao_id` | `varchar` | ✓ |
| `modelo_relatorio_enum` | `varchar` | ✓ |
| `fazer_auto_interpretacao` | `bit` | ✓ |
| `id_cigam` | `varchar` | ✓ |
| `setor_cliente_id` | `bigint` | ✓ |
| `termo_pagamento_id` | `bigint` | ✓ |
| `mercado_cliente_id` | `bigint` | ✓ |
| `cliente_integracao_sisma_id` | `bigint` | ✓ |
| `obra_padrao_id` | `bigint` | ✓ |
| `estrangeiro_na_operacao` | `bit` | ✓ |
| `sam_id` | `varchar` | ✓ |
| `short_code` | `varchar` | ✓ |
| `currency` | `varchar` | ✓ |
| `twist_id` | `varchar` | ✓ |
| `tax` | `float` | ✓ |

#### Tabela: `compartimento`

**Colunas**: 19

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `ativo` | `bit` | ✓ |
| `codigo_externo` | `varchar` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `equipamento_id` | `bigint` | ✓ |
| `nome` | `varchar` | ✓ |
| `num_serie` | `varchar` | ✓ |
| `tipo_compartimento_id` | `bigint` | ✓ |
| `volume` | `real` | ✓ |
| `descricao_oleo` | `varchar` | ✓ |
| `fabricante_oleo_id` | `bigint` | ✓ |
| `modelo_oleo_id` | `bigint` | ✓ |
| `viscosidade_oleo_id` | `bigint` | ✓ |
| `horas_oleo` | `int` | ✓ |
| `oleo_trocado` | `varchar` | ✓ |
| `sam_id` | `varchar` | ✓ |
| `uin` | `varchar` | ✓ |

#### Tabela: `equipamento`

**Colunas**: 20

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `ativo` | `bit` | ✓ |
| `chassi_serie` | `varchar` | ✓ |
| `codigo_externo` | `varchar` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `filtro_oil_check` | `bit` | ✓ |
| `modelo` | `varchar` | ✓ |
| `tag_frota` | `varchar` | ✓ |
| `tamanho_metrica_controle` | `int` | ✓ |
| `controle_importacao_id` | `bigint` | ✓ |
| `fabricante_equipamento_id` | `bigint` | ✓ |
| `familia_equipamento_id` | `bigint` | ✓ |
| `obra_id` | `bigint` | ✓ |
| `tipo_metrica_controle` | `int` | ✓ |
| `area` | `varchar` | ✓ |
| `setor` | `varchar` | ✓ |
| `saude` | `real` | ✓ |
| `sam_id` | `varchar` | ✓ |

#### Tabela: `expedicao`

**Colunas**: 15

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `cancelado` | `bit` | ✓ |
| `cliente_id` | `bigint` | ✓ |
| `data_nota` | `datetime2` | ✓ |
| `observacao` | `varchar` | ✓ |
| `numero` | `varchar` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `pos_pago` | `bit` | ✓ |
| `programa_id` | `bigint` | ✓ |
| `numero_notafiscal_servico` | `varchar` | ✓ |
| `valor_total_servico_valor` | `decimal` | ✓ |
| `valor_total_servico_moeda` | `varchar` | ✓ |
| `operacao_id` | `varchar` | ✓ |

#### Tabela: `grupo_trabalho`

**Colunas**: 6

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `ativo` | `bit` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `forma_resultado_grupo_trabalho_enum` | `int` | ✓ |

#### Tabela: `grupo_trabalho_laboratorios`

**Colunas**: 2

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `laboratorio_id` | `bigint` | ✓ |
| `grupo_trabalho_id` | `bigint` | ✓ |

#### Tabela: `grupo_trabalho_traducao`

**Colunas**: 6

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `grupo_trabalho_id` | `bigint` | ✓ |
| `locale` | `varchar` | ✓ |
| `version` | `bigint` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `nome` | `varchar` | ✓ |

#### Tabela: `laboratorio`

**Colunas**: 21

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `nome` | `varchar` | ✓ |
| `endereco_id` | `bigint` | ✓ |
| `impressora_id` | `bigint` | ✓ |
| `operacao_id` | `varchar` | ✓ |
| `entrar_sem_coleta` | `bit` | ✓ |
| `time_zone` | `varchar` | ✓ |
| `trabalha_com_rack` | `bit` | ✓ |
| `tamanho_maximo_rack` | `int` | ✓ |
| `laboratory_entry_deadline` | `int` | ✓ |
| `interpretation_deadline` | `int` | ✓ |
| `missing_pre_registration_deadline` | `int` | ✓ |
| `desegregation_deadline` | `int` | ✓ |
| `missing_test_package_deadline` | `int` | ✓ |
| `financial_pending_deadline` | `int` | ✓ |
| `out_of_bottle_deadline` | `int` | ✓ |
| `out_of_program_deadline` | `int` | ✓ |
| `analysis_review_deadline` | `int` | ✓ |

#### Tabela: `layouts_grupo_trabalho`

**Colunas**: 5

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `layout` | `varchar` | ✓ |
| `grupo_trabalho_id` | `bigint` | ✓ |
| `parametros` | `varchar` | ✓ |
| `apelido` | `varchar` | ✓ |

#### Tabela: `plano_analise`

**Colunas**: 6

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `ativo` | `bit` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `prazo` | `int` | ✓ |

#### Tabela: `plano_analise_traducao`

**Colunas**: 7

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `plano_analise_id` | `bigint` | ✓ |
| `locale` | `varchar` | ✓ |
| `version` | `bigint` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `nome` | `varchar` | ✓ |
| `aplicacao` | `varchar` | ✓ |

#### Tabela: `produto_caixa_expedicoes`

**Colunas**: 2

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `expedicao_id` | `bigint` | ✓ |
| `produto_caixa_id` | `bigint` | ✓ |

#### Tabela: `recebimento_amostra`

**Colunas**: 16

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `cliente_id` | `bigint` | ✓ |
| `conhecimento_frete` | `varchar` | ✓ |
| `data_postagem` | `datetime2` | ✓ |
| `data_recebimento` | `datetime2` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `observacao` | `varchar` | ✓ |
| `endereco_id` | `bigint` | ✓ |
| `laboratorio_id` | `bigint` | ✓ |
| `forma_recebimento_id` | `bigint` | ✓ |
| `codigo_transportadora` | `varchar` | ✓ |
| `obra_id` | `bigint` | ✓ |
| `responsible_id` | `bigint` | ✓ |
| `data_recebimento_original` | `datetime2` | ✓ |

#### Tabela: `recebimento_amostra_amostra`

**Colunas**: 6

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `amostra_id` | `bigint` | ✓ |
| `recebimento_amostra_id` | `bigint` | ✓ |
| `segregado` | `bit` | ✓ |
| `tipo_compartimento_id` | `bigint` | ✓ |

#### Tabela: `resultado_amostra`

**Colunas**: 21

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `amostra_id` | `bigint` | ✓ |
| `data_liberacao_para_interpretacao` | `datetime2` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `cliente_id` | `bigint` | ✓ |
| `resultado_interpretacao_amostra` | `bigint` | ✓ |
| `status_resultado_amostra` | `bigint` | ✓ |
| `responsavel_id` | `bigint` | ✓ |
| `data_interpretacao_finalizada` | `datetime2` | ✓ |
| `informacoes_ao_cliente` | `varchar` | ✓ |
| `texto_interpretacao` | `varchar` | ✓ |
| `email_enviado` | `bit` | ✓ |
| `idioma_na_interpretacao` | `varchar` | ✓ |
| `data_alteracao_recomendacao_comentario` | `datetime2` | ✓ |
| `responsavel_edicao_recomendacao_comentario_id` | `bigint` | ✓ |
| `cobertura` | `real` | ✓ |
| `sugestao_resultado_interpretacao_amostra` | `varchar` | ✓ |
| `parametro_interpretacao_id` | `bigint` | ✓ |
| `updated_by_user` | `bit` | ✓ |

#### Tabela: `resultado_analise`

**Colunas**: 21

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `amostra_id` | `bigint` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_resultado` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `motivo_analise` | `varchar` | ✓ |
| `valor` | `varchar` | ✓ |
| `laboratorio_id` | `bigint` | ✓ |
| `analise_id` | `bigint` | ✓ |
| `arquivo_id` | `bigint` | ✓ |
| `tipo_valor_analise_enum` | `int` | ✓ |
| `responsavel_id` | `bigint` | ✓ |
| `resultado_interpretacao_amostra` | `bigint` | ✓ |
| `quantidade_reanalise` | `int` | ✓ |
| `origem_reanalise_enum` | `int` | ✓ |
| `responsavel_reanalise_id` | `bigint` | ✓ |
| `status_resultado_analise` | `smallint` | ✓ |
| `parametro_interpretacao_valor_id` | `bigint` | ✓ |
| `grupo_trabalho_id` | `bigint` | ✓ |
| `resultado_sugerido_parametro` | `varchar` | ✓ |

#### Tabela: `tipo_compartimento_traducao`

**Colunas**: 7

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `tipo_compartimento_id` | `bigint` | ✓ |
| `locale` | `varchar` | ✓ |
| `version` | `bigint` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `descricao` | `varchar` | ✓ |
| `nome` | `varchar` | ✓ |

#### Tabela: `tipo_produto`

**Colunas**: 8

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `ativo` | `bit` | ✓ |
| `nome` | `varchar` | ✓ |
| `programa_id` | `bigint` | ✓ |
| `quantidade_kits` | `int` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |

#### Tabela: `usuario`

**Colunas**: 31

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `ativo` | `bit` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `email` | `varchar` | ✓ |
| `foto_id` | `bigint` | ✓ |
| `login` | `varchar` | ✓ |
| `nome_completo` | `varchar` | ✓ |
| `senha` | `varchar` | ✓ |
| `identidade_visual_id` | `bigint` | ✓ |
| `cargo` | `varchar` | ✓ |
| `celular` | `varchar` | ✓ |
| `data_ultimo_login` | `datetime2` | ✓ |
| `exibir_interpretacao` | `bit` | ✓ |
| `receber_anexo` | `bit` | ✓ |
| `telefone` | `varchar` | ✓ |
| `laboratorio_padrao_id` | `bigint` | ✓ |
| `resultado_email_enum` | `int` | ✓ |
| `idioma` | `varchar` | ✓ |
| `layout_exportacao` | `varchar` | ✓ |
| `identificador_hub_spot` | `bigint` | ✓ |
| `data_atualizacao_hubspot` | `datetime2` | ✓ |
| `email_invalido` | `bit` | ✓ |
| `time_zone` | `varchar` | ✓ |
| `tipo_ordenacao` | `varchar` | ✓ |
| `pode_gerenciar_senha` | `bit` | ✓ |
| `locked` | `bit` | ✓ |
| `zipped_attachment` | `bit` | ✓ |
| `send_brand_on_sample_result_email` | `bit` | ✓ |
| `rule_to_send_sample_result_email_enum` | `varchar` | ✓ |

### Schema: `bronze_zoho`

#### Tabela: `accounts`

**Colunas**: 162

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `$field_states` | `varchar` | ✓ |
| `id_protheus` | `varchar` | ✓ |
| `zohocrmforprotheus__cliente_totvs` | `varchar` | ✓ |
| `payment_type` | `varchar` | ✓ |
| `average_samples_per_month_last_6_months_trend` | `varchar` | ✓ |
| `zohocontracts__contracts_counterparty_id` | `varchar` | ✓ |
| `zohocrmforprotheus__integration_status` | `varchar` | ✓ |
| `matriz` | `varchar` | ✓ |
| `$state` | `varchar` | ✓ |
| `$process_flow` | `varchar` | ✓ |
| `billing_country` | `varchar` | ✓ |
| `customer_portf_lio` | `varchar` | ✓ |
| `signed_contract` | `varchar` | ✓ |
| `id` | `varchar` | ✓ |
| `status` | `varchar` | ✓ |
| `past_due` | `varchar` | ✓ |
| `predefined_packages` | `varchar` | ✓ |
| `created_time` | `varchar` | ✓ |
| `payment_method` | `varchar` | ✓ |
| `phone_primary` | `varchar` | ✓ |
| `nps_satisfa_o` | `varchar` | ✓ |
| `billing_city` | `varchar` | ✓ |
| `initial_quantity_of_active_equipment` | `varchar` | ✓ |
| `description` | `varchar` | ✓ |
| `customer_segmentation` | `varchar` | ✓ |
| `indication` | `varchar` | ✓ |
| `website` | `varchar` | ✓ |
| `trade_name` | `varchar` | ✓ |
| `record_image` | `varchar` | ✓ |
| `business_number` | `varchar` | ✓ |
| `payment_terms` | `varchar` | ✓ |
| `zohocrmforprotheus__totvs_type` | `varchar` | ✓ |
| `fixed_or_mobile` | `varchar` | ✓ |
| `maintenanc_e_software_nica_9` | `varchar` | ✓ |
| `zohocrmforprotheus__sync_status` | `varchar` | ✓ |
| `account_name` | `varchar` | ✓ |
| `primary_mail` | `varchar` | ✓ |
| `zohocrmforprotheus__contribuinte_totvs` | `varchar` | ✓ |
| `contract_expiry_date` | `varchar` | ✓ |
| `zohocrmforprotheus__store_totvs` | `varchar` | ✓ |
| `$orchestration` | `varchar` | ✓ |
| `contact_name` | `varchar` | ✓ |
| `customer_notes` | `varchar` | ✓ |
| `zohocrmforprotheus__payment_term` | `varchar` | ✓ |
| `contract_start_date` | `varchar` | ✓ |
| `zohocrmforprotheus__freight_type_totvs` | `varchar` | ✓ |
| `locked__s` | `varchar` | ✓ |
| `originating_lead` | `varchar` | ✓ |
| `real_status` | `varchar` | ✓ |
| `zohocrmforprotheus__status` | `varchar` | ✓ |
| `tag` | `varchar` | ✓ |
| `zohocrmforprotheus__price_book` | `varchar` | ✓ |
| `nearby_distance__s` | `varchar` | ✓ |
| `$currency_symbol` | `varchar` | ✓ |
| `evolution_of_monitoring_coverage` | `varchar` | ✓ |
| `currency1` | `varchar` | ✓ |
| `ttm_sales` | `varchar` | ✓ |
| `contract_status1` | `varchar` | ✓ |
| `cod_account_type` | `varchar` | ✓ |
| `last_activity_time` | `varchar` | ✓ |
| `company_website_lead_crm` | `varchar` | ✓ |
| `$locked_for_me` | `varchar` | ✓ |
| `$approved` | `varchar` | ✓ |
| `alert_criticality_rate_last_6_months` | `varchar` | ✓ |
| `billing_street` | `varchar` | ✓ |
| `account_team` | `varchar` | ✓ |
| `zohocrmforprotheus__integration_result` | `varchar` | ✓ |
| `zohocrmforprotheus__loja_totvs` | `varchar` | ✓ |
| `$editable` | `varchar` | ✓ |
| `billing_code` | `varchar` | ✓ |
| `mobile_cont` | `varchar` | ✓ |
| `sales_ytd_vs_ly` | `varchar` | ✓ |
| `specific_packages` | `varchar` | ✓ |
| `neighborhood` | `varchar` | ✓ |
| `brand` | `varchar` | ✓ |
| `state_registration_number` | `varchar` | ✓ |
| `company_name` | `varchar` | ✓ |
| `average_tat_last_3_months` | `varchar` | ✓ |
| `$zia_owner_assignment` | `varchar` | ✓ |
| `additional_address_details` | `varchar` | ✓ |
| `$is_duplicate` | `varchar` | ✓ |
| `last_complaint` | `varchar` | ✓ |
| `top_3_pieces_of_equipment` | `varchar` | ✓ |
| `equipment_monitoredin_the_last_24_months_active` | `varchar` | ✓ |
| `credit_limit` | `varchar` | ✓ |
| `outstanding_proposal` | `varchar` | ✓ |
| `child_accounts` | `varchar` | ✓ |
| `accounts_type` | `varchar` | ✓ |
| `use_maintenance_software` | `varchar` | ✓ |
| `samples_with_pre_registration_last_3_months` | `varchar` | ✓ |
| `segment` | `varchar` | ✓ |
| `$review` | `varchar` | ✓ |
| `als_business_unit` | `varchar` | ✓ |
| `linha_nica_8` | `varchar` | ✓ |
| `number` | `varchar` | ✓ |
| `phone` | `varchar` | ✓ |
| `zohocrmforprotheus__cod_pais_totvs` | `varchar` | ✓ |
| `modified_time` | `varchar` | ✓ |
| `sector` | `varchar` | ✓ |
| `cod_sector` | `varchar` | ✓ |
| `equipment_monitored_in_the_last_24_months_active` | `varchar` | ✓ |
| `matriz_filial` | `varchar` | ✓ |
| `account_rating` | `varchar` | ✓ |
| `zohocrmforprotheus__sales_representative` | `varchar` | ✓ |
| `parent_account` | `varchar` | ✓ |
| `legal_person` | `varchar` | ✓ |
| `$in_merge` | `varchar` | ✓ |
| `cod_segment` | `varchar` | ✓ |
| `billing_state` | `varchar` | ✓ |
| `$approval_state` | `varchar` | ✓ |
| `owner_name` | `varchar` | ✓ |
| `owner_id` | `varchar` | ✓ |
| `owner_email` | `varchar` | ✓ |
| `$approval_delegate` | `varchar` | ✓ |
| `$approval_add_approver` | `varchar` | ✓ |
| `$approval_takeover` | `varchar` | ✓ |
| `$approval_approve` | `varchar` | ✓ |
| `$approval_reject` | `varchar` | ✓ |
| `$approval_resubmit` | `varchar` | ✓ |
| `primary_contact_for_results_name` | `varchar` | ✓ |
| `primary_contact_for_results_id` | `varchar` | ✓ |
| `main_financial_contact_name` | `varchar` | ✓ |
| `main_financial_contact_id` | `varchar` | ✓ |
| `created_by_name` | `varchar` | ✓ |
| `created_by_id` | `varchar` | ✓ |
| `created_by_email` | `varchar` | ✓ |
| `$review_process_approve` | `varchar` | ✓ |
| `$review_process_reject` | `varchar` | ✓ |
| `$review_process_resubmit` | `varchar` | ✓ |
| `primary_contact_name` | `varchar` | ✓ |
| `primary_contact_id` | `varchar` | ✓ |
| `co_owner_name` | `varchar` | ✓ |
| `co_owner_id` | `varchar` | ✓ |
| `primary_contact_for_billing_name` | `varchar` | ✓ |
| `primary_contact_for_billing_id` | `varchar` | ✓ |
| `$layout_id_display_label` | `varchar` | ✓ |
| `$layout_id_name` | `varchar` | ✓ |
| `$layout_id_id` | `varchar` | ✓ |
| `modified_by_name` | `varchar` | ✓ |
| `modified_by_id` | `varchar` | ✓ |
| `modified_by_email` | `varchar` | ✓ |
| `primary_contact_for_results` | `varchar` | ✓ |
| `main_financial_contact` | `varchar` | ✓ |
| `primary_contact` | `varchar` | ✓ |
| `co_owner` | `varchar` | ✓ |
| `primary_contact_for_billing` | `varchar` | ✓ |
| `zohocrmforprotheus__payment_term_name` | `varchar` | ✓ |
| `zohocrmforprotheus__payment_term_id` | `varchar` | ✓ |
| `zohocrmforprotheus__sales_representative_name` | `varchar` | ✓ |
| `zohocrmforprotheus__sales_representative_id` | `varchar` | ✓ |
| `zohocrmforprotheus__price_book_name` | `varchar` | ✓ |
| `zohocrmforprotheus__price_book_id` | `varchar` | ✓ |
| `matriz_name` | `varchar` | ✓ |
| `matriz_id` | `varchar` | ✓ |
| `indication_name` | `varchar` | ✓ |
| `indication_id` | `varchar` | ✓ |
| `child_accounts_name` | `varchar` | ✓ |
| `child_accounts_id` | `varchar` | ✓ |
| `parent_account_name` | `varchar` | ✓ |
| `parent_account_id` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `calls`

**Colunas**: 56

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `call_duration` | `varchar` | ✓ |
| `description` | `varchar` | ✓ |
| `$currency_symbol` | `varchar` | ✓ |
| `caller_id` | `varchar` | ✓ |
| `$calendar_booking_call` | `varchar` | ✓ |
| `$field_states` | `varchar` | ✓ |
| `$review_process` | `varchar` | ✓ |
| `call_result_description` | `varchar` | ✓ |
| `last_activity_time` | `varchar` | ✓ |
| `call_agenda` | `varchar` | ✓ |
| `$review` | `varchar` | ✓ |
| `$state` | `varchar` | ✓ |
| `$process_flow` | `varchar` | ✓ |
| `call_purpose` | `varchar` | ✓ |
| `id` | `varchar` | ✓ |
| `call_status` | `varchar` | ✓ |
| `$approved` | `varchar` | ✓ |
| `modified_time` | `varchar` | ✓ |
| `call_transcription__c` | `varchar` | ✓ |
| `reminder` | `varchar` | ✓ |
| `created_time` | `varchar` | ✓ |
| `call_start_time` | `varchar` | ✓ |
| `$editable` | `varchar` | ✓ |
| `subject` | `varchar` | ✓ |
| `$orchestration` | `varchar` | ✓ |
| `$se_module` | `varchar` | ✓ |
| `call_type` | `varchar` | ✓ |
| `call_result` | `varchar` | ✓ |
| `$in_merge` | `varchar` | ✓ |
| `call_duration_in_seconds` | `varchar` | ✓ |
| `tag` | `varchar` | ✓ |
| `dialled_number` | `varchar` | ✓ |
| `$approval_state` | `varchar` | ✓ |
| `owner_name` | `varchar` | ✓ |
| `owner_id` | `varchar` | ✓ |
| `owner_email` | `varchar` | ✓ |
| `modified_by_name` | `varchar` | ✓ |
| `modified_by_id` | `varchar` | ✓ |
| `modified_by_email` | `varchar` | ✓ |
| `who_id_name` | `varchar` | ✓ |
| `who_id_id` | `varchar` | ✓ |
| `$approval_delegate` | `varchar` | ✓ |
| `$approval_add_approver` | `varchar` | ✓ |
| `$approval_takeover` | `varchar` | ✓ |
| `$approval_approve` | `varchar` | ✓ |
| `$approval_reject` | `varchar` | ✓ |
| `$approval_resubmit` | `varchar` | ✓ |
| `what_id_name` | `varchar` | ✓ |
| `what_id_id` | `varchar` | ✓ |
| `created_by_name` | `varchar` | ✓ |
| `created_by_id` | `varchar` | ✓ |
| `created_by_email` | `varchar` | ✓ |
| `who_id` | `varchar` | ✓ |
| `what_id` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `campaigns`

**Colunas**: 66

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `$currency_symbol` | `varchar` | ✓ |
| `$field_states` | `varchar` | ✓ |
| `native__campaigns__extn__sender_name` | `varchar` | ✓ |
| `last_activity_time` | `varchar` | ✓ |
| `native__webinar__extn__webinar_duration` | `varchar` | ✓ |
| `budgeted_cost1` | `varchar` | ✓ |
| `$state` | `varchar` | ✓ |
| `num_sent` | `varchar` | ✓ |
| `$process_flow` | `varchar` | ✓ |
| `actual_cost` | `varchar` | ✓ |
| `native__webinar__extn__webinar_launch_url` | `varchar` | ✓ |
| `id` | `varchar` | ✓ |
| `native__webinar__extn__webinar_registration_url` | `varchar` | ✓ |
| `$approved` | `varchar` | ✓ |
| `native__survey__extn__survey_type` | `varchar` | ✓ |
| `actual_cost1` | `varchar` | ✓ |
| `status` | `varchar` | ✓ |
| `native__survey__extn__survey_department` | `varchar` | ✓ |
| `created_time` | `varchar` | ✓ |
| `native__campaigns__extn__sender_address` | `varchar` | ✓ |
| `$editable` | `varchar` | ✓ |
| `native__survey__extn__survey` | `varchar` | ✓ |
| `native__survey__extn__survey_url` | `varchar` | ✓ |
| `native__campaigns__extn__reply_to_address` | `varchar` | ✓ |
| `budgeted_cost` | `varchar` | ✓ |
| `description` | `varchar` | ✓ |
| `campaign_name` | `varchar` | ✓ |
| `$review_process` | `varchar` | ✓ |
| `native__campaigns__extn__campaign_subject` | `varchar` | ✓ |
| `end_date` | `varchar` | ✓ |
| `$review` | `varchar` | ✓ |
| `expected_revenue` | `varchar` | ✓ |
| `expected_response` | `varchar` | ✓ |
| `start_date` | `varchar` | ✓ |
| `native__survey__extn__department_id` | `varchar` | ✓ |
| `modified_time` | `varchar` | ✓ |
| `native__webinar__extn__webinar_schedule` | `varchar` | ✓ |
| `$orchestration` | `varchar` | ✓ |
| `type` | `varchar` | ✓ |
| `$in_merge` | `varchar` | ✓ |
| `tag` | `varchar` | ✓ |
| `parent_campaign` | `varchar` | ✓ |
| `$approval_state` | `varchar` | ✓ |
| `owner_name` | `varchar` | ✓ |
| `owner_id` | `varchar` | ✓ |
| `owner_email` | `varchar` | ✓ |
| `$approval_delegate` | `varchar` | ✓ |
| `$approval_add_approver` | `varchar` | ✓ |
| `$approval_takeover` | `varchar` | ✓ |
| `$approval_approve` | `varchar` | ✓ |
| `$approval_reject` | `varchar` | ✓ |
| `$approval_resubmit` | `varchar` | ✓ |
| `created_by_name` | `varchar` | ✓ |
| `created_by_id` | `varchar` | ✓ |
| `created_by_email` | `varchar` | ✓ |
| `$layout_id_display_label` | `varchar` | ✓ |
| `$layout_id_name` | `varchar` | ✓ |
| `$layout_id_id` | `varchar` | ✓ |
| `modified_by_name` | `varchar` | ✓ |
| `modified_by_id` | `varchar` | ✓ |
| `modified_by_email` | `varchar` | ✓ |
| `layout_display_label` | `varchar` | ✓ |
| `layout_name` | `varchar` | ✓ |
| `layout_id` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `cases`

**Colunas**: 67

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `email` | `varchar` | ✓ |
| `description` | `varchar` | ✓ |
| `$currency_symbol` | `varchar` | ✓ |
| `internal_comments` | `varchar` | ✓ |
| `$field_states` | `varchar` | ✓ |
| `no_of_comments` | `varchar` | ✓ |
| `reported_by` | `varchar` | ✓ |
| `case_number` | `varchar` | ✓ |
| `last_activity_time` | `varchar` | ✓ |
| `$review` | `varchar` | ✓ |
| `$state` | `varchar` | ✓ |
| `$process_flow` | `varchar` | ✓ |
| `deal_name` | `varchar` | ✓ |
| `phone` | `varchar` | ✓ |
| `$locked_for_me` | `varchar` | ✓ |
| `account_name` | `varchar` | ✓ |
| `id` | `varchar` | ✓ |
| `$approved` | `varchar` | ✓ |
| `solution` | `varchar` | ✓ |
| `status` | `varchar` | ✓ |
| `modified_time` | `varchar` | ✓ |
| `priority` | `varchar` | ✓ |
| `created_time` | `varchar` | ✓ |
| `comments` | `varchar` | ✓ |
| `product_name` | `varchar` | ✓ |
| `$editable` | `varchar` | ✓ |
| `add_comment` | `varchar` | ✓ |
| `case_origin` | `varchar` | ✓ |
| `case_reason` | `varchar` | ✓ |
| `subject` | `varchar` | ✓ |
| `$orchestration` | `varchar` | ✓ |
| `type` | `varchar` | ✓ |
| `$in_merge` | `varchar` | ✓ |
| `locked__s` | `varchar` | ✓ |
| `tag` | `varchar` | ✓ |
| `$zia_owner_assignment` | `varchar` | ✓ |
| `$approval_state` | `varchar` | ✓ |
| `related_to` | `varchar` | ✓ |
| `owner_name` | `varchar` | ✓ |
| `owner_id` | `varchar` | ✓ |
| `owner_email` | `varchar` | ✓ |
| `$review_process_approve` | `varchar` | ✓ |
| `$review_process_reject` | `varchar` | ✓ |
| `$review_process_resubmit` | `varchar` | ✓ |
| `$layout_id_display_label` | `varchar` | ✓ |
| `$layout_id_name` | `varchar` | ✓ |
| `$layout_id_id` | `varchar` | ✓ |
| `modified_by_name` | `varchar` | ✓ |
| `modified_by_id` | `varchar` | ✓ |
| `modified_by_email` | `varchar` | ✓ |
| `$approval_delegate` | `varchar` | ✓ |
| `$approval_add_approver` | `varchar` | ✓ |
| `$approval_takeover` | `varchar` | ✓ |
| `$approval_approve` | `varchar` | ✓ |
| `$approval_reject` | `varchar` | ✓ |
| `$approval_resubmit` | `varchar` | ✓ |
| `created_by_name` | `varchar` | ✓ |
| `created_by_id` | `varchar` | ✓ |
| `created_by_email` | `varchar` | ✓ |
| `account_name_name` | `varchar` | ✓ |
| `account_name_id` | `varchar` | ✓ |
| `related_to_name` | `varchar` | ✓ |
| `related_to_id` | `varchar` | ✓ |
| `product_name_name` | `varchar` | ✓ |
| `product_name_id` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `contacts`

**Colunas**: 103

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `email` | `varchar` | ✓ |
| `gclid` | `varchar` | ✓ |
| `$currency_symbol` | `varchar` | ✓ |
| `linkedin_url_lead_crm` | `varchar` | ✓ |
| `visitor_score` | `varchar` | ✓ |
| `$field_states` | `varchar` | ✓ |
| `utm_term_ctt` | `varchar` | ✓ |
| `last_activity_time` | `varchar` | ✓ |
| `hierarchy` | `varchar` | ✓ |
| `$state` | `varchar` | ✓ |
| `unsubscribed_mode` | `varchar` | ✓ |
| `$process_flow` | `varchar` | ✓ |
| `last_message_sent_on_leadcrm` | `varchar` | ✓ |
| `utm_medium_ctt` | `varchar` | ✓ |
| `ad_network` | `varchar` | ✓ |
| `$locked_for_me` | `varchar` | ✓ |
| `id` | `varchar` | ✓ |
| `$approved` | `varchar` | ✓ |
| `conversion_exported_on` | `varchar` | ✓ |
| `invite_accepted_on_leadcrm` | `varchar` | ✓ |
| `last_response_received_on_leadcrm` | `varchar` | ✓ |
| `status` | `varchar` | ✓ |
| `rapport` | `varchar` | ✓ |
| `cost_per_click` | `varchar` | ✓ |
| `first_visited_url` | `varchar` | ✓ |
| `days_visited` | `varchar` | ✓ |
| `click_type` | `varchar` | ✓ |
| `created_time` | `varchar` | ✓ |
| `$editable` | `varchar` | ✓ |
| `adgroup_name` | `varchar` | ✓ |
| `best_time_to_contact` | `varchar` | ✓ |
| `linkedin` | `varchar` | ✓ |
| `ad_click_date` | `varchar` | ✓ |
| `lead_source_lead_crm` | `varchar` | ✓ |
| `last_visited_time` | `varchar` | ✓ |
| `$zia_owner_assignment` | `varchar` | ✓ |
| `$is_duplicate` | `varchar` | ✓ |
| `last_interaction` | `varchar` | ✓ |
| `id_account` | `varchar` | ✓ |
| `description` | `varchar` | ✓ |
| `ad` | `varchar` | ✓ |
| `number_of_chats` | `varchar` | ✓ |
| `search_partner_network` | `varchar` | ✓ |
| `average_time_spent_minutes` | `varchar` | ✓ |
| `salutation` | `varchar` | ✓ |
| `first_name` | `varchar` | ✓ |
| `full_name` | `varchar` | ✓ |
| `record_image` | `varchar` | ✓ |
| `conversion_export_status` | `varchar` | ✓ |
| `cost_per_conversion` | `varchar` | ✓ |
| `$review` | `varchar` | ✓ |
| `als_business_unit` | `varchar` | ✓ |
| `decision_level` | `varchar` | ✓ |
| `phone` | `varchar` | ✓ |
| `utm_source_ctt` | `varchar` | ✓ |
| `utm_campaign_ctt` | `varchar` | ✓ |
| `utm_content_ctt` | `varchar` | ✓ |
| `modified_time` | `varchar` | ✓ |
| `departments` | `varchar` | ✓ |
| `keyword` | `varchar` | ✓ |
| `unsubscribed_time` | `varchar` | ✓ |
| `device_type` | `varchar` | ✓ |
| `google_ads_campaign_id_ctt` | `varchar` | ✓ |
| `job_title` | `varchar` | ✓ |
| `mobile` | `varchar` | ✓ |
| `$orchestration` | `varchar` | ✓ |
| `first_visited_time` | `varchar` | ✓ |
| `last_name` | `varchar` | ✓ |
| `$in_merge` | `varchar` | ✓ |
| `ad_campaign_name` | `varchar` | ✓ |
| `referrer` | `varchar` | ✓ |
| `job_title_category` | `varchar` | ✓ |
| `locked__s` | `varchar` | ✓ |
| `originating_lead` | `varchar` | ✓ |
| `tag` | `varchar` | ✓ |
| `$approval_state` | `varchar` | ✓ |
| `reason_for_conversion_failure` | `varchar` | ✓ |
| `owner_name` | `varchar` | ✓ |
| `owner_id` | `varchar` | ✓ |
| `owner_email` | `varchar` | ✓ |
| `$approval_delegate` | `varchar` | ✓ |
| `$approval_add_approver` | `varchar` | ✓ |
| `$approval_takeover` | `varchar` | ✓ |
| `$approval_approve` | `varchar` | ✓ |
| `$approval_reject` | `varchar` | ✓ |
| `$approval_resubmit` | `varchar` | ✓ |
| `created_by_name` | `varchar` | ✓ |
| `created_by_id` | `varchar` | ✓ |
| `created_by_email` | `varchar` | ✓ |
| `$review_process_approve` | `varchar` | ✓ |
| `$review_process_reject` | `varchar` | ✓ |
| `$review_process_resubmit` | `varchar` | ✓ |
| `$layout_id_display_label` | `varchar` | ✓ |
| `$layout_id_name` | `varchar` | ✓ |
| `$layout_id_id` | `varchar` | ✓ |
| `modified_by_name` | `varchar` | ✓ |
| `modified_by_id` | `varchar` | ✓ |
| `modified_by_email` | `varchar` | ✓ |
| `account_name_name` | `varchar` | ✓ |
| `account_name_id` | `varchar` | ✓ |
| `account_name` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `deals`

**Colunas**: 95

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `gclid` | `varchar` | ✓ |
| `$currency_symbol` | `varchar` | ✓ |
| `$field_states` | `varchar` | ✓ |
| `status_atividade` | `varchar` | ✓ |
| `last_activity_time` | `varchar` | ✓ |
| `$state` | `varchar` | ✓ |
| `origem_lead` | `varchar` | ✓ |
| `$process_flow` | `varchar` | ✓ |
| `deal_name` | `varchar` | ✓ |
| `est_close_date` | `varchar` | ✓ |
| `date_quote_sent` | `varchar` | ✓ |
| `deal_currency` | `varchar` | ✓ |
| `source_campaing` | `varchar` | ✓ |
| `ad_network` | `varchar` | ✓ |
| `stage` | `varchar` | ✓ |
| `$locked_for_me` | `varchar` | ✓ |
| `id` | `varchar` | ✓ |
| `term_months` | `varchar` | ✓ |
| `last_completed_call_acc` | `varchar` | ✓ |
| `$approved` | `varchar` | ✓ |
| `conversion_exported_on` | `varchar` | ✓ |
| `cost_per_click` | `varchar` | ✓ |
| `click_type` | `varchar` | ✓ |
| `created_time` | `varchar` | ✓ |
| `$editable` | `varchar` | ✓ |
| `adgroup_name` | `varchar` | ✓ |
| `em_risco_abandono` | `varchar` | ✓ |
| `already_does_analysis` | `varchar` | ✓ |
| `ad_click_date` | `varchar` | ✓ |
| `$zia_owner_assignment` | `varchar` | ✓ |
| `initial_quantity_of_active_equipment` | `varchar` | ✓ |
| `id_account` | `varchar` | ✓ |
| `description` | `varchar` | ✓ |
| `ad` | `varchar` | ✓ |
| `search_partner_network` | `varchar` | ✓ |
| `closing_date` | `varchar` | ✓ |
| `reason_for_loss__s` | `varchar` | ✓ |
| `conversion_export_status` | `varchar` | ✓ |
| `cost_per_conversion` | `varchar` | ✓ |
| `$review` | `varchar` | ✓ |
| `lead_conversion_time` | `varchar` | ✓ |
| `als_business_unit` | `varchar` | ✓ |
| `overall_sales_duration` | `varchar` | ✓ |
| `leadchain0__social_lead_id` | `varchar` | ✓ |
| `quote_status` | `varchar` | ✓ |
| `topic` | `varchar` | ✓ |
| `modified_time` | `varchar` | ✓ |
| `keyword` | `varchar` | ✓ |
| `device_type` | `varchar` | ✓ |
| `probability` | `varchar` | ✓ |
| `anexo` | `varchar` | ✓ |
| `$orchestration` | `varchar` | ✓ |
| `sales_cycle_duration` | `varchar` | ✓ |
| `amount1` | `varchar` | ✓ |
| `$in_merge` | `varchar` | ✓ |
| `ad_campaign_name` | `varchar` | ✓ |
| `locked__s` | `varchar` | ✓ |
| `originating_lead` | `varchar` | ✓ |
| `tag` | `varchar` | ✓ |
| `difficulty_encountered_in_the_company` | `varchar` | ✓ |
| `opportunity_type` | `varchar` | ✓ |
| `$approval_state` | `varchar` | ✓ |
| `reason_for_conversion_failure` | `varchar` | ✓ |
| `owner_name` | `varchar` | ✓ |
| `owner_id` | `varchar` | ✓ |
| `owner_email` | `varchar` | ✓ |
| `$approval_delegate` | `varchar` | ✓ |
| `$approval_add_approver` | `varchar` | ✓ |
| `$approval_takeover` | `varchar` | ✓ |
| `$approval_approve` | `varchar` | ✓ |
| `$approval_reject` | `varchar` | ✓ |
| `$approval_resubmit` | `varchar` | ✓ |
| `created_by_name` | `varchar` | ✓ |
| `created_by_id` | `varchar` | ✓ |
| `created_by_email` | `varchar` | ✓ |
| `campaign_source_name` | `varchar` | ✓ |
| `campaign_source_id` | `varchar` | ✓ |
| `$review_process_approve` | `varchar` | ✓ |
| `$review_process_reject` | `varchar` | ✓ |
| `$review_process_resubmit` | `varchar` | ✓ |
| `$layout_id_display_label` | `varchar` | ✓ |
| `$layout_id_name` | `varchar` | ✓ |
| `$layout_id_id` | `varchar` | ✓ |
| `modified_by_name` | `varchar` | ✓ |
| `modified_by_id` | `varchar` | ✓ |
| `modified_by_email` | `varchar` | ✓ |
| `account_name_name` | `varchar` | ✓ |
| `account_name_id` | `varchar` | ✓ |
| `contact_name_name` | `varchar` | ✓ |
| `contact_name_id` | `varchar` | ✓ |
| `campaign_source` | `varchar` | ✓ |
| `contact_name` | `varchar` | ✓ |
| `account_name` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `events`

**Colunas**: 75

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `all_day` | `varchar` | ✓ |
| `check_in_state` | `varchar` | ✓ |
| `$currency_symbol` | `varchar` | ✓ |
| `$field_states` | `varchar` | ✓ |
| `latitude` | `varchar` | ✓ |
| `participants` | `varchar` | ✓ |
| `last_activity_time` | `varchar` | ✓ |
| `$state` | `varchar` | ✓ |
| `$process_flow` | `varchar` | ✓ |
| `check_in_city` | `varchar` | ✓ |
| `id` | `varchar` | ✓ |
| `check_in_comment` | `varchar` | ✓ |
| `$approved` | `varchar` | ✓ |
| `remind_at` | `varchar` | ✓ |
| `check_in_status` | `varchar` | ✓ |
| `venue` | `varchar` | ✓ |
| `zip_code` | `varchar` | ✓ |
| `created_time` | `varchar` | ✓ |
| `$editable` | `varchar` | ✓ |
| `longitude` | `varchar` | ✓ |
| `check_in_time` | `varchar` | ✓ |
| `recurring_activity` | `varchar` | ✓ |
| `meeting_notes_internal` | `varchar` | ✓ |
| `check_in_address` | `varchar` | ✓ |
| `description` | `varchar` | ✓ |
| `start_datetime` | `varchar` | ✓ |
| `meeting_format` | `varchar` | ✓ |
| `$review_process` | `varchar` | ✓ |
| `event_title` | `varchar` | ✓ |
| `$calendar_booking_event` | `varchar` | ✓ |
| `check_in_by` | `varchar` | ✓ |
| `end_datetime` | `varchar` | ✓ |
| `$review` | `varchar` | ✓ |
| `meeting_status` | `varchar` | ✓ |
| `check_in_country` | `varchar` | ✓ |
| `modified_time` | `varchar` | ✓ |
| `$recurrence_id` | `varchar` | ✓ |
| `$orchestration` | `varchar` | ✓ |
| `$se_module` | `varchar` | ✓ |
| `check_in_sub_locality` | `varchar` | ✓ |
| `$in_merge` | `varchar` | ✓ |
| `$meeting_details` | `varchar` | ✓ |
| `$u_id` | `varchar` | ✓ |
| `tag` | `varchar` | ✓ |
| `$send_notification` | `varchar` | ✓ |
| `$approval_state` | `varchar` | ✓ |
| `owner_name` | `varchar` | ✓ |
| `owner_id` | `varchar` | ✓ |
| `owner_email` | `varchar` | ✓ |
| `who_id_name` | `varchar` | ✓ |
| `who_id_id` | `varchar` | ✓ |
| `$approval_delegate` | `varchar` | ✓ |
| `$approval_add_approver` | `varchar` | ✓ |
| `$approval_takeover` | `varchar` | ✓ |
| `$approval_approve` | `varchar` | ✓ |
| `$approval_reject` | `varchar` | ✓ |
| `$approval_resubmit` | `varchar` | ✓ |
| `what_id_name` | `varchar` | ✓ |
| `what_id_id` | `varchar` | ✓ |
| `created_by_name` | `varchar` | ✓ |
| `created_by_id` | `varchar` | ✓ |
| `created_by_email` | `varchar` | ✓ |
| `modified_by_name` | `varchar` | ✓ |
| `modified_by_id` | `varchar` | ✓ |
| `modified_by_email` | `varchar` | ✓ |
| `who_id` | `varchar` | ✓ |
| `$meeting_details_tool_name` | `varchar` | ✓ |
| `$meeting_details_joinmeeting_url` | `varchar` | ✓ |
| `$meeting_details_startmeeting_url` | `varchar` | ✓ |
| `what_id` | `varchar` | ✓ |
| `$meeting_details_meeting_attendees_details_wallace_viana@alsglobal_com_attendeename` | `varchar` | ✓ |
| `$meeting_details_meeting_attendees_details_wallace_viana@alsglobal_com_leavetime` | `varchar` | ✓ |
| `$meeting_details_meeting_attendees_details_wallace_viana@alsglobal_com_jointime` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `invoices`

**Colunas**: 83

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `$currency_symbol` | `varchar` | ✓ |
| `$field_states` | `varchar` | ✓ |
| `tax` | `varchar` | ✓ |
| `last_activity_time` | `varchar` | ✓ |
| `$state` | `varchar` | ✓ |
| `$process_flow` | `varchar` | ✓ |
| `billing_country` | `varchar` | ✓ |
| `$locked_for_me` | `varchar` | ✓ |
| `id` | `varchar` | ✓ |
| `zohocrmforprotheus__document_totvs` | `varchar` | ✓ |
| `$approved` | `varchar` | ✓ |
| `status` | `varchar` | ✓ |
| `grand_total` | `varchar` | ✓ |
| `adjustment` | `varchar` | ✓ |
| `billing_street` | `varchar` | ✓ |
| `created_time` | `varchar` | ✓ |
| `$editable` | `varchar` | ✓ |
| `billing_code` | `varchar` | ✓ |
| `product_details` | `varchar` | ✓ |
| `excise_duty` | `varchar` | ✓ |
| `shipping_city` | `varchar` | ✓ |
| `shipping_country` | `varchar` | ✓ |
| `shipping_code` | `varchar` | ✓ |
| `billing_city` | `varchar` | ✓ |
| `purchase_order` | `varchar` | ✓ |
| `shipping_street` | `varchar` | ✓ |
| `description` | `varchar` | ✓ |
| `discount` | `varchar` | ✓ |
| `shipping_state` | `varchar` | ✓ |
| `zohocrmforprotheus__delivery_customer` | `varchar` | ✓ |
| `invoice_date` | `varchar` | ✓ |
| `$review` | `varchar` | ✓ |
| `zohocrmforprotheus__sync_status` | `varchar` | ✓ |
| `zohocrmforprotheus__nfe_key` | `varchar` | ✓ |
| `sales_order` | `varchar` | ✓ |
| `zohocrmforprotheus__stamped_date` | `varchar` | ✓ |
| `sales_commission` | `varchar` | ✓ |
| `modified_time` | `varchar` | ✓ |
| `due_date` | `varchar` | ✓ |
| `terms_and_conditions` | `varchar` | ✓ |
| `sub_total` | `varchar` | ✓ |
| `invoice_number` | `varchar` | ✓ |
| `zohocrmforprotheus__sales_representative` | `varchar` | ✓ |
| `subject` | `varchar` | ✓ |
| `$orchestration` | `varchar` | ✓ |
| `contact_name` | `varchar` | ✓ |
| `zohocrmforprotheus__payment_term` | `varchar` | ✓ |
| `zohocrmforprotheus__document_type` | `varchar` | ✓ |
| `$in_merge` | `varchar` | ✓ |
| `locked__s` | `varchar` | ✓ |
| `billing_state` | `varchar` | ✓ |
| `$line_tax` | `varchar` | ✓ |
| `tag` | `varchar` | ✓ |
| `zohocrmforprotheus__stamped_nfe` | `varchar` | ✓ |
| `$approval_state` | `varchar` | ✓ |
| `zohocrmforprotheus__price_book` | `varchar` | ✓ |
| `owner_name` | `varchar` | ✓ |
| `owner_id` | `varchar` | ✓ |
| `owner_email` | `varchar` | ✓ |
| `$approval_delegate` | `varchar` | ✓ |
| `$approval_add_approver` | `varchar` | ✓ |
| `$approval_takeover` | `varchar` | ✓ |
| `$approval_approve` | `varchar` | ✓ |
| `$approval_reject` | `varchar` | ✓ |
| `$approval_resubmit` | `varchar` | ✓ |
| `created_by_name` | `varchar` | ✓ |
| `created_by_id` | `varchar` | ✓ |
| `created_by_email` | `varchar` | ✓ |
| `$review_process_approve` | `varchar` | ✓ |
| `$review_process_reject` | `varchar` | ✓ |
| `$review_process_resubmit` | `varchar` | ✓ |
| `$layout_id_display_label` | `varchar` | ✓ |
| `$layout_id_name` | `varchar` | ✓ |
| `$layout_id_id` | `varchar` | ✓ |
| `modified_by_name` | `varchar` | ✓ |
| `modified_by_id` | `varchar` | ✓ |
| `modified_by_email` | `varchar` | ✓ |
| `account_name_name` | `varchar` | ✓ |
| `account_name_id` | `varchar` | ✓ |
| `deal_name__s_name` | `varchar` | ✓ |
| `deal_name__s_id` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `leads`

**Colunas**: 144

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `gclid` | `varchar` | ✓ |
| `lead_score` | `varchar` | ✓ |
| `linkedin_url_lead_crm` | `varchar` | ✓ |
| `$field_states` | `varchar` | ✓ |
| `was_a_meeting_necessary` | `varchar` | ✓ |
| `department` | `varchar` | ✓ |
| `$state` | `varchar` | ✓ |
| `origem_lead` | `varchar` | ✓ |
| `$process_flow` | `varchar` | ✓ |
| `ad_network` | `varchar` | ✓ |
| `street` | `varchar` | ✓ |
| `id` | `varchar` | ✓ |
| `cost_per_click` | `varchar` | ✓ |
| `first_visited_url` | `varchar` | ✓ |
| `existing_customer` | `varchar` | ✓ |
| `created_time` | `varchar` | ✓ |
| `linkedin` | `varchar` | ✓ |
| `ad_click_date` | `varchar` | ✓ |
| `lead_source_lead_crm` | `varchar` | ✓ |
| `country` | `varchar` | ✓ |
| `last_visited_time` | `varchar` | ✓ |
| `initial_quantity_of_active_equipment` | `varchar` | ✓ |
| `last_interaction` | `varchar` | ✓ |
| `utm_medium` | `varchar` | ✓ |
| `description` | `varchar` | ✓ |
| `ad` | `varchar` | ✓ |
| `number_of_chats` | `varchar` | ✓ |
| `indication` | `varchar` | ✓ |
| `search_partner_network` | `varchar` | ✓ |
| `website` | `varchar` | ✓ |
| `average_time_spent_minutes` | `varchar` | ✓ |
| `salutation` | `varchar` | ✓ |
| `lead_status` | `varchar` | ✓ |
| `full_name` | `varchar` | ✓ |
| `record_image` | `varchar` | ✓ |
| `business_number` | `varchar` | ✓ |
| `fixed_or_mobile` | `varchar` | ✓ |
| `decision_level` | `varchar` | ✓ |
| `leadchain0__social_lead_id` | `varchar` | ✓ |
| `email_opt_out` | `varchar` | ✓ |
| `keyword` | `varchar` | ✓ |
| `job_title` | `varchar` | ✓ |
| `mobile` | `varchar` | ✓ |
| `id_conta` | `varchar` | ✓ |
| `$orchestration` | `varchar` | ✓ |
| `ad_campaign_name` | `varchar` | ✓ |
| `conta_existente` | `varchar` | ✓ |
| `locked__s` | `varchar` | ✓ |
| `lead_source` | `varchar` | ✓ |
| `tag` | `varchar` | ✓ |
| `difficulty_encountered_in_the_company` | `varchar` | ✓ |
| `reason_for_conversion_failure` | `varchar` | ✓ |
| `company` | `varchar` | ✓ |
| `deal_owner` | `varchar` | ✓ |
| `email` | `varchar` | ✓ |
| `$currency_symbol` | `varchar` | ✓ |
| `best_time_to_contacts` | `varchar` | ✓ |
| `visitor_score` | `varchar` | ✓ |
| `account_type` | `varchar` | ✓ |
| `utm_term` | `varchar` | ✓ |
| `last_activity_time` | `varchar` | ✓ |
| `unsubscribed_mode` | `varchar` | ✓ |
| `$converted` | `varchar` | ✓ |
| `deal_currency` | `varchar` | ✓ |
| `last_message_sent_on_leadcrm` | `varchar` | ✓ |
| `$locked_for_me` | `varchar` | ✓ |
| `zip_code` | `varchar` | ✓ |
| `$approved` | `varchar` | ✓ |
| `conversion_exported_on` | `varchar` | ✓ |
| `invite_accepted_on_leadcrm` | `varchar` | ✓ |
| `last_response_received_on_leadcrm` | `varchar` | ✓ |
| `rapport` | `varchar` | ✓ |
| `days_visited` | `varchar` | ✓ |
| `click_type` | `varchar` | ✓ |
| `$editable` | `varchar` | ✓ |
| `city` | `varchar` | ✓ |
| `adgroup_name` | `varchar` | ✓ |
| `neighborhood` | `varchar` | ✓ |
| `state_registration_number` | `varchar` | ✓ |
| `utm_content` | `varchar` | ✓ |
| `state` | `varchar` | ✓ |
| `already_does_analysis` | `varchar` | ✓ |
| `$zia_owner_assignment` | `varchar` | ✓ |
| `additional_address_details` | `varchar` | ✓ |
| `reason_for_loss` | `varchar` | ✓ |
| `utm_campaign` | `varchar` | ✓ |
| `use_maintenance_software` | `varchar` | ✓ |
| `segment` | `varchar` | ✓ |
| `first_name` | `varchar` | ✓ |
| `conversion_export_status` | `varchar` | ✓ |
| `cost_per_conversion` | `varchar` | ✓ |
| `$review` | `varchar` | ✓ |
| `als_business_unit` | `varchar` | ✓ |
| `number` | `varchar` | ✓ |
| `phone` | `varchar` | ✓ |
| `topic` | `varchar` | ✓ |
| `maintenance_software` | `varchar` | ✓ |
| `modified_time` | `varchar` | ✓ |
| `sector` | `varchar` | ✓ |
| `unsubscribed_time` | `varchar` | ✓ |
| `google_ads_campaign_id` | `varchar` | ✓ |
| `device_type` | `varchar` | ✓ |
| `account_rating` | `varchar` | ✓ |
| `first_visited_time` | `varchar` | ✓ |
| `last_name` | `varchar` | ✓ |
| `$in_merge` | `varchar` | ✓ |
| `referrer` | `varchar` | ✓ |
| `job_title_category` | `varchar` | ✓ |
| `utm_source` | `varchar` | ✓ |
| `$approval_state` | `varchar` | ✓ |
| `owner_name` | `varchar` | ✓ |
| `owner_id` | `varchar` | ✓ |
| `owner_email` | `varchar` | ✓ |
| `source_campaing_name` | `varchar` | ✓ |
| `source_campaing_id` | `varchar` | ✓ |
| `$approval_delegate` | `varchar` | ✓ |
| `$approval_add_approver` | `varchar` | ✓ |
| `$approval_takeover` | `varchar` | ✓ |
| `$approval_approve` | `varchar` | ✓ |
| `$approval_reject` | `varchar` | ✓ |
| `$approval_resubmit` | `varchar` | ✓ |
| `created_by_name` | `varchar` | ✓ |
| `created_by_id` | `varchar` | ✓ |
| `created_by_email` | `varchar` | ✓ |
| `$review_process_approve` | `varchar` | ✓ |
| `$review_process_reject` | `varchar` | ✓ |
| `$review_process_resubmit` | `varchar` | ✓ |
| `layout_display_label` | `varchar` | ✓ |
| `layout_name` | `varchar` | ✓ |
| `layout_id` | `varchar` | ✓ |
| `$layout_id_display_label` | `varchar` | ✓ |
| `$layout_id_name` | `varchar` | ✓ |
| `$layout_id_id` | `varchar` | ✓ |
| `modified_by_name` | `varchar` | ✓ |
| `modified_by_id` | `varchar` | ✓ |
| `modified_by_email` | `varchar` | ✓ |
| `deal_owner_name` | `varchar` | ✓ |
| `deal_owner_id` | `varchar` | ✓ |
| `existing_customer_name` | `varchar` | ✓ |
| `existing_customer_id` | `varchar` | ✓ |
| `indication_name` | `varchar` | ✓ |
| `indication_id` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `notes`

**Colunas**: 26

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `modified_time` | `varchar` | ✓ |
| `$attachments` | `varchar` | ✓ |
| `$field_states` | `varchar` | ✓ |
| `created_time` | `varchar` | ✓ |
| `$editable` | `varchar` | ✓ |
| `$se_module` | `varchar` | ✓ |
| `$is_shared_to_client` | `varchar` | ✓ |
| `$size` | `varchar` | ✓ |
| `$state` | `varchar` | ✓ |
| `$voice_note` | `varchar` | ✓ |
| `id` | `varchar` | ✓ |
| `note_title` | `varchar` | ✓ |
| `note_content` | `varchar` | ✓ |
| `owner_name` | `varchar` | ✓ |
| `owner_id` | `varchar` | ✓ |
| `owner_email` | `varchar` | ✓ |
| `parent_id_name` | `varchar` | ✓ |
| `parent_id_id` | `varchar` | ✓ |
| `modified_by_name` | `varchar` | ✓ |
| `modified_by_id` | `varchar` | ✓ |
| `modified_by_email` | `varchar` | ✓ |
| `created_by_name` | `varchar` | ✓ |
| `created_by_id` | `varchar` | ✓ |
| `created_by_email` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `price_books`

**Colunas**: 53

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `pricing_details` | `varchar` | ✓ |
| `description` | `varchar` | ✓ |
| `$currency_symbol` | `varchar` | ✓ |
| `$field_states` | `varchar` | ✓ |
| `id_protheus` | `varchar` | ✓ |
| `last_activity_time` | `varchar` | ✓ |
| `zohocrmforprotheus__type_totvs` | `varchar` | ✓ |
| `zohocrmforprotheus__totvs_validity_start_date` | `varchar` | ✓ |
| `$review` | `varchar` | ✓ |
| `$state` | `varchar` | ✓ |
| `$process_flow` | `varchar` | ✓ |
| `zohocrmforprotheus__sync_status` | `varchar` | ✓ |
| `price_book_name` | `varchar` | ✓ |
| `$locked_for_me` | `varchar` | ✓ |
| `id` | `varchar` | ✓ |
| `$approved` | `varchar` | ✓ |
| `modified_time` | `varchar` | ✓ |
| `zohocrmforprotheus__totvs_validity_end_date` | `varchar` | ✓ |
| `created_time` | `varchar` | ✓ |
| `$editable` | `varchar` | ✓ |
| `zohocrmforprotheus__totvs_validity_start_hour` | `varchar` | ✓ |
| `$orchestration` | `varchar` | ✓ |
| `zohocrmforprotheus__payment_term` | `varchar` | ✓ |
| `active` | `varchar` | ✓ |
| `pricing_model` | `varchar` | ✓ |
| `zohocrmforprotheus__totvs_validity_end_hour` | `varchar` | ✓ |
| `$in_merge` | `varchar` | ✓ |
| `locked__s` | `varchar` | ✓ |
| `tag` | `varchar` | ✓ |
| `$approval_state` | `varchar` | ✓ |
| `owner_name` | `varchar` | ✓ |
| `owner_id` | `varchar` | ✓ |
| `owner_email` | `varchar` | ✓ |
| `$review_process_approve` | `varchar` | ✓ |
| `$review_process_reject` | `varchar` | ✓ |
| `$review_process_resubmit` | `varchar` | ✓ |
| `$layout_id_display_label` | `varchar` | ✓ |
| `$layout_id_name` | `varchar` | ✓ |
| `$layout_id_id` | `varchar` | ✓ |
| `modified_by_name` | `varchar` | ✓ |
| `modified_by_id` | `varchar` | ✓ |
| `modified_by_email` | `varchar` | ✓ |
| `$approval_delegate` | `varchar` | ✓ |
| `$approval_add_approver` | `varchar` | ✓ |
| `$approval_takeover` | `varchar` | ✓ |
| `$approval_approve` | `varchar` | ✓ |
| `$approval_reject` | `varchar` | ✓ |
| `$approval_resubmit` | `varchar` | ✓ |
| `created_by_name` | `varchar` | ✓ |
| `created_by_id` | `varchar` | ✓ |
| `created_by_email` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `products`

**Colunas**: 79

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `decimals_supported` | `varchar` | ✓ |
| `$currency_symbol` | `varchar` | ✓ |
| `$field_states` | `varchar` | ✓ |
| `tat` | `varchar` | ✓ |
| `clp` | `varchar` | ✓ |
| `product` | `varchar` | ✓ |
| `pos_ipi_ncm` | `varchar` | ✓ |
| `product_active` | `varchar` | ✓ |
| `last_activity_time` | `varchar` | ✓ |
| `uf` | `varchar` | ✓ |
| `$state` | `varchar` | ✓ |
| `$process_flow` | `varchar` | ✓ |
| `$locked_for_me` | `varchar` | ✓ |
| `id` | `varchar` | ✓ |
| `$approved` | `varchar` | ✓ |
| `status` | `varchar` | ✓ |
| `created_on` | `varchar` | ✓ |
| `eur` | `varchar` | ✓ |
| `created_time` | `varchar` | ✓ |
| `zohocrmforprotheus__integration_result` | `varchar` | ✓ |
| `product_name` | `varchar` | ✓ |
| `$taxable` | `varchar` | ✓ |
| `$editable` | `varchar` | ✓ |
| `mx` | `varchar` | ✓ |
| `product_structure` | `varchar` | ✓ |
| `czk` | `varchar` | ✓ |
| `volume` | `varchar` | ✓ |
| `laborat_rio` | `varchar` | ✓ |
| `prod_oild` | `varchar` | ✓ |
| `description` | `varchar` | ✓ |
| `vendor_name` | `varchar` | ✓ |
| `product_id` | `varchar` | ✓ |
| `modified_on` | `varchar` | ✓ |
| `record_image` | `varchar` | ✓ |
| `$review` | `varchar` | ✓ |
| `product_code` | `varchar` | ✓ |
| `pln` | `varchar` | ✓ |
| `zohocrmforprotheus__sync_status` | `varchar` | ✓ |
| `grupo` | `varchar` | ✓ |
| `volume1` | `varchar` | ✓ |
| `zohocrmforprotheus__default_warehouse` | `varchar` | ✓ |
| `modified_time` | `varchar` | ✓ |
| `usd` | `varchar` | ✓ |
| `prazo` | `varchar` | ✓ |
| `subject` | `varchar` | ✓ |
| `$orchestration` | `varchar` | ✓ |
| `zohocrmforprotheus__tes_saida` | `varchar` | ✓ |
| `$in_merge` | `varchar` | ✓ |
| `als_business_unit2` | `varchar` | ✓ |
| `locked__s` | `varchar` | ✓ |
| `metodologia` | `varchar` | ✓ |
| `tag` | `varchar` | ✓ |
| `$approval_state` | `varchar` | ✓ |
| `valid_to` | `varchar` | ✓ |
| `brl` | `varchar` | ✓ |
| `cod_item` | `varchar` | ✓ |
| `owner_name` | `varchar` | ✓ |
| `owner_id` | `varchar` | ✓ |
| `owner_email` | `varchar` | ✓ |
| `$approval_delegate` | `varchar` | ✓ |
| `$approval_add_approver` | `varchar` | ✓ |
| `$approval_takeover` | `varchar` | ✓ |
| `$approval_approve` | `varchar` | ✓ |
| `$approval_reject` | `varchar` | ✓ |
| `$approval_resubmit` | `varchar` | ✓ |
| `created_by_name` | `varchar` | ✓ |
| `created_by_id` | `varchar` | ✓ |
| `created_by_email` | `varchar` | ✓ |
| `$review_process_approve` | `varchar` | ✓ |
| `$review_process_reject` | `varchar` | ✓ |
| `$review_process_resubmit` | `varchar` | ✓ |
| `$layout_id_display_label` | `varchar` | ✓ |
| `$layout_id_name` | `varchar` | ✓ |
| `$layout_id_id` | `varchar` | ✓ |
| `modified_by_name` | `varchar` | ✓ |
| `modified_by_id` | `varchar` | ✓ |
| `modified_by_email` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `quoted_items1`

**Colunas**: 34

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `linkingmodule1_serial_number` | `varchar` | ✓ |
| `discount` | `varchar` | ✓ |
| `$currency_symbol` | `varchar` | ✓ |
| `$field_states` | `varchar` | ✓ |
| `created_time` | `varchar` | ✓ |
| `amount` | `varchar` | ✓ |
| `$review_process` | `varchar` | ✓ |
| `quantity` | `varchar` | ✓ |
| `$editable` | `varchar` | ✓ |
| `$orchestration` | `varchar` | ✓ |
| `$review` | `varchar` | ✓ |
| `$state` | `varchar` | ✓ |
| `$process_flow` | `varchar` | ✓ |
| `$in_merge` | `varchar` | ✓ |
| `list_price` | `varchar` | ✓ |
| `id` | `varchar` | ✓ |
| `$approval_state` | `varchar` | ✓ |
| `$approved` | `varchar` | ✓ |
| `$approval_delegate` | `varchar` | ✓ |
| `$approval_add_approver` | `varchar` | ✓ |
| `$approval_takeover` | `varchar` | ✓ |
| `$approval_approve` | `varchar` | ✓ |
| `$approval_reject` | `varchar` | ✓ |
| `$approval_resubmit` | `varchar` | ✓ |
| `parent_id_name` | `varchar` | ✓ |
| `parent_id_id` | `varchar` | ✓ |
| `product_name_name` | `varchar` | ✓ |
| `product_name_id` | `varchar` | ✓ |
| `$layout_id_display_label` | `varchar` | ✓ |
| `$layout_id_name` | `varchar` | ✓ |
| `$layout_id_id` | `varchar` | ✓ |
| `product_name` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `quotes`

**Colunas**: 74

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `$currency_symbol` | `varchar` | ✓ |
| `$field_states` | `varchar` | ✓ |
| `template_pdf` | `varchar` | ✓ |
| `reason_for_loss` | `varchar` | ✓ |
| `quote_number_new` | `varchar` | ✓ |
| `last_activity_time` | `varchar` | ✓ |
| `$state` | `varchar` | ✓ |
| `$converted` | `varchar` | ✓ |
| `$process_flow` | `varchar` | ✓ |
| `billing_country` | `varchar` | ✓ |
| `$locked_for_me` | `varchar` | ✓ |
| `id` | `varchar` | ✓ |
| `$approved` | `varchar` | ✓ |
| `freight` | `varchar` | ✓ |
| `billing_street` | `varchar` | ✓ |
| `quote_data_sent` | `varchar` | ✓ |
| `created_time` | `varchar` | ✓ |
| `$editable` | `varchar` | ✓ |
| `billing_code` | `varchar` | ✓ |
| `product_details` | `varchar` | ✓ |
| `neighborhood` | `varchar` | ✓ |
| `billing_city` | `varchar` | ✓ |
| `currency_quote` | `varchar` | ✓ |
| `description` | `varchar` | ✓ |
| `payment_terms` | `varchar` | ✓ |
| `$review` | `varchar` | ✓ |
| `als_business_unit` | `varchar` | ✓ |
| `number` | `varchar` | ✓ |
| `valid_till` | `varchar` | ✓ |
| `issue_date` | `varchar` | ✓ |
| `payment_type` | `varchar` | ✓ |
| `quote_stage` | `varchar` | ✓ |
| `modified_time` | `varchar` | ✓ |
| `main_phone` | `varchar` | ✓ |
| `subject` | `varchar` | ✓ |
| `$orchestration` | `varchar` | ✓ |
| `erp_id` | `varchar` | ✓ |
| `$in_merge` | `varchar` | ✓ |
| `locked__s` | `varchar` | ✓ |
| `billing_state` | `varchar` | ✓ |
| `$line_tax` | `varchar` | ✓ |
| `tag` | `varchar` | ✓ |
| `$approval_state` | `varchar` | ✓ |
| `owner_name` | `varchar` | ✓ |
| `owner_id` | `varchar` | ✓ |
| `owner_email` | `varchar` | ✓ |
| `deal_name_name` | `varchar` | ✓ |
| `deal_name_id` | `varchar` | ✓ |
| `$approval_delegate` | `varchar` | ✓ |
| `$approval_add_approver` | `varchar` | ✓ |
| `$approval_takeover` | `varchar` | ✓ |
| `$approval_approve` | `varchar` | ✓ |
| `$approval_reject` | `varchar` | ✓ |
| `$approval_resubmit` | `varchar` | ✓ |
| `created_by_name` | `varchar` | ✓ |
| `created_by_id` | `varchar` | ✓ |
| `created_by_email` | `varchar` | ✓ |
| `$review_process_approve` | `varchar` | ✓ |
| `$review_process_reject` | `varchar` | ✓ |
| `$review_process_resubmit` | `varchar` | ✓ |
| `$layout_id_display_label` | `varchar` | ✓ |
| `$layout_id_name` | `varchar` | ✓ |
| `$layout_id_id` | `varchar` | ✓ |
| `modified_by_name` | `varchar` | ✓ |
| `modified_by_id` | `varchar` | ✓ |
| `modified_by_email` | `varchar` | ✓ |
| `account_name_name` | `varchar` | ✓ |
| `account_name_id` | `varchar` | ✓ |
| `contact_name_name` | `varchar` | ✓ |
| `contact_name_id` | `varchar` | ✓ |
| `contact_name` | `varchar` | ✓ |
| `deal_name` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `sales_orders`

**Colunas**: 89

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `$currency_symbol` | `varchar` | ✓ |
| `$field_states` | `varchar` | ✓ |
| `customer_no` | `varchar` | ✓ |
| `tax` | `varchar` | ✓ |
| `last_activity_time` | `varchar` | ✓ |
| `zohocrmforprotheus__integration_status` | `varchar` | ✓ |
| `$state` | `varchar` | ✓ |
| `$converted` | `varchar` | ✓ |
| `$process_flow` | `varchar` | ✓ |
| `deal_name` | `varchar` | ✓ |
| `billing_country` | `varchar` | ✓ |
| `$locked_for_me` | `varchar` | ✓ |
| `id` | `varchar` | ✓ |
| `carrier` | `varchar` | ✓ |
| `$approved` | `varchar` | ✓ |
| `quote_name` | `varchar` | ✓ |
| `status` | `varchar` | ✓ |
| `grand_total` | `varchar` | ✓ |
| `adjustment` | `varchar` | ✓ |
| `billing_street` | `varchar` | ✓ |
| `created_time` | `varchar` | ✓ |
| `zohocrmforprotheus__integration_result` | `varchar` | ✓ |
| `$editable` | `varchar` | ✓ |
| `billing_code` | `varchar` | ✓ |
| `product_details` | `varchar` | ✓ |
| `zohocrmforprotheus__block_receivables` | `varchar` | ✓ |
| `excise_duty` | `varchar` | ✓ |
| `shipping_city` | `varchar` | ✓ |
| `shipping_country` | `varchar` | ✓ |
| `shipping_code` | `varchar` | ✓ |
| `billing_city` | `varchar` | ✓ |
| `purchase_order` | `varchar` | ✓ |
| `shipping_street` | `varchar` | ✓ |
| `description` | `varchar` | ✓ |
| `discount` | `varchar` | ✓ |
| `zohocrmforprotheus__num_totvs` | `varchar` | ✓ |
| `zohocrmforprotheus__stock_reserved` | `varchar` | ✓ |
| `shipping_state` | `varchar` | ✓ |
| `zohocrmforprotheus__delivery_customer` | `varchar` | ✓ |
| `zohocrmforprotheus__type_totvs` | `varchar` | ✓ |
| `$review` | `varchar` | ✓ |
| `zohocrmforprotheus__sync_status` | `varchar` | ✓ |
| `sales_commission` | `varchar` | ✓ |
| `modified_time` | `varchar` | ✓ |
| `due_date` | `varchar` | ✓ |
| `terms_and_conditions` | `varchar` | ✓ |
| `sub_total` | `varchar` | ✓ |
| `zohocrmforprotheus__sales_representative` | `varchar` | ✓ |
| `subject` | `varchar` | ✓ |
| `$orchestration` | `varchar` | ✓ |
| `zohocrmforprotheus__payment_term` | `varchar` | ✓ |
| `zohocrmforprotheus__freight_type_totvs` | `varchar` | ✓ |
| `$in_merge` | `varchar` | ✓ |
| `so_number` | `varchar` | ✓ |
| `locked__s` | `varchar` | ✓ |
| `billing_state` | `varchar` | ✓ |
| `$line_tax` | `varchar` | ✓ |
| `tag` | `varchar` | ✓ |
| `$approval_state` | `varchar` | ✓ |
| `zohocrmforprotheus__price_book` | `varchar` | ✓ |
| `pending` | `varchar` | ✓ |
| `owner_name` | `varchar` | ✓ |
| `owner_id` | `varchar` | ✓ |
| `owner_email` | `varchar` | ✓ |
| `$approval_delegate` | `varchar` | ✓ |
| `$approval_add_approver` | `varchar` | ✓ |
| `$approval_takeover` | `varchar` | ✓ |
| `$approval_approve` | `varchar` | ✓ |
| `$approval_reject` | `varchar` | ✓ |
| `$approval_resubmit` | `varchar` | ✓ |
| `created_by_name` | `varchar` | ✓ |
| `created_by_id` | `varchar` | ✓ |
| `created_by_email` | `varchar` | ✓ |
| `$review_process_approve` | `varchar` | ✓ |
| `$review_process_reject` | `varchar` | ✓ |
| `$review_process_resubmit` | `varchar` | ✓ |
| `$layout_id_display_label` | `varchar` | ✓ |
| `$layout_id_name` | `varchar` | ✓ |
| `$layout_id_id` | `varchar` | ✓ |
| `modified_by_name` | `varchar` | ✓ |
| `modified_by_id` | `varchar` | ✓ |
| `modified_by_email` | `varchar` | ✓ |
| `account_name_name` | `varchar` | ✓ |
| `account_name_id` | `varchar` | ✓ |
| `contact_name_name` | `varchar` | ✓ |
| `contact_name_id` | `varchar` | ✓ |
| `contact_name` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `tasks`

**Colunas**: 55

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `description` | `varchar` | ✓ |
| `$currency_symbol` | `varchar` | ✓ |
| `$field_states` | `varchar` | ✓ |
| `closed_time` | `varchar` | ✓ |
| `$review_process` | `varchar` | ✓ |
| `last_activity_time` | `varchar` | ✓ |
| `send_notification_email` | `varchar` | ✓ |
| `$review` | `varchar` | ✓ |
| `$state` | `varchar` | ✓ |
| `$process_flow` | `varchar` | ✓ |
| `$locked_for_me` | `varchar` | ✓ |
| `id` | `varchar` | ✓ |
| `$approved` | `varchar` | ✓ |
| `who_id` | `varchar` | ✓ |
| `status` | `varchar` | ✓ |
| `modified_time` | `varchar` | ✓ |
| `due_date` | `varchar` | ✓ |
| `priority` | `varchar` | ✓ |
| `created_time` | `varchar` | ✓ |
| `$editable` | `varchar` | ✓ |
| `subject` | `varchar` | ✓ |
| `$orchestration` | `varchar` | ✓ |
| `$se_module` | `varchar` | ✓ |
| `recurring_activity` | `varchar` | ✓ |
| `$in_merge` | `varchar` | ✓ |
| `$u_id` | `varchar` | ✓ |
| `locked__s` | `varchar` | ✓ |
| `tag` | `varchar` | ✓ |
| `$zia_owner_assignment` | `varchar` | ✓ |
| `best_time` | `varchar` | ✓ |
| `$approval_state` | `varchar` | ✓ |
| `owner_name` | `varchar` | ✓ |
| `owner_id` | `varchar` | ✓ |
| `owner_email` | `varchar` | ✓ |
| `modified_by_name` | `varchar` | ✓ |
| `modified_by_id` | `varchar` | ✓ |
| `modified_by_email` | `varchar` | ✓ |
| `remind_at_alarm` | `varchar` | ✓ |
| `$approval_delegate` | `varchar` | ✓ |
| `$approval_add_approver` | `varchar` | ✓ |
| `$approval_takeover` | `varchar` | ✓ |
| `$approval_approve` | `varchar` | ✓ |
| `$approval_reject` | `varchar` | ✓ |
| `$approval_resubmit` | `varchar` | ✓ |
| `what_id_name` | `varchar` | ✓ |
| `what_id_id` | `varchar` | ✓ |
| `created_by_name` | `varchar` | ✓ |
| `created_by_id` | `varchar` | ✓ |
| `created_by_email` | `varchar` | ✓ |
| `remind_at` | `varchar` | ✓ |
| `who_id_name` | `varchar` | ✓ |
| `who_id_id` | `varchar` | ✓ |
| `what_id` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `tickets`

**Colunas**: 64

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `origin` | `varchar` | ✓ |
| `status_reason` | `varchar` | ✓ |
| `email` | `varchar` | ✓ |
| `created_on` | `varchar` | ✓ |
| `description` | `varchar` | ✓ |
| `$currency_symbol` | `varchar` | ✓ |
| `create_nonconformance` | `varchar` | ✓ |
| `$field_states` | `varchar` | ✓ |
| `sla` | `varchar` | ✓ |
| `case_type` | `varchar` | ✓ |
| `received_on` | `varchar` | ✓ |
| `name` | `varchar` | ✓ |
| `last_activity_time` | `varchar` | ✓ |
| `record_image` | `varchar` | ✓ |
| `department` | `varchar` | ✓ |
| `$review` | `varchar` | ✓ |
| `$state` | `varchar` | ✓ |
| `unsubscribed_mode` | `varchar` | ✓ |
| `$process_flow` | `varchar` | ✓ |
| `id_desk` | `varchar` | ✓ |
| `resolution_date` | `varchar` | ✓ |
| `$locked_for_me` | `varchar` | ✓ |
| `approver` | `varchar` | ✓ |
| `id` | `varchar` | ✓ |
| `$approved` | `varchar` | ✓ |
| `status` | `varchar` | ✓ |
| `modified_time` | `varchar` | ✓ |
| `created_time` | `varchar` | ✓ |
| `unsubscribed_time` | `varchar` | ✓ |
| `request` | `varchar` | ✓ |
| `$editable` | `varchar` | ✓ |
| `id_departamento` | `varchar` | ✓ |
| `case_reason` | `varchar` | ✓ |
| `$orchestration` | `varchar` | ✓ |
| `$in_merge` | `varchar` | ✓ |
| `locked__s` | `varchar` | ✓ |
| `tag` | `varchar` | ✓ |
| `$zia_owner_assignment` | `varchar` | ✓ |
| `complaint_validation` | `varchar` | ✓ |
| `$approval_state` | `varchar` | ✓ |
| `title_case` | `varchar` | ✓ |
| `owner_name` | `varchar` | ✓ |
| `owner_id` | `varchar` | ✓ |
| `owner_email` | `varchar` | ✓ |
| `$review_process_approve` | `varchar` | ✓ |
| `$review_process_reject` | `varchar` | ✓ |
| `$review_process_resubmit` | `varchar` | ✓ |
| `$layout_id_display_label` | `varchar` | ✓ |
| `$layout_id_name` | `varchar` | ✓ |
| `$layout_id_id` | `varchar` | ✓ |
| `account_name_name` | `varchar` | ✓ |
| `account_name_id` | `varchar` | ✓ |
| `$approval_delegate` | `varchar` | ✓ |
| `$approval_add_approver` | `varchar` | ✓ |
| `$approval_takeover` | `varchar` | ✓ |
| `$approval_approve` | `varchar` | ✓ |
| `$approval_reject` | `varchar` | ✓ |
| `$approval_resubmit` | `varchar` | ✓ |
| `contact_name_name` | `varchar` | ✓ |
| `contact_name_id` | `varchar` | ✓ |
| `account_name` | `varchar` | ✓ |
| `contact_name` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `users`

**Colunas**: 82

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `country` | `varchar` | ✓ |
| `preferred_currency__s` | `varchar` | ✓ |
| `language` | `varchar` | ✓ |
| `microsoft` | `varchar` | ✓ |
| `currency` | `varchar` | ✓ |
| `id` | `varchar` | ✓ |
| `state` | `varchar` | ✓ |
| `fax` | `varchar` | ✓ |
| `country_locale` | `varchar` | ✓ |
| `sandboxdeveloper` | `varchar` | ✓ |
| `reporting_to` | `varchar` | ✓ |
| `zip` | `varchar` | ✓ |
| `created_time` | `varchar` | ✓ |
| `invited_by__s` | `varchar` | ✓ |
| `time_format` | `varchar` | ✓ |
| `offset` | `varchar` | ✓ |
| `zuid` | `varchar` | ✓ |
| `full_name` | `varchar` | ✓ |
| `territories` | `varchar` | ✓ |
| `phone` | `varchar` | ✓ |
| `current_shift__s` | `varchar` | ✓ |
| `dob` | `varchar` | ✓ |
| `status_updated_by__s` | `varchar` | ✓ |
| `status` | `varchar` | ✓ |
| `city` | `varchar` | ✓ |
| `distance_preference__s` | `varchar` | ✓ |
| `confirmed_time__s` | `varchar` | ✓ |
| `locale` | `varchar` | ✓ |
| `shift_effective_from__s` | `varchar` | ✓ |
| `status_updated_time__s` | `varchar` | ✓ |
| `invited_time__s` | `varchar` | ✓ |
| `isonline` | `varchar` | ✓ |
| `street` | `varchar` | ✓ |
| `alias` | `varchar` | ✓ |
| `first_name` | `varchar` | ✓ |
| `email` | `varchar` | ✓ |
| `status_reason__s` | `varchar` | ✓ |
| `website` | `varchar` | ✓ |
| `modified_time` | `varchar` | ✓ |
| `mobile` | `varchar` | ✓ |
| `last_name` | `varchar` | ✓ |
| `time_zone` | `varchar` | ✓ |
| `job_title` | `varchar` | ✓ |
| `confirm` | `varchar` | ✓ |
| `next_shift__s` | `varchar` | ✓ |
| `date_format` | `varchar` | ✓ |
| `profile_name` | `varchar` | ✓ |
| `profile_id` | `varchar` | ✓ |
| `created_by_name` | `varchar` | ✓ |
| `created_by_id` | `varchar` | ✓ |
| `role_name` | `varchar` | ✓ |
| `role_id` | `varchar` | ✓ |
| `modified_by_name` | `varchar` | ✓ |
| `modified_by_id` | `varchar` | ✓ |
| `status_updated_by__s_name` | `varchar` | ✓ |
| `status_updated_by__s_id` | `varchar` | ✓ |
| `invited_by__s_name` | `varchar` | ✓ |
| `invited_by__s_id` | `varchar` | ✓ |
| `preferred_currency__s_name` | `varchar` | ✓ |
| `preferred_currency__s_id` | `varchar` | ✓ |
| `decimal_separator` | `varchar` | ✓ |
| `signature` | `varchar` | ✓ |
| `name_format` | `varchar` | ✓ |
| `personal_account` | `varchar` | ✓ |
| `default_tab_group` | `varchar` | ✓ |
| `customize_info_notes_desc` | `varchar` | ✓ |
| `customize_info_show_right_panel` | `varchar` | ✓ |
| `customize_info_bc_view` | `varchar` | ✓ |
| `customize_info_show_home` | `varchar` | ✓ |
| `customize_info_show_detail_view` | `varchar` | ✓ |
| `customize_info_show_left_panel` | `varchar` | ✓ |
| `customize_info_unpin_recent_item` | `varchar` | ✓ |
| `theme_normal_tab_font_color` | `varchar` | ✓ |
| `theme_normal_tab_background` | `varchar` | ✓ |
| `theme_selected_tab_font_color` | `varchar` | ✓ |
| `theme_selected_tab_background` | `varchar` | ✓ |
| `theme_new_background` | `varchar` | ✓ |
| `theme_background` | `varchar` | ✓ |
| `theme_screen` | `varchar` | ✓ |
| `theme_type` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

### Schema: `silver_protheus`

#### Tabela: `contabil`

**Colunas**: 15

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `data` | `date` | ✓ |
| `lote` | `varchar` | ✓ |
| `sublote` | `varchar` | ✓ |
| `debito` | `varchar` | ✓ |
| `credito` | `varchar` | ✓ |
| `linha` | `varchar` | ✓ |
| `valor` | `decimal` | ✓ |
| `historico` | `varchar` | ✓ |
| `cc_debito` | `varchar` | ✓ |
| `cc_credito` | `varchar` | ✓ |
| `item_debito` | `varchar` | ✓ |
| `item_credito` | `varchar` | ✓ |
| `filial` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `contaspagar`

**Colunas**: 31

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `nota_eletronica` | `varchar` | ✓ |
| `prefixo` | `varchar` | ✓ |
| `parcela` | `varchar` | ✓ |
| `tipo` | `varchar` | ✓ |
| `fornecedor` | `varchar` | ✓ |
| `loja` | `varchar` | ✓ |
| `nome_fornecedor` | `varchar` | ✓ |
| `emissao` | `date` | ✓ |
| `numero` | `varchar` | ✓ |
| `vencimento` | `date` | ✓ |
| `vencimento_real` | `date` | ✓ |
| `valor` | `decimal` | ✓ |
| `filial` | `varchar` | ✓ |
| `iss` | `decimal` | ✓ |
| `irrf` | `decimal` | ✓ |
| `baixa` | `date` | ✓ |
| `historico` | `varchar` | ✓ |
| `contabilizado` | `varchar` | ✓ |
| `saldo` | `decimal` | ✓ |
| `desconto` | `decimal` | ✓ |
| `multa` | `decimal` | ✓ |
| `juros` | `decimal` | ✓ |
| `moeda` | `varchar` | ✓ |
| `inss` | `decimal` | ✓ |
| `cofins` | `decimal` | ✓ |
| `pis` | `decimal` | ✓ |
| `csll` | `decimal` | ✓ |
| `data_digitacao` | `date` | ✓ |
| `origem` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `contasreceber`

**Colunas**: 35

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `nota_eletronica` | `varchar` | ✓ |
| `prefixo` | `varchar` | ✓ |
| `parcela` | `varchar` | ✓ |
| `tipo` | `varchar` | ✓ |
| `cliente` | `varchar` | ✓ |
| `loja` | `varchar` | ✓ |
| `nome_cliente` | `varchar` | ✓ |
| `emissao` | `date` | ✓ |
| `numero` | `varchar` | ✓ |
| `vencimento` | `date` | ✓ |
| `vencimento_real` | `date` | ✓ |
| `valor` | `decimal` | ✓ |
| `filial` | `varchar` | ✓ |
| `iss` | `decimal` | ✓ |
| `irrf` | `decimal` | ✓ |
| `baixa` | `date` | ✓ |
| `historico` | `varchar` | ✓ |
| `contabilizado` | `varchar` | ✓ |
| `saldo` | `decimal` | ✓ |
| `desconto` | `decimal` | ✓ |
| `multa` | `decimal` | ✓ |
| `juros` | `decimal` | ✓ |
| `moeda` | `varchar` | ✓ |
| `inss` | `decimal` | ✓ |
| `cofins` | `decimal` | ✓ |
| `pis` | `decimal` | ✓ |
| `csll` | `decimal` | ✓ |
| `orcamento` | `varchar` | ✓ |
| `nome_vendedor` | `varchar` | ✓ |
| `forma_pagamento` | `varchar` | ✓ |
| `write_off` | `varchar` | ✓ |
| `cancelamento_adm` | `varchar` | ✓ |
| `origem` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `depara_intercompany`

**Colunas**: 5

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `conta` | `varchar` | ✓ |
| `empresa` | `varchar` | ✓ |
| `lado` | `varchar` | ✓ |
| `plano` | `varchar` | ✓ |
| `obs` | `varchar` | ✓ |

#### Tabela: `depreciacao`

**Colunas**: 15

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `codigo_base` | `varchar` | ✓ |
| `ocorrencia` | `varchar` | ✓ |
| `conta` | `varchar` | ✓ |
| `data` | `date` | ✓ |
| `valor` | `decimal` | ✓ |
| `item` | `varchar` | ✓ |
| `tipo` | `varchar` | ✓ |
| `serie` | `varchar` | ✓ |
| `nota` | `varchar` | ✓ |
| `centro_custo` | `varchar` | ✓ |
| `taxa_depreciacao` | `decimal` | ✓ |
| `contabilizado` | `varchar` | ✓ |
| `filial` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `ferias`

**Colunas**: 6

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `periodo` | `varchar` | ✓ |
| `descricao` | `varchar` | ✓ |
| `valor` | `decimal` | ✓ |
| `filial` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `folhaantiga`

**Colunas**: 10

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `periodo` | `varchar` | ✓ |
| `codigo_verba` | `varchar` | ✓ |
| `descricao` | `varchar` | ✓ |
| `valor` | `decimal` | ✓ |
| `filial` | `varchar` | ✓ |
| `roteiro` | `varchar` | ✓ |
| `centro_custo` | `varchar` | ✓ |
| `departamento` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `folhaatual`

**Colunas**: 7

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `periodo` | `varchar` | ✓ |
| `descricao` | `varchar` | ✓ |
| `valor` | `decimal` | ✓ |
| `filial` | `varchar` | ✓ |
| `roteiro` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `movbancario`

**Colunas**: 24

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `filial` | `varchar` | ✓ |
| `data` | `date` | ✓ |
| `tipo` | `varchar` | ✓ |
| `moeda` | `varchar` | ✓ |
| `valor` | `decimal` | ✓ |
| `banco` | `varchar` | ✓ |
| `agencia` | `varchar` | ✓ |
| `conta` | `varchar` | ✓ |
| `recpag` | `varchar` | ✓ |
| `beneficiario` | `varchar` | ✓ |
| `historico` | `varchar` | ✓ |
| `contabilizado` | `varchar` | ✓ |
| `prefixo` | `varchar` | ✓ |
| `numero` | `varchar` | ✓ |
| `parcela` | `varchar` | ✓ |
| `data_digitacao` | `date` | ✓ |
| `mot_baixa` | `varchar` | ✓ |
| `data_disponibilizacao` | `date` | ✓ |
| `juros` | `decimal` | ✓ |
| `multa` | `decimal` | ✓ |
| `desconto` | `decimal` | ✓ |
| `taxa_moeda` | `decimal` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `notasentrada`

**Colunas**: 38

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `item` | `varchar` | ✓ |
| `cod_produto` | `varchar` | ✓ |
| `desc_produto` | `varchar` | ✓ |
| `unid_medida` | `varchar` | ✓ |
| `quantidade` | `decimal` | ✓ |
| `preco` | `decimal` | ✓ |
| `total` | `decimal` | ✓ |
| `num_pedido` | `varchar` | ✓ |
| `numero` | `varchar` | ✓ |
| `ipi` | `decimal` | ✓ |
| `item_pedido` | `varchar` | ✓ |
| `armazem` | `varchar` | ✓ |
| `filial` | `varchar` | ✓ |
| `icms` | `decimal` | ✓ |
| `cod_fornecedor` | `varchar` | ✓ |
| `loja_fornecedor` | `varchar` | ✓ |
| `centro_custo` | `varchar` | ✓ |
| `conta_contabil` | `varchar` | ✓ |
| `cfop` | `varchar` | ✓ |
| `emissao` | `date` | ✓ |
| `porc_icms` | `decimal` | ✓ |
| `data_digitacao` | `date` | ✓ |
| `serie` | `varchar` | ✓ |
| `tipo` | `varchar` | ✓ |
| `nota_origem` | `varchar` | ✓ |
| `serie_origem` | `varchar` | ✓ |
| `item_origem` | `varchar` | ✓ |
| `desconto` | `decimal` | ✓ |
| `icms_retido` | `decimal` | ✓ |
| `cofins` | `decimal` | ✓ |
| `pis` | `decimal` | ✓ |
| `iss` | `decimal` | ✓ |
| `ir` | `decimal` | ✓ |
| `seguro` | `decimal` | ✓ |
| `despesas` | `decimal` | ✓ |
| `inss` | `decimal` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `notassaida`

**Colunas**: 36

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `item` | `varchar` | ✓ |
| `cod_produto` | `varchar` | ✓ |
| `unid_medida` | `varchar` | ✓ |
| `quantidade` | `decimal` | ✓ |
| `preco` | `decimal` | ✓ |
| `total` | `decimal` | ✓ |
| `num_pedido` | `varchar` | ✓ |
| `numero` | `varchar` | ✓ |
| `ipi` | `decimal` | ✓ |
| `item_pedido` | `varchar` | ✓ |
| `armazem` | `varchar` | ✓ |
| `filial` | `varchar` | ✓ |
| `icms` | `decimal` | ✓ |
| `cod_cliente` | `varchar` | ✓ |
| `loja` | `varchar` | ✓ |
| `conta_contabil` | `varchar` | ✓ |
| `cfop` | `varchar` | ✓ |
| `emissao` | `date` | ✓ |
| `porc_icms` | `decimal` | ✓ |
| `data_digitacao` | `varchar` | ✓ |
| `serie` | `varchar` | ✓ |
| `nota_origem` | `varchar` | ✓ |
| `serie_origem` | `varchar` | ✓ |
| `item_origem` | `varchar` | ✓ |
| `desconto` | `decimal` | ✓ |
| `icms_retido` | `decimal` | ✓ |
| `cofins` | `decimal` | ✓ |
| `pis` | `decimal` | ✓ |
| `iss` | `decimal` | ✓ |
| `ir` | `decimal` | ✓ |
| `seguro` | `decimal` | ✓ |
| `despesas` | `decimal` | ✓ |
| `inss` | `decimal` | ✓ |
| `frete` | `decimal` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `pedcompras`

**Colunas**: 25

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `item` | `varchar` | ✓ |
| `cod_produto` | `varchar` | ✓ |
| `desc_produto` | `varchar` | ✓ |
| `unid_medida` | `varchar` | ✓ |
| `quantidade` | `decimal` | ✓ |
| `preco` | `decimal` | ✓ |
| `total` | `decimal` | ✓ |
| `num_solicitacao` | `varchar` | ✓ |
| `numero` | `varchar` | ✓ |
| `data_entrega` | `date` | ✓ |
| `item_solicitacao` | `varchar` | ✓ |
| `armazem` | `varchar` | ✓ |
| `filial` | `varchar` | ✓ |
| `observacao` | `varchar` | ✓ |
| `cod_fornecedor` | `varchar` | ✓ |
| `loja_fornecedor` | `varchar` | ✓ |
| `centro_custo` | `varchar` | ✓ |
| `conta_contabil` | `varchar` | ✓ |
| `cond_pagto` | `varchar` | ✓ |
| `emissao` | `date` | ✓ |
| `aprovacao` | `varchar` | ✓ |
| `especificacao` | `varchar` | ✓ |
| `quant_entregue` | `decimal` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `pedvendas`

**Colunas**: 23

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `item` | `varchar` | ✓ |
| `cod_produto` | `varchar` | ✓ |
| `desc_produto` | `varchar` | ✓ |
| `unid_medida` | `varchar` | ✓ |
| `quantidade` | `decimal` | ✓ |
| `preco` | `decimal` | ✓ |
| `total` | `decimal` | ✓ |
| `numero` | `varchar` | ✓ |
| `data_entrega` | `date` | ✓ |
| `armazem` | `varchar` | ✓ |
| `filial` | `varchar` | ✓ |
| `cod_fornecedor` | `varchar` | ✓ |
| `loja_fornecedor` | `varchar` | ✓ |
| `centro_custo` | `varchar` | ✓ |
| `conta_contabil` | `varchar` | ✓ |
| `pedido_compra` | `varchar` | ✓ |
| `item_pedido_compra` | `varchar` | ✓ |
| `perc_desconto` | `decimal` | ✓ |
| `valor_desconto` | `decimal` | ✓ |
| `nota_fiscal` | `varchar` | ✓ |
| `serie` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `provisao`

**Colunas**: 7

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `periodo` | `date` | ✓ |
| `descricao` | `varchar` | ✓ |
| `valor` | `decimal` | ✓ |
| `filial` | `varchar` | ✓ |
| `tipo` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `reajuste`

**Colunas**: 8

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `filial` | `varchar` | ✓ |
| `descricao` | `varchar` | ✓ |
| `data` | `date` | ✓ |
| `tipo` | `varchar` | ✓ |
| `valor` | `decimal` | ✓ |
| `valor_anterior` | `decimal` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `rescisao`

**Colunas**: 6

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `periodo` | `varchar` | ✓ |
| `descricao` | `varchar` | ✓ |
| `valor` | `decimal` | ✓ |
| `filial` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

#### Tabela: `solcompras`

**Colunas**: 25

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `item` | `varchar` | ✓ |
| `cod_produto` | `varchar` | ✓ |
| `desc_produto` | `varchar` | ✓ |
| `unid_medida` | `varchar` | ✓ |
| `quantidade` | `decimal` | ✓ |
| `num_pedido` | `varchar` | ✓ |
| `numero` | `varchar` | ✓ |
| `data_entrega` | `date` | ✓ |
| `item_pedido` | `varchar` | ✓ |
| `armazem` | `varchar` | ✓ |
| `filial` | `varchar` | ✓ |
| `observacao` | `varchar` | ✓ |
| `cod_fornecedor` | `varchar` | ✓ |
| `loja_fornecedor` | `varchar` | ✓ |
| `centro_custo` | `varchar` | ✓ |
| `conta_contabil` | `varchar` | ✓ |
| `emissao` | `date` | ✓ |
| `especificacao` | `varchar` | ✓ |
| `solicitante` | `varchar` | ✓ |
| `tipo_solicitacao` | `varchar` | ✓ |
| `comprador` | `varchar` | ✓ |
| `quant_entregue` | `decimal` | ✓ |
| `aprovacao` | `varchar` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `fonte_api` | `varchar` | ✓ |

### Schema: `silver_s360`

#### Tabela: `bridge_amostra_plano`

**Colunas**: 2

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `amostra_id` | `bigint` | ✓ |
| `plano_analise_id` | `bigint` | ✓ |

#### Tabela: `dim_calendario`

**Colunas**: 9

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `data` | `date` | ✓ |
| `ano` | `int` | ✓ |
| `mes` | `int` | ✓ |
| `dia` | `int` | ✓ |
| `competencia` | `varchar` | ✓ |
| `primeiro_dia_mes` | `varchar` | ✓ |
| `dia_semana` | `int` | ✓ |
| `flag_fim_semana` | `int` | ✓ |
| `trimestre` | `int` | ✓ |

#### Tabela: `dim_cliente`

**Colunas**: 3

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `cliente_id` | `bigint` | ✓ |
| `nome_cliente` | `varchar` | ✓ |
| `razao_social` | `varchar` | ✓ |

#### Tabela: `dim_grupo_trabalho`

**Colunas**: 3

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `grupo_trabalho_id` | `bigint` | ✓ |
| `nome_grupo_ptbr` | `varchar` | ✓ |
| `status_ativo` | `int` | ✓ |

#### Tabela: `dim_laboratorio`

**Colunas**: 3

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `laboratorio_id` | `bigint` | ✓ |
| `nome_origem` | `varchar` | ✓ |
| `nome_canonico` | `varchar` | ✓ |

#### Tabela: `dim_plano_analise`

**Colunas**: 4

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `plano_analise_id` | `bigint` | ✓ |
| `nome_plano_ptbr` | `varchar` | ✓ |
| `prazo_horas` | `int` | ✓ |
| `status_ativo` | `int` | ✓ |

#### Tabela: `fato_amostra_aberta`

**Colunas**: 17

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `amostra_id` | `bigint` | ✓ |
| `numero_amostra` | `varchar` | ✓ |
| `numero_laboratorio` | `bigint` | ✓ |
| `laboratorio_id` | `bigint` | ✓ |
| `cliente_id` | `bigint` | ✓ |
| `nome_compartimento` | `varchar` | ✓ |
| `data_entrada_laboratorio` | `datetime2` | ✓ |
| `prazo_min_horas` | `int` | ✓ |
| `planos_analise` | `varchar` | ✓ |
| `data_limite` | `datetime2` | ✓ |
| `total_reanalises` | `bigint` | ✓ |
| `total_workgroups` | `bigint` | ✓ |
| `processing_window_hours` | `int` | ✓ |
| `grupos_trabalho` | `varchar` | ✓ |
| `ultimo_grupo_concluido_id` | `bigint` | ✓ |
| `receita_valor` | `decimal` | ✓ |
| `receita_moeda` | `varchar` | ✓ |

#### Tabela: `fato_amostra_concluida`

**Colunas**: 34

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `amostra_id` | `bigint` | ✓ |
| `numero_amostra` | `varchar` | ✓ |
| `numero_laboratorio` | `bigint` | ✓ |
| `laboratorio_id` | `bigint` | ✓ |
| `cliente_id` | `bigint` | ✓ |
| `nome_compartimento` | `varchar` | ✓ |
| `data_entrada_laboratorio` | `datetime2` | ✓ |
| `data_finalizacao` | `datetime2` | ✓ |
| `data_finalizacao_dia` | `date` | ✓ |
| `competencia` | `varchar` | ✓ |
| `tat_horas_prazo_entrega` | `float` | ✓ |
| `tat_horas_corridas` | `decimal` | ✓ |
| `prazo_min_horas` | `int` | ✓ |
| `prazo_max_horas` | `int` | ✓ |
| `qtd_planos` | `bigint` | ✓ |
| `qtd_prazos_distintos` | `int` | ✓ |
| `planos_analise` | `varchar` | ✓ |
| `flag_prazo_cumprido_kpi` | `int` | ✓ |
| `flag_prazo_cumprido_corrido` | `int` | ✓ |
| `flag_tat_lt_24h` | `int` | ✓ |
| `flag_tat_lt_48h` | `int` | ✓ |
| `flag_tat_lt_72h` | `int` | ✓ |
| `agente_coleta` | `bigint` | ✓ |
| `flag_submissao_online` | `int` | ✓ |
| `flag_base_submissao` | `int` | ✓ |
| `qtd_reanalises` | `bigint` | ✓ |
| `teve_reanalise` | `int` | ✓ |
| `qtd_grupos_trabalho` | `int` | ✓ |
| `janela_processamento_horas` | `decimal` | ✓ |
| `grupos_trabalho` | `varchar` | ✓ |
| `ultimo_grupo_importado_id` | `bigint` | ✓ |
| `ultimo_grupo_concluido_id` | `bigint` | ✓ |
| `receita_valor` | `decimal` | ✓ |
| `receita_moeda` | `varchar` | ✓ |

#### Tabela: `fato_bancada`

**Colunas**: 13

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `amostra_id` | `bigint` | ✓ |
| `grupo_trabalho_id` | `bigint` | ✓ |
| `laboratorio_id` | `bigint` | ✓ |
| `status_amostra` | `smallint` | ✓ |
| `data_finalizacao_dia` | `date` | ✓ |
| `competencia` | `varchar` | ✓ |
| `bancada_inicio` | `datetime2` | ✓ |
| `bancada_fim` | `datetime2` | ✓ |
| `qtd_linhas_resultado` | `bigint` | ✓ |
| `qtd_reanalises` | `bigint` | ✓ |
| `horas_bancada` | `decimal` | ✓ |
| `horas_desde_entrada` | `decimal` | ✓ |
| `flag_bancada_atrasada` | `int` | ✓ |

#### Tabela: `fato_grupo_trabalho`

**Colunas**: 12

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `amostra_id` | `bigint` | ✓ |
| `grupo_trabalho_id` | `bigint` | ✓ |
| `laboratorio_id` | `bigint` | ✓ |
| `competencia` | `varchar` | ✓ |
| `data_entrada_laboratorio` | `datetime2` | ✓ |
| `data_finalizacao` | `datetime2` | ✓ |
| `prazo_min_horas` | `int` | ✓ |
| `n_linhas` | `bigint` | ✓ |
| `soma_horas_registro` | `decimal` | ✓ |
| `soma_reanalise` | `bigint` | ✓ |
| `bench_finish` | `datetime2` | ✓ |
| `data_registro_max` | `datetime2` | ✓ |

#### Tabela: `stg_amostra_agregado`

**Colunas**: 13

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `amostra_id` | `bigint` | ✓ |
| `prazo_min_horas` | `int` | ✓ |
| `prazo_max_horas` | `int` | ✓ |
| `qtd_planos` | `bigint` | ✓ |
| `qtd_prazos_distintos` | `int` | ✓ |
| `planos_analise` | `varchar` | ✓ |
| `qtd_reanalises` | `bigint` | ✓ |
| `teve_reanalise` | `int` | ✓ |
| `qtd_grupos_trabalho` | `int` | ✓ |
| `janela_processamento_horas` | `decimal` | ✓ |
| `ultimo_grupo_importado_id` | `bigint` | ✓ |
| `ultimo_grupo_concluido_id` | `bigint` | ✓ |
| `grupos_trabalho` | `varchar` | ✓ |

#### Tabela: `stg_plano_grupo`

**Colunas**: 3

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `plano_analise_id` | `bigint` | ✓ |
| `laboratorio_id` | `bigint` | ✓ |
| `grupos_trabalho` | `varchar` | ✓ |

### Schema: `silver_zoho`

#### Tabela: `accounts`

**Colunas**: 37

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `zoho_id` | `varchar` | ✓ |
| `conta` | `varchar` | ✓ |
| `razao_social` | `varchar` | ✓ |
| `cnpj` | `varchar` | ✓ |
| `inscricao_estadual` | `varchar` | ✓ |
| `erp_id` | `varchar` | ✓ |
| `id_protheus` | `varchar` | ✓ |
| `proprietario` | `varchar` | ✓ |
| `proprietario_id` | `varchar` | ✓ |
| `setor` | `varchar` | ✓ |
| `segmento` | `varchar` | ✓ |
| `cidade` | `varchar` | ✓ |
| `uf` | `varchar` | ✓ |
| `marca` | `varchar` | ✓ |
| `unidade_negocio` | `varchar` | ✓ |
| `classificacao` | `varchar` | ✓ |
| `segmentacao_cliente` | `varchar` | ✓ |
| `portfolio_cliente` | `varchar` | ✓ |
| `tipo_conta` | `varchar` | ✓ |
| `pessoa_juridica` | `varchar` | ✓ |
| `status` | `varchar` | ✓ |
| `status_real` | `varchar` | ✓ |
| `conta_pai` | `varchar` | ✓ |
| `conta_pai_id` | `varchar` | ✓ |
| `contrato_assinado` | `varchar` | ✓ |
| `status_contrato` | `varchar` | ✓ |
| `contrato_inicio` | `date` | ✓ |
| `contrato_fim` | `date` | ✓ |
| `tipo_pagamento` | `varchar` | ✓ |
| `cond_pagamento` | `varchar` | ✓ |
| `tabela_preco` | `varchar` | ✓ |
| `limite_credito` | `bigint` | ✓ |
| `vendas_ttm` | `bigint` | ✓ |
| `data_criacao` | `datetime2` | ✓ |
| `data_modificacao` | `datetime2` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `calls`

**Colunas**: 16

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `zoho_id` | `varchar` | ✓ |
| `inicio_ligacao` | `datetime2` | ✓ |
| `tipo_ligacao` | `varchar` | ✓ |
| `finalidade` | `varchar` | ✓ |
| `resultado` | `varchar` | ✓ |
| `duracao_segundos` | `int` | ✓ |
| `proprietario` | `varchar` | ✓ |
| `proprietario_id` | `varchar` | ✓ |
| `relacionado_pessoa` | `varchar` | ✓ |
| `relacionado_pessoa_id` | `varchar` | ✓ |
| `relacionado_registro` | `varchar` | ✓ |
| `relacionado_registro_id` | `varchar` | ✓ |
| `data_criacao` | `datetime2` | ✓ |
| `data_modificacao` | `datetime2` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `campaigns`

**Colunas**: 16

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `zoho_id` | `varchar` | ✓ |
| `campanha` | `varchar` | ✓ |
| `tipo` | `varchar` | ✓ |
| `status` | `varchar` | ✓ |
| `data_inicio` | `date` | ✓ |
| `data_fim` | `date` | ✓ |
| `custo_orcado` | `decimal` | ✓ |
| `custo_real` | `decimal` | ✓ |
| `receita_esperada` | `decimal` | ✓ |
| `proprietario` | `varchar` | ✓ |
| `proprietario_id` | `varchar` | ✓ |
| `campanha_pai` | `varchar` | ✓ |
| `data_criacao` | `datetime2` | ✓ |
| `data_modificacao` | `datetime2` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `cases`

**Colunas**: 14

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `zoho_id` | `varchar` | ✓ |
| `assunto` | `varchar` | ✓ |
| `conta` | `varchar` | ✓ |
| `conta_id` | `varchar` | ✓ |
| `status` | `varchar` | ✓ |
| `prioridade` | `varchar` | ✓ |
| `canal` | `varchar` | ✓ |
| `tipo` | `varchar` | ✓ |
| `proprietario` | `varchar` | ✓ |
| `proprietario_id` | `varchar` | ✓ |
| `data_abertura` | `datetime2` | ✓ |
| `data_modificacao` | `datetime2` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `contacts`

**Colunas**: 22

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `zoho_id` | `varchar` | ✓ |
| `nome` | `varchar` | ✓ |
| `sobrenome` | `varchar` | ✓ |
| `conta` | `varchar` | ✓ |
| `conta_id` | `varchar` | ✓ |
| `id_conta` | `varchar` | ✓ |
| `email` | `varchar` | ✓ |
| `telefone` | `varchar` | ✓ |
| `celular` | `varchar` | ✓ |
| `cargo` | `varchar` | ✓ |
| `categoria_cargo` | `varchar` | ✓ |
| `nivel_decisao` | `varchar` | ✓ |
| `departamento` | `varchar` | ✓ |
| `unidade_negocio` | `varchar` | ✓ |
| `status` | `varchar` | ✓ |
| `proprietario` | `varchar` | ✓ |
| `proprietario_id` | `varchar` | ✓ |
| `ultima_interacao` | `date` | ✓ |
| `data_criacao` | `datetime2` | ✓ |
| `data_modificacao` | `datetime2` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `deals`

**Colunas**: 28

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `zoho_id` | `varchar` | ✓ |
| `negocio` | `varchar` | ✓ |
| `conta` | `varchar` | ✓ |
| `conta_id` | `varchar` | ✓ |
| `contato` | `varchar` | ✓ |
| `contato_id` | `varchar` | ✓ |
| `campanha` | `varchar` | ✓ |
| `campanha_id` | `varchar` | ✓ |
| `proprietario` | `varchar` | ✓ |
| `proprietario_id` | `varchar` | ✓ |
| `estagio` | `varchar` | ✓ |
| `valor` | `decimal` | ✓ |
| `probabilidade` | `bigint` | ✓ |
| `tipo_oportunidade` | `varchar` | ✓ |
| `status_orcamento` | `varchar` | ✓ |
| `origem_midia` | `varchar` | ✓ |
| `motivo_perda` | `varchar` | ✓ |
| `unidade_negocio` | `varchar` | ✓ |
| `moeda` | `varchar` | ✓ |
| `prazo_meses` | `bigint` | ✓ |
| `data_fechamento_real` | `date` | ✓ |
| `data_fechamento_prevista` | `date` | ✓ |
| `data_envio_orcamento` | `date` | ✓ |
| `em_risco_abandono` | `bit` | ✓ |
| `data_criacao` | `datetime2` | ✓ |
| `data_modificacao` | `datetime2` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `events`

**Colunas**: 15

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `zoho_id` | `varchar` | ✓ |
| `titulo` | `varchar` | ✓ |
| `inicio` | `datetime2` | ✓ |
| `fim` | `datetime2` | ✓ |
| `responsavel` | `varchar` | ✓ |
| `responsavel_id` | `varchar` | ✓ |
| `relacionado_pessoa` | `varchar` | ✓ |
| `relacionado_pessoa_id` | `varchar` | ✓ |
| `relacionado_registro` | `varchar` | ✓ |
| `relacionado_registro_id` | `varchar` | ✓ |
| `status_reuniao` | `varchar` | ✓ |
| `data_criacao` | `datetime2` | ✓ |
| `data_modificacao` | `datetime2` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `invoices`

**Colunas**: 14

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `zoho_id` | `varchar` | ✓ |
| `assunto` | `varchar` | ✓ |
| `conta` | `varchar` | ✓ |
| `conta_id` | `varchar` | ✓ |
| `proprietario` | `varchar` | ✓ |
| `proprietario_id` | `varchar` | ✓ |
| `status` | `varchar` | ✓ |
| `subtotal` | `decimal` | ✓ |
| `total_geral` | `decimal` | ✓ |
| `pais_cobranca` | `varchar` | ✓ |
| `data_criacao` | `datetime2` | ✓ |
| `data_modificacao` | `datetime2` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `leads`

**Colunas**: 30

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `zoho_id` | `varchar` | ✓ |
| `nome` | `varchar` | ✓ |
| `sobrenome` | `varchar` | ✓ |
| `empresa` | `varchar` | ✓ |
| `cnpj` | `varchar` | ✓ |
| `id_conta` | `varchar` | ✓ |
| `email` | `varchar` | ✓ |
| `telefone` | `varchar` | ✓ |
| `celular` | `varchar` | ✓ |
| `origem_campanha` | `varchar` | ✓ |
| `origem_campanha_id` | `varchar` | ✓ |
| `proprietario` | `varchar` | ✓ |
| `proprietario_id` | `varchar` | ✓ |
| `setor` | `varchar` | ✓ |
| `segmento` | `varchar` | ✓ |
| `classificacao` | `varchar` | ✓ |
| `tipo_conta` | `varchar` | ✓ |
| `unidade_negocio` | `varchar` | ✓ |
| `nivel_decisao` | `varchar` | ✓ |
| `cargo` | `varchar` | ✓ |
| `motivo_perda` | `varchar` | ✓ |
| `cliente_existente` | `varchar` | ✓ |
| `cliente_existente_id` | `varchar` | ✓ |
| `cidade` | `varchar` | ✓ |
| `uf` | `varchar` | ✓ |
| `ultima_interacao` | `date` | ✓ |
| `data_criacao` | `datetime2` | ✓ |
| `data_modificacao` | `datetime2` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `notes`

**Colunas**: 9

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `zoho_id` | `varchar` | ✓ |
| `titulo` | `varchar` | ✓ |
| `conteudo` | `varchar` | ✓ |
| `proprietario` | `varchar` | ✓ |
| `proprietario_id` | `varchar` | ✓ |
| `data_criacao` | `datetime2` | ✓ |
| `data_modificacao` | `datetime2` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `products`

**Colunas**: 24

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `zoho_id` | `varchar` | ✓ |
| `produto` | `varchar` | ✓ |
| `codigo_produto` | `varchar` | ✓ |
| `cod_item` | `varchar` | ✓ |
| `ativo` | `bit` | ✓ |
| `status` | `varchar` | ✓ |
| `estrutura` | `varchar` | ✓ |
| `grupo` | `varchar` | ✓ |
| `fornecedor` | `varchar` | ✓ |
| `unidade_negocio` | `varchar` | ✓ |
| `laboratorio` | `varchar` | ✓ |
| `metodologia` | `varchar` | ✓ |
| `tat_horas` | `int` | ✓ |
| `volume_ml` | `int` | ✓ |
| `prazo` | `bigint` | ✓ |
| `preco_brl` | `decimal` | ✓ |
| `preco_usd` | `decimal` | ✓ |
| `preco_eur` | `decimal` | ✓ |
| `proprietario` | `varchar` | ✓ |
| `proprietario_id` | `varchar` | ✓ |
| `data_criacao` | `datetime2` | ✓ |
| `data_modificacao` | `datetime2` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `quoted_items1`

**Colunas**: 13

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `zoho_id` | `varchar` | ✓ |
| `negocio` | `varchar` | ✓ |
| `negocio_id` | `varchar` | ✓ |
| `produto` | `varchar` | ✓ |
| `produto_id` | `varchar` | ✓ |
| `item` | `bigint` | ✓ |
| `quantidade` | `bigint` | ✓ |
| `preco_lista` | `decimal` | ✓ |
| `desconto_pct` | `decimal` | ✓ |
| `valor` | `decimal` | ✓ |
| `data_criacao` | `datetime2` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `quotes`

**Colunas**: 29

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `zoho_id` | `varchar` | ✓ |
| `assunto` | `varchar` | ✓ |
| `numero_orcamento` | `varchar` | ✓ |
| `numero` | `varchar` | ✓ |
| `conta` | `varchar` | ✓ |
| `conta_id` | `varchar` | ✓ |
| `negocio` | `varchar` | ✓ |
| `negocio_id` | `varchar` | ✓ |
| `contato` | `varchar` | ✓ |
| `contato_id` | `varchar` | ✓ |
| `proprietario` | `varchar` | ✓ |
| `proprietario_id` | `varchar` | ✓ |
| `estagio` | `varchar` | ✓ |
| `erp_id` | `varchar` | ✓ |
| `moeda` | `varchar` | ✓ |
| `unidade_negocio` | `varchar` | ✓ |
| `cond_pagamento` | `varchar` | ✓ |
| `tipo_pagamento` | `varchar` | ✓ |
| `frete` | `varchar` | ✓ |
| `motivo_perda` | `varchar` | ✓ |
| `data_emissao` | `date` | ✓ |
| `valido_ate` | `date` | ✓ |
| `data_envio` | `date` | ✓ |
| `cidade` | `varchar` | ✓ |
| `uf` | `varchar` | ✓ |
| `data_criacao` | `datetime2` | ✓ |
| `data_modificacao` | `datetime2` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `sales_orders`

**Colunas**: 14

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `zoho_id` | `varchar` | ✓ |
| `assunto` | `varchar` | ✓ |
| `conta` | `varchar` | ✓ |
| `conta_id` | `varchar` | ✓ |
| `negocio` | `varchar` | ✓ |
| `proprietario` | `varchar` | ✓ |
| `proprietario_id` | `varchar` | ✓ |
| `status` | `varchar` | ✓ |
| `subtotal` | `decimal` | ✓ |
| `total_geral` | `decimal` | ✓ |
| `data_criacao` | `datetime2` | ✓ |
| `data_modificacao` | `datetime2` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `tasks`

**Colunas**: 16

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `zoho_id` | `varchar` | ✓ |
| `assunto` | `varchar` | ✓ |
| `data_vencimento` | `date` | ✓ |
| `data_conclusao` | `datetime2` | ✓ |
| `proprietario` | `varchar` | ✓ |
| `proprietario_id` | `varchar` | ✓ |
| `relacionado_pessoa` | `varchar` | ✓ |
| `relacionado_pessoa_id` | `varchar` | ✓ |
| `relacionado_registro` | `varchar` | ✓ |
| `relacionado_registro_id` | `varchar` | ✓ |
| `status` | `varchar` | ✓ |
| `prioridade` | `varchar` | ✓ |
| `data_criacao` | `datetime2` | ✓ |
| `data_modificacao` | `datetime2` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

#### Tabela: `tickets`

**Colunas**: 24

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `zoho_id` | `varchar` | ✓ |
| `id_ticket` | `varchar` | ✓ |
| `titulo` | `varchar` | ✓ |
| `conta` | `varchar` | ✓ |
| `conta_id` | `varchar` | ✓ |
| `contato` | `varchar` | ✓ |
| `contato_id` | `varchar` | ✓ |
| `status` | `varchar` | ✓ |
| `status_motivo` | `varchar` | ✓ |
| `canal` | `varchar` | ✓ |
| `tipo_caso` | `varchar` | ✓ |
| `motivo_caso` | `varchar` | ✓ |
| `departamento` | `varchar` | ✓ |
| `sla` | `varchar` | ✓ |
| `proprietario` | `varchar` | ✓ |
| `proprietario_id` | `varchar` | ✓ |
| `email` | `varchar` | ✓ |
| `data_recebimento` | `date` | ✓ |
| `data_abertura` | `date` | ✓ |
| `data_resolucao` | `date` | ✓ |
| `data_criacao` | `datetime2` | ✓ |
| `data_modificacao` | `datetime2` | ✓ |
| `data_ingestao` | `datetime2` | ✓ |
| `origem` | `varchar` | ✓ |

## Ontology_OeL

## s360

### Schema: `_public`

#### Tabela: `amostra`

**Colunas**: 64

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `comentario` | `varchar` | ✓ |
| `data_coleta` | `datetime2` | ✓ |
| `data_criacao` | `datetime2` | ✓ |
| `data_entrada_laboratorio` | `datetime2` | ✓ |
| `data_impressao` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `horas_oleo` | `int` | ✓ |
| `horimetro_equipado` | `int` | ✓ |
| `numero_amostra` | `varchar` | ✓ |
| `oleo_trocado` | `int` | ✓ |
| `versao` | `int` | ✓ |
| `volume_adicionado` | `real` | ✓ |
| `cliente_id` | `bigint` | ✓ |
| `produto_caixa_id` | `bigint` | ✓ |
| `programa_id` | `bigint` | ✓ |
| `tipo_amostra` | `bigint` | ✓ |
| `excluido` | `bit` | ✓ |
| `status_amostra` | `smallint` | ✓ |
| `compartimento_id` | `bigint` | ✓ |
| `controle_importacao_id` | `bigint` | ✓ |
| `fabricante_oleo_id` | `bigint` | ✓ |
| `viscosidade_oleo_id` | `bigint` | ✓ |
| `codigo_externo` | `varchar` | ✓ |
| `numero_laboratorio` | `bigint` | ✓ |
| `coleta_amostra_id` | `bigint` | ✓ |
| `ja_foi_segregada` | `bit` | ✓ |
| `descricao_oleo` | `varchar` | ✓ |
| `data_finalizacao` | `datetime2` | ✓ |
| `nome_compartimento` | `varchar` | ✓ |
| `tipo_compartimento_id` | `bigint` | ✓ |
| `tipo_coleta_amostra` | `bigint` | ✓ |
| `data_desegregacao` | `datetime2` | ✓ |
| `houve_pre_registro` | `bit` | ✓ |
| `data_registro_coleta` | `datetime2` | ✓ |
| `prazo_entrada_laboratorio` | `bigint` | ✓ |
| `prazo_entrega` | `bigint` | ✓ |
| `prazo_interpretacao` | `bigint` | ✓ |
| `prazo_laboratorio` | `bigint` | ✓ |
| `prazo_registro_coleta_laboratorio` | `bigint` | ✓ |
| `prazo_solucao_segregado` | `bigint` | ✓ |
| `obra_id` | `bigint` | ✓ |
| `fix_id` | `bigint` | ✓ |
| `pos_pago` | `bit` | ✓ |
| `data_processo` | `datetime2` | ✓ |
| `data_saida_laboratorio` | `datetime2` | ✓ |
| `data_atualizacao_finalizacao` | `datetime2` | ✓ |
| `laboratorio_id` | `bigint` | ✓ |
| `valor_servico_valor` | `decimal` | ✓ |
| `valor_servico_moeda` | `varchar` | ✓ |
| `operacao_id` | `varchar` | ✓ |
| `valido_no_programa` | `bit` | ✓ |
| `modelo_oleo_id` | `bigint` | ✓ |
| `rack_id` | `bigint` | ✓ |
| `agente_coleta` | `bigint` | ✓ |
| `responsavel_registro_id` | `bigint` | ✓ |
| `finished_sample_index_submission_date` | `datetime2` | ✓ |
| `responsible_to_close_data_entry_issue_id` | `bigint` | ✓ |
| `data_entry_activity` | `varchar` | ✓ |
| `numero_amostra_idx` | `varchar` | ✓ |
| `operation_id` | `int` | ✓ |
| `test_package_deadline` | `int` | ✓ |
| `laboratory_deadline` | `int` | ✓ |

#### Tabela: `amostra_plano_analise`

**Colunas**: 7

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `amostra_id` | `bigint` | ✓ |
| `plano_analise_id` | `bigint` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `fixo` | `bit` | ✓ |

#### Tabela: `analise_grupos_trabalho`

**Colunas**: 2

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `analise_id` | `bigint` | ✓ |
| `grupo_trabalho_id` | `bigint` | ✓ |

#### Tabela: `analise_traducao`

**Colunas**: 9

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `analise_id` | `bigint` | ✓ |
| `locale` | `varchar` | ✓ |
| `version` | `bigint` | ✓ |
| `abreviacao` | `varchar` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `metodo` | `varchar` | ✓ |
| `nome` | `varchar` | ✓ |
| `unidade_medida` | `varchar` | ✓ |

#### Tabela: `atividade_base`

**Colunas**: 5

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `data` | `datetime2` | ✓ |
| `tipo` | `int` | ✓ |
| `usuario_id` | `bigint` | ✓ |

#### Tabela: `atividade_resultado_analise`

**Colunas**: 2

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `entidade_referenciada_id` | `bigint` | ✓ |

#### Tabela: `cliente`

**Colunas**: 42

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `ativo` | `bit` | ✓ |
| `data_nascimento` | `datetime2` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `nome` | `varchar` | ✓ |
| `razao_social` | `varchar` | ✓ |
| `sexo_id` | `bigint` | ✓ |
| `tipo_cliente` | `int` | ✓ |
| `dealer` | `varchar` | ✓ |
| `envio_relatorio_sem_interpretacao` | `bit` | ✓ |
| `inadimplente` | `bit` | ✓ |
| `seguimento_cliente_id` | `bigint` | ✓ |
| `tipo_forma_pagamento_cliente` | `bigint` | ✓ |
| `tipo_conta_cliente_id` | `bigint` | ✓ |
| `grupo_clientes_id` | `bigint` | ✓ |
| `codigo_legado` | `varchar` | ✓ |
| `programa_padrao_id` | `bigint` | ✓ |
| `ordenar_por_horimetro_equipamentopdf` | `bit` | ✓ |
| `exibir_legendapdf` | `bit` | ✓ |
| `fazer_interpretacao_ativa` | `bit` | ✓ |
| `gerar_interpretacao` | `bit` | ✓ |
| `layout_importacao_coleta` | `varchar` | ✓ |
| `data_atualizacao_hubspot` | `datetime2` | ✓ |
| `identificador_hub_spot` | `bigint` | ✓ |
| `idioma_interpretacao` | `varchar` | ✓ |
| `operacao_id` | `varchar` | ✓ |
| `modelo_relatorio_enum` | `varchar` | ✓ |
| `fazer_auto_interpretacao` | `bit` | ✓ |
| `id_cigam` | `varchar` | ✓ |
| `setor_cliente_id` | `bigint` | ✓ |
| `termo_pagamento_id` | `bigint` | ✓ |
| `mercado_cliente_id` | `bigint` | ✓ |
| `cliente_integracao_sisma_id` | `bigint` | ✓ |
| `obra_padrao_id` | `bigint` | ✓ |
| `estrangeiro_na_operacao` | `bit` | ✓ |
| `sam_id` | `varchar` | ✓ |
| `short_code` | `varchar` | ✓ |
| `currency` | `varchar` | ✓ |
| `twist_id` | `varchar` | ✓ |
| `tax` | `float` | ✓ |

#### Tabela: `compartimento`

**Colunas**: 19

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `ativo` | `bit` | ✓ |
| `codigo_externo` | `varchar` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `equipamento_id` | `bigint` | ✓ |
| `nome` | `varchar` | ✓ |
| `num_serie` | `varchar` | ✓ |
| `tipo_compartimento_id` | `bigint` | ✓ |
| `volume` | `real` | ✓ |
| `descricao_oleo` | `varchar` | ✓ |
| `fabricante_oleo_id` | `bigint` | ✓ |
| `modelo_oleo_id` | `bigint` | ✓ |
| `viscosidade_oleo_id` | `bigint` | ✓ |
| `horas_oleo` | `int` | ✓ |
| `oleo_trocado` | `varchar` | ✓ |
| `sam_id` | `varchar` | ✓ |
| `uin` | `varchar` | ✓ |

#### Tabela: `equipamento`

**Colunas**: 20

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `ativo` | `bit` | ✓ |
| `chassi_serie` | `varchar` | ✓ |
| `codigo_externo` | `varchar` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `filtro_oil_check` | `bit` | ✓ |
| `modelo` | `varchar` | ✓ |
| `tag_frota` | `varchar` | ✓ |
| `tamanho_metrica_controle` | `int` | ✓ |
| `controle_importacao_id` | `bigint` | ✓ |
| `fabricante_equipamento_id` | `bigint` | ✓ |
| `familia_equipamento_id` | `bigint` | ✓ |
| `obra_id` | `bigint` | ✓ |
| `tipo_metrica_controle` | `int` | ✓ |
| `area` | `varchar` | ✓ |
| `setor` | `varchar` | ✓ |
| `saude` | `real` | ✓ |
| `sam_id` | `varchar` | ✓ |

#### Tabela: `expedicao`

**Colunas**: 15

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `cancelado` | `bit` | ✓ |
| `cliente_id` | `bigint` | ✓ |
| `data_nota` | `datetime2` | ✓ |
| `observacao` | `varchar` | ✓ |
| `numero` | `varchar` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `pos_pago` | `bit` | ✓ |
| `programa_id` | `bigint` | ✓ |
| `numero_notafiscal_servico` | `varchar` | ✓ |
| `valor_total_servico_valor` | `decimal` | ✓ |
| `valor_total_servico_moeda` | `varchar` | ✓ |
| `operacao_id` | `varchar` | ✓ |

#### Tabela: `grupo_trabalho`

**Colunas**: 6

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `ativo` | `bit` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `forma_resultado_grupo_trabalho_enum` | `int` | ✓ |

#### Tabela: `grupo_trabalho_laboratorios`

**Colunas**: 2

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `laboratorio_id` | `bigint` | ✓ |
| `grupo_trabalho_id` | `bigint` | ✓ |

#### Tabela: `grupo_trabalho_traducao`

**Colunas**: 6

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `grupo_trabalho_id` | `bigint` | ✓ |
| `locale` | `varchar` | ✓ |
| `version` | `bigint` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `nome` | `varchar` | ✓ |

#### Tabela: `laboratorio`

**Colunas**: 21

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `nome` | `varchar` | ✓ |
| `endereco_id` | `bigint` | ✓ |
| `impressora_id` | `bigint` | ✓ |
| `operacao_id` | `varchar` | ✓ |
| `entrar_sem_coleta` | `bit` | ✓ |
| `time_zone` | `varchar` | ✓ |
| `trabalha_com_rack` | `bit` | ✓ |
| `tamanho_maximo_rack` | `int` | ✓ |
| `laboratory_entry_deadline` | `int` | ✓ |
| `interpretation_deadline` | `int` | ✓ |
| `missing_pre_registration_deadline` | `int` | ✓ |
| `desegregation_deadline` | `int` | ✓ |
| `missing_test_package_deadline` | `int` | ✓ |
| `financial_pending_deadline` | `int` | ✓ |
| `out_of_bottle_deadline` | `int` | ✓ |
| `out_of_program_deadline` | `int` | ✓ |
| `analysis_review_deadline` | `int` | ✓ |

#### Tabela: `layouts_grupo_trabalho`

**Colunas**: 5

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `layout` | `varchar` | ✓ |
| `grupo_trabalho_id` | `bigint` | ✓ |
| `parametros` | `varchar` | ✓ |
| `apelido` | `varchar` | ✓ |

#### Tabela: `plano_analise`

**Colunas**: 6

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `ativo` | `bit` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `prazo` | `int` | ✓ |

#### Tabela: `plano_analise_traducao`

**Colunas**: 7

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `plano_analise_id` | `bigint` | ✓ |
| `locale` | `varchar` | ✓ |
| `version` | `bigint` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `nome` | `varchar` | ✓ |
| `aplicacao` | `varchar` | ✓ |

#### Tabela: `produto_caixa_expedicoes`

**Colunas**: 2

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `expedicao_id` | `bigint` | ✓ |
| `produto_caixa_id` | `bigint` | ✓ |

#### Tabela: `recebimento_amostra`

**Colunas**: 16

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `cliente_id` | `bigint` | ✓ |
| `conhecimento_frete` | `varchar` | ✓ |
| `data_postagem` | `datetime2` | ✓ |
| `data_recebimento` | `datetime2` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `observacao` | `varchar` | ✓ |
| `endereco_id` | `bigint` | ✓ |
| `laboratorio_id` | `bigint` | ✓ |
| `forma_recebimento_id` | `bigint` | ✓ |
| `codigo_transportadora` | `varchar` | ✓ |
| `obra_id` | `bigint` | ✓ |
| `responsible_id` | `bigint` | ✓ |
| `data_recebimento_original` | `datetime2` | ✓ |

#### Tabela: `recebimento_amostra_amostra`

**Colunas**: 6

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `amostra_id` | `bigint` | ✓ |
| `recebimento_amostra_id` | `bigint` | ✓ |
| `segregado` | `bit` | ✓ |
| `tipo_compartimento_id` | `bigint` | ✓ |

#### Tabela: `resultado_amostra`

**Colunas**: 21

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `amostra_id` | `bigint` | ✓ |
| `data_liberacao_para_interpretacao` | `datetime2` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `cliente_id` | `bigint` | ✓ |
| `resultado_interpretacao_amostra` | `bigint` | ✓ |
| `status_resultado_amostra` | `bigint` | ✓ |
| `responsavel_id` | `bigint` | ✓ |
| `data_interpretacao_finalizada` | `datetime2` | ✓ |
| `informacoes_ao_cliente` | `varchar` | ✓ |
| `texto_interpretacao` | `varchar` | ✓ |
| `email_enviado` | `bit` | ✓ |
| `idioma_na_interpretacao` | `varchar` | ✓ |
| `data_alteracao_recomendacao_comentario` | `datetime2` | ✓ |
| `responsavel_edicao_recomendacao_comentario_id` | `bigint` | ✓ |
| `cobertura` | `real` | ✓ |
| `sugestao_resultado_interpretacao_amostra` | `varchar` | ✓ |
| `parametro_interpretacao_id` | `bigint` | ✓ |
| `updated_by_user` | `bit` | ✓ |

#### Tabela: `resultado_analise`

**Colunas**: 21

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `amostra_id` | `bigint` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_resultado` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `motivo_analise` | `varchar` | ✓ |
| `valor` | `varchar` | ✓ |
| `laboratorio_id` | `bigint` | ✓ |
| `analise_id` | `bigint` | ✓ |
| `arquivo_id` | `bigint` | ✓ |
| `tipo_valor_analise_enum` | `int` | ✓ |
| `responsavel_id` | `bigint` | ✓ |
| `resultado_interpretacao_amostra` | `bigint` | ✓ |
| `quantidade_reanalise` | `int` | ✓ |
| `origem_reanalise_enum` | `int` | ✓ |
| `responsavel_reanalise_id` | `bigint` | ✓ |
| `status_resultado_analise` | `smallint` | ✓ |
| `parametro_interpretacao_valor_id` | `bigint` | ✓ |
| `grupo_trabalho_id` | `bigint` | ✓ |
| `resultado_sugerido_parametro` | `varchar` | ✓ |

#### Tabela: `tipo_compartimento_traducao`

**Colunas**: 7

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `tipo_compartimento_id` | `bigint` | ✓ |
| `locale` | `varchar` | ✓ |
| `version` | `bigint` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `descricao` | `varchar` | ✓ |
| `nome` | `varchar` | ✓ |

#### Tabela: `tipo_produto`

**Colunas**: 8

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `ativo` | `bit` | ✓ |
| `nome` | `varchar` | ✓ |
| `programa_id` | `bigint` | ✓ |
| `quantidade_kits` | `int` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |

#### Tabela: `usuario`

**Colunas**: 31

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `id` | `bigint` | ✓ |
| `version` | `bigint` | ✓ |
| `ativo` | `bit` | ✓ |
| `data_registro` | `datetime2` | ✓ |
| `data_ultima_atualizacao` | `datetime2` | ✓ |
| `email` | `varchar` | ✓ |
| `foto_id` | `bigint` | ✓ |
| `login` | `varchar` | ✓ |
| `nome_completo` | `varchar` | ✓ |
| `senha` | `varchar` | ✓ |
| `identidade_visual_id` | `bigint` | ✓ |
| `cargo` | `varchar` | ✓ |
| `celular` | `varchar` | ✓ |
| `data_ultimo_login` | `datetime2` | ✓ |
| `exibir_interpretacao` | `bit` | ✓ |
| `receber_anexo` | `bit` | ✓ |
| `telefone` | `varchar` | ✓ |
| `laboratorio_padrao_id` | `bigint` | ✓ |
| `resultado_email_enum` | `int` | ✓ |
| `idioma` | `varchar` | ✓ |
| `layout_exportacao` | `varchar` | ✓ |
| `identificador_hub_spot` | `bigint` | ✓ |
| `data_atualizacao_hubspot` | `datetime2` | ✓ |
| `email_invalido` | `bit` | ✓ |
| `time_zone` | `varchar` | ✓ |
| `tipo_ordenacao` | `varchar` | ✓ |
| `pode_gerenciar_senha` | `bit` | ✓ |
| `locked` | `bit` | ✓ |
| `zipped_attachment` | `bit` | ✓ |
| `send_brand_on_sample_result_email` | `bit` | ✓ |
| `rule_to_send_sample_result_email_enum` | `varchar` | ✓ |

