# Matriz de cobertura dos insumos (Etapa 1)

> Estado em 27/10/2026. Responde à Etapa 1 de [12](12_plano_trabalho_esboco.md): cada insumo dos KPIs 1 e 2 existe, com granularidade, histórico e qualidade suficientes? Tarefa T04 do [BACKLOG](../BACKLOG.md).

## Base da evidência (leia antes da tabela)

- **Schema:** `fabric_probe_results.json` e [08 discovery](08_dicionario_de_dados_discovery.md) (colunas e tipos reais do `LakehouseOel`, lidos em somente leitura).
- **Planilhas:** números de [14](14_fase0_engenharia_reversa_e_base_de_codigo.md) §1 (Customer Status, Forecast 27, Calculadora).
- **Perfil (T02) e chaves (T03): sem saída neste worktree.** `data/perfil` não existe e a tabela de chaves de 14 §2 ainda diz "a confirmar". O probe só traz nomes e tipos de colunas, sem contagem de linhas, nulos nem período. Por isso nenhuma célula abaixo tem volume, nulos ou taxa de casamento inventados: onde o número vem do perfil, a coluna "Evidência" diz **pendente T02** ou **pendente T03**.
- **Critério de status usado:** ✅ = coluna existe no schema e o insumo se resolve com ela; ⚠️ = existe mas depende de join, é derivado, ou tem lacuna conhecida; ❌ = não existe na base. Não sobrou ❓: o que falta medir virou ⚠️ com "medir" no plano. Quando T02/T03 rodarem, trocar "pendente" pelo número e rever o status.

## Matriz

| # | Insumo | KPI | Status | Tabela / coluna real | Granularidade | Histórico | Evidência |
|---|---|---|---|---|---|---|---|
| 1 | Amostras (data, cliente, compartimento, status) | 1 e 2 | ✅ | `bronze_s360.amostra`: `data_coleta`, `cliente_id`, `compartimento_id`, `status_amostra`, `excluido`, `numero_amostra` (64 colunas) | 1 linha por amostra | desde 2022 não verificado | Colunas existem. Volume, duplicatas e período: **pendente T02** |
| 2 | ID do equipamento | 1 | ⚠️ | Sem `equipamento_id` em `amostra`. Caminho: `amostra.compartimento_id` → `compartimento.equipamento_id` → `equipamento.id`. `equipamento` não tem `cliente_id` | por equipamento | — | Schema confirma o caminho em 3 saltos. Avulsas (sem compartimento) ficam sem equipamento: taxa **pendente T02/T03** (reunião de 21/10 relata o problema) |
| 3 | Horímetro | 1 | ⚠️ | `amostra.horas_oleo` (int), `amostra.horimetro_equipado` (int); `compartimento.horas_oleo` | uma leitura por coleta, não série contínua | idem | Colunas existem ([04](04_notas_dados.md)). Monotonicidade, lacunas e outliers: **pendente T02** |
| 4 | Compartimento | 1 | ✅ | `bronze_s360.compartimento`: `equipamento_id`, `tipo_compartimento_id`, `nome`, `ativo`, `volume` (19 colunas); `tipo_compartimento_traducao` para o nome | por compartimento | — | Colunas existem. Silver não tem `compartimento` nem `equipamento` (só bronze, [04](04_notas_dados.md)) |
| 5 | Intervalo de coleta (250/500/1000 h) | 1 | ❌ | Não há coluna de intervalo no S360. Existe só na planilha: [specs/calculadora_compartimentos.csv](../specs/calculadora_compartimentos.csv) (22 famílias) | por família × compartimento | — | Calculadora v8 reproduz 48 de 50 blocos ([14](14_fase0_engenharia_reversa_e_base_de_codigo.md) §1). `equipamento.familia_equipamento_id` não tem tabela de nome |
| 6 | Cliente / raiz CNPJ ↔ ERP ID | 1 e 2 | ⚠️ | S360 `cliente`: `codigo_legado`, `id_cigam`, `sam_id` (sem CNPJ). Protheus `notassaida`: `cod_cliente` + `loja`. Zoho `accounts`: `id_protheus`, `business_number`, `matriz`/`parent_account` | por cliente | — | Customer Status: 2.388 clientes, ERP ID em 6 dígitos (1.689) ou `A`+5 (697). Taxa de casamento S360↔Protheus↔Zoho: **pendente T03** |
| 7 | Faturamento (valor, data, item) | 2 | ✅ | `silver_protheus.notassaida`: `emissao`, `total`, `quantidade`, `preco`, `cod_produto`, `cod_cliente`, `loja`, `num_pedido`, `filial` (36 colunas). `bronze_protheus` tem tudo como `varchar` | por item de nota | desde 2022 não verificado | Colunas existem. Vínculo com amostra: ver linha 8. Período e devoluções (`devolucao`): **pendente T02** |
| 8 | Vínculo faturamento ↔ amostra | 2 | ❌ | Nenhuma chave entre `notassaida` e `amostra`. Há `silver_s360.fato_amostra_concluida.receita_valor`/`receita_moeda` (receita atribuída por amostra, origem a confirmar) | cliente × mês | — | Forecast 27 trabalha em nível de cliente e mês, sem precisar do vínculo por amostra |
| 9 | Pedidos pendentes | 2 | ⚠️ | `silver_protheus.pedvendas` tem `cod_fornecedor`, `pedido_compra`, `centro_custo`: parece pedido de **compra**, não de venda. Alternativa: `silver_zoho.sales_orders` | por pedido | — | Natureza de `pedvendas` não confirmada; frescor: **pendente T02** |
| 10 | Oportunidades abertas | 2 | ✅ | `silver_zoho.deals`: `estagio`, `valor`, `probabilidade`, `conta_id`, `data_fechamento_prevista`, `data_fechamento_real`, `motivo_perda` (28 colunas) | por oportunidade | — | Colunas existem. Preenchimento de `valor` e estágio: **pendente T02** |
| 11 | Segmento do cliente | 1 e 2 | ⚠️ | S360 `cliente`: `seguimento_cliente_id`, `setor_cliente_id`, `mercado_cliente_id` (só IDs, sem tabela de nomes na lista de tabelas). Zoho `accounts`: `segment`, `cod_segment`, `sector`, `customer_segmentation` | por cliente | — | Customer Status traz Sector e Segment por cliente (2.388). Preenchimento no S360/Zoho: **pendente T02** |
| 12 | Status do cliente (ativo/churn) | 1 e 2 | ⚠️ | Zoho `accounts.real_status`, `status`; S360 `cliente.ativo`. Regra derivável: última atividade = máx(venda, amostra) | por cliente | — | Regra de 14 §1 explica 90,8% do `Real Status` do Customer Status; os ~9% restantes são ajuste manual |
| 13 | Annual Sample Potential | 1 (Potencial) | ❌ | Não há coluna. Candidatos em Zoho `accounts`: `initial_quantity_of_active_equipment`, `equipment_monitored_in_the_last_24_months_active`, `average_samples_per_month_last_6_months_trend` | por cliente | — | Customer Status: preenchido para 1.314 clientes (soma 1,19 milhão/ano), valores colados sem fórmula (R1). Origem é a T05 |
| 14 | Ticket médio e conversão | 2 | ⚠️ | Derivável de `notassaida` (`total`/`quantidade`) e `fato_amostra_concluida.receita_valor`; conversão de `deals` | por cliente × mês | — | Planilha usa R$ 1.950 e 5% (out/2022, defasados, RN-11). Recálculo: **pendente T02** |
| 15 | Calendário / sazonalidade | 1 e 2 | ✅ | `silver_s360.dim_calendario`; sazonalidade derivada nas features (`src/features/series.py`) | por dia | — | Forecast 27 já aplica % de mercado por mês (hibernação da cana, recesso, carnaval) |

Contagem: ✅ 5 · ⚠️ 7 · ❌ 3 · ❓ 0.

## Plano para cada ⚠️ e ❌

| # | Lacuna | Decisão | Plano | Dono |
|---|---|---|---|---|
| 2 | Equipamento sem vínculo direto na amostra; avulsas | **Derivar** | Join amostra → compartimento → equipamento; amostras com `compartimento_id` nulo vão para a classe "avulsa" (limpeza em T14). Medir a taxa de avulsas por cliente e o efeito no KPI 1 | @analista-dados |
| 3 | Horímetro é leitura por coleta | **Aceitar a limitação** + derivar | Estimar uso por intervalo entre coletas (horas/dia) e marcar confiança; descartar leituras não monotônicas depois de medir quantas são | @especialista-dados |
| 5 | Intervalo 250/500/1000 h só na planilha | **Derivar** | Carregar `calculadora_compartimentos.csv` como tabela de parâmetros por família. Pedir ao time de dados a tabela de nomes de `familia_equipamento_id` para casar S360 ↔ família da Calculadora | @engenheiro-software; pedido ao time de dados |
| 6 | Chave cliente entre fontes | **Derivar** + medir | Medir (T03) `codigo_legado`/`id_cigam` ↔ `cod_cliente`+`loja` e `id_protheus` ↔ ERP ID. Clientes sem casamento ficam fora do KPI 2 por cliente, mas entram no total. Se a taxa for baixa, pedir ao time de dados o CNPJ no S360 | @analista-dados |
| 8 | Faturamento sem vínculo com amostra | **Aceitar a limitação** | Modelar o KPI 2 em cliente × mês, como o Forecast 27, e correlacionar consumo e venda nesse nível (T17). Confirmar a origem de `receita_valor` antes de usá-lo | @cientista-dados |
| 9 | `pedvendas` parece compra | **Pedir ao time de dados** | Confirmar se há pedido de venda pendente no Protheus (tabela ou filtro por tipo). Sem isso, usar `sales_orders` do Zoho como aproximação e registrar a diferença | @analista-dados |
| 11 | Segmento: IDs sem nomes no S360 | **Derivar** | Usar o segmento do Zoho (`segment`, `sector`) e o do Customer Status como dimensão; medir o preenchimento. Pedir ao time de dados as tabelas de domínio de `seguimento_cliente_id`/`setor_cliente_id` | @analista-dados |
| 12 | Status: ~9% por ajuste manual | **Derivar** + aceitar | Aplicar a regra de 14 §1; preservar o `Real Status` da planilha só como referência de validação | @especialista-dados |
| 13 | Sem origem do potencial | **Derivar** (T05) | Descobrir a origem por dados (T05). Se não houver, benchmark por similares (segmento × família) com `average_samples_per_month_last_6_months_trend` e equipamentos ativos como candidatos (T16). Decisão final com o negócio (Bahia) | @especialista-dados |
| 14 | Ticket e conversão defasados | **Derivar** | Recalcular de `notassaida` e `deals`, por segmento e por ano; substituir R$ 1.950 e 5% (RN-11) | @cientista-dados |

## Pendências para fechar a matriz

1. **T02:** preencher volume, período, nulos e duplicatas das linhas 1, 3, 7, 9, 10, 11 e 14, e confirmar o histórico desde 2022.
2. **T03:** preencher as taxas de casamento da linha 6 e das ligações cliente → equipamento → compartimento → amostra (linhas 1 e 2).
3. Ao receber os números, atualizar esta página, a tabela de chaves de [14](14_fase0_engenharia_reversa_e_base_de_codigo.md) §2 e o status das linhas que mudarem de ⚠️ para ✅ ou ❌.

**Critério de saída da Etapa 1** ([12](12_plano_trabalho_esboco.md)): todo insumo ✅ ou ⚠️ com decisão registrada, sem ❓. Atendido quanto à decisão. As três linhas ❌ (5, 8, 13) têm plano (derivar ou aceitar). A confirmação numérica depende de T02 e T03.
