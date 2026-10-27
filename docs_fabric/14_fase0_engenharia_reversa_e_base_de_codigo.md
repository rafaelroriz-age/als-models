# Fase 0: engenharia reversa das planilhas e base de código

> Estado em 27/10/2026. Complementa as hipóteses e descobertas de [13](13_revisao_alinhamento_reuniao_2026-10-21.md).

## 1. Descobertas nas planilhas

### Forecast 27 (regra atual de receita)
- **H4 resolvida: é E.** Texto da própria planilha: "faturado em pelo menos 6 meses diferentes nos últimos 12 meses completos. A última compra precisa ter ocorrido nos últimos 90 dias em relação à data de corte (31/08)".
- Novos e reativados viram recorrentes após 3 meses, com 50% do valor (Diego): `Recorrente(t) = base(t) + ½ × (novos + reativados)(t−3)`.
- Churn = mais de 6 meses sem comprar; receita perdida = média dos 6 meses anteriores à última compra.
- Total = (recorrente + não recorrente + novos + reativados) − churn; depois × (1 + variável de mercado), um % manual por mês com justificativa sazonal (hibernação da cana, recesso, carnaval).
- **Réplica em Python reproduz a planilha de set a fev ao centavo.** Em março a planilha soma de novo ½ dos novos de setembro (`C8 = B8 + E5/2 + F5/2 + E2/2`): +R$ 100 mil no recorrente e +R$ 92 mil no total. Parece erro de fórmula; confirmar com Diego/Keli.

### Customer Status 2026 (aba `data CLIENTES`, 2.388 clientes)
- `Recorrencia Fat = COUNTIF(12 meses, ">1")` e recorrente = `>= 6`. **A planilha não aplica os 90 dias**, mas na prática quase não muda: 233 recorrentes só com ≥6 meses e 231 com a regra E (com a regra OU seriam 813).
- `ERP ID` é a chave do Protheus (`cod_cliente`): a aba `data CLIENTES (2)` monta o faturamento mensal por `SUMIFS` num extrato externo pelo ERP ID. Formatos: 6 dígitos (1.689) e `A` + 5 dígitos (697).
- **`Real Status` e `Annual Sample Potential` são valores colados, sem fórmula (R1).** Uma regra explica 90,8% do status: última atividade = máx(última venda, última amostra), com ≤90 dias Active, 91–180 Inactive e >180 Churn (referência 10/08/2026). Os casos restantes são majoritariamente Churn com amostra recente e venda antiga, ou seja, ajuste manual.
- Potencial preenchido para 1.314 clientes (soma 1,19 milhão de amostras/ano). Mediana por segmento: cana 788, florestal 568, mobile 314, construção 208. A fórmula de origem não está na planilha e continua como descoberta com o Bahia (R1).
- `% Achieved = amostras do período ÷ potencial anual`. Atenção: o numerador cobre só abr–jul (4 meses), enquanto o denominador é anual.

### Calculadora v8 (R2)
- Regra por família: `amostras/ano = máquinas × Σ ⌊uso/ano ÷ intervalo do compartimento⌋`. O uso é em horas, ou em km quando horas ≤ 1 (caminhões). Há três variantes: sem diesel, com diesel e "3 amostras/compartimento/ano".
- Faturamento (dealer) = amostras × 5% de conversão × R$ 1.950 de ticket (out/2022, defasado). A aba MSC usa `horas/ano ÷ 1000 × 12 × frota`.
- **22 famílias** em 3 setores: Construção/Mineração, Agro e Florestal. Confirma a estimativa do Bahia de 20–30 famílias. Configuração extraída em [specs/calculadora_familias.csv](../specs/calculadora_familias.csv) e [specs/calculadora_compartimentos.csv](../specs/calculadora_compartimentos.csv).
- **48 de 50 blocos reproduzidos.** Os 2 divergentes (caminhões agro "com diesel") têm zeros digitados no lugar da fórmula.

## 2. Chaves entre fontes (medido em 2026-10-27, T03)
Medição somente leitura por `notebooks/00_validacao/02_validar_chaves.py` (saída em `data/chaves/chaves.json`, fora do git; normalização em `src/pipeline/chaves.py`). % = chaves distintas que casam; "% fat." = ponderado pelo faturamento Protheus (`notassaida.total`).

| Fonte | Campo | Medido |
|---|---|---|
| Protheus `notassaida` | `cod_cliente` (+ `loja`; 99,3% das combinações são loja `01`) | 2.850 códigos; 2.823 no formato `A`+5 dígitos |
| Zoho `accounts` | `erp_id`, `cnpj`; `id_protheus` | 9.843 contas; `id_protheus` 100% nulo; `erp_id` nulo em 1.824 (18,5%); `cnpj` nulo em 1.776 e inválido/zerado em 1.018 |
| S360 `cliente` | `codigo_legado`, `id_cigam`, `sam_id` | **sem CNPJ**; 1.675 de 10.232 clientes (16,4%) sem `codigo_legado` nem `id_cigam`; ERP ID = `id_cigam` (casa 2.339 de 2.388 ERPs do Customer Status; `codigo_legado` só 1.328; T05, doc 13 §3) |
| S360 `equipamento` | `familia_equipamento_id` | **sem `cliente_id`**; o cliente vem de `amostra.cliente_id` (amostra → compartimento → equipamento); não há tabela de nome da família |

**Casamento medido**

| Ligação | Resultado |
|---|---|
| Protheus `cod_cliente` ↔ S360 `id_cigam` | 1.144 de 2.850 (**40,1%**; 11,1% do fat.) |
| Protheus `cod_cliente` ↔ S360 `codigo_legado` | 9 de 2.850 (**0,3%**): `codigo_legado` **não** é o ERP ID; `id_cigam` é o candidato |
| Protheus ↔ S360, regra de grupo (abaixo) | 1.440 de 2.849 (**50,5%**; 44,8% do fat.); últimos 12 meses 51,8% (43,0% do fat.) |
| Zoho `erp_id` ↔ Protheus `cod_cliente` | exato 16,2% (1.280 de 7.881); por grupo 34,4% (1.566 de 4.550). Sentido Protheus → Zoho: 44,9% exato, 55,0% por grupo (44,9% do fat.) |
| Zoho `erp_id` ↔ S360 (`codigo_legado` ou `id_cigam`) | 78,2% exato (6.159 de 7.881); 66,4% por grupo. Sentido S360 → Zoho: 72,7% exato, 83,1% por grupo |
| Raiz CNPJ ↔ ERP ID (só no Zoho) | 6.141 contas têm os dois; 4.103 raízes; **771 raízes têm mais de um `erp_id`** (739 por grupo); 163 contas com `erp_id` repetido; 3 `erp_id` com mais de uma raiz; 1.052 contas com CNPJ completo repetido |
| Zoho conta ↔ S360 por razão social exata (normalizada) | 59,7% (3.153 de 5.286); das 1.926 contas que não casam por ERP, 569 casam por nome |
| Cadeia S360, amostras não excluídas de 2022+ (4.036.512) | `cliente_id`: 13 nulos, 0 órfãos · `compartimento_id`: 92.527 nulos (2,3%), 0 órfãos · compartimento → equipamento: 0 nulos, 0 órfãos · cadeia completa amostra → compartimento → equipamento: 3.943.985 (**97,7%**) · nenhum equipamento aparece com mais de um cliente |
| Compartimentos (3.478.601) | 100% com equipamento válido |
| Equipamentos | 371.300 de 1.063.706 (34,9%) têm amostra desde 2022 |

**Regra de grupo.** O código numérico de 6 dígitos do S360/Zoho (ex.: `191295`) parece ser o código Protheus + 1 dígito de filial: `A19129` + `5`. Vários clientes S360 (filiais) mapeiam para um código Protheus (ex.: `A19129`, Soluções Integradas Verdes Vales no Zoho, tem 6 filiais no S360). Implementada em `chave_grupo()`. É inferência por padrão de código e por nomes conferidos em amostra; falta confirmação do time de dados.

**Principais motivos de não casamento**
1. **Dois formatos de ERP ID no S360** (`A#####` e `######`): sem a regra de grupo o casamento Protheus ↔ S360 cai de 50,5% para 40,1%.
2. **Cobertura**: 16,4% dos clientes S360 não têm código ERP, 18,5% das contas Zoho não têm `erp_id`, e o CNPJ do Zoho é nulo ou inválido em 28%. Sem CNPJ no S360 e no Protheus, a raiz CNPJ só liga contas dentro do Zoho.
3. **Protheus fatura clientes ausentes do S360**: 1.409 dos 2.849 grupos (49,5%) ficam sem par, com 55,2% do faturamento. Os cinco maiores (A12456, ZOAG81, A57577, A19524, A17331) somam R$ 18,5 mi. A causa (cliente sem coleta, venda de peças, intercompany, código guardado de outro jeito) **não foi apurada**.
4. **Duplicidade**: `codigo_legado` repetido em 433 clientes e `id_cigam` em 48; em 286 clientes `codigo_legado` ≠ `id_cigam`.

**Impacto nos KPIs**
- **KPI 1 (amostras)** não depende do Protheus: o cliente vem de `amostra.cliente_id` (sem órfãos) e a cadeia até o equipamento fecha em 97,7%. As perdas são 2,3% de amostras sem compartimento (avulsas, tratadas na RN de recorrência) e 161.455 amostras (4,0%) de clientes sem código ERP, que ficam sem ponte para Zoho/Protheus. Pelo Zoho, 98,7% das amostras de 2022+ são de clientes cujo grupo ERP existe lá.
- **KPI 2 (vendas)**: só 27,6% das amostras de 2022+ (44,1% dos clientes) pertencem a clientes que também aparecem no Protheus por grupo, e apenas 44,8% do faturamento Protheus tem cliente S360. A tabela-base (T14) não pode juntar faturamento e consumo por `cod_cliente` sem a regra de grupo; mesmo com ela, o faturamento restante só entra no nível agregado. A ponte Zoho cobre 98,7% das amostras, mas só 44,9% do faturamento Protheus.
- Pendências para o time de dados: confirmar a regra de grupo; explicar por que `id_protheus` do Zoho está 100% nulo; fornecer CNPJ para S360 e Protheus; explicar os grandes clientes Protheus sem par no S360.

## 3. Base de código (pronta para rodar local e no Fabric)
| Caminho | Conteúdo |
|---|---|
| `src/pipeline/fabric.py` | Leitura somente leitura: local via SQL endpoint (pyodbc, login em cache) ou Spark no Fabric |
| `src/features/regras.py` | Recorrência (E), churn, novo/reativado, status, receita de churn, % Achieved, avulsas, meses contínuos |
| `src/features/calculadora.py` | Calculadora v8 em Python + leitor/validador da planilha |
| `src/models/baselines.py` | Ingênuo sazonal, médias móveis 3 e 12 e réplica do Forecast 27 |
| `src/backtest/harness.py` | Rolling origin, WAPE/MAE/viés/sMAPE/cobertura, agregação, MLflow |
| `src/gates/checks.py` | Gates G0 (fontes) e G1 (tabela-base) |
| `notebooks/00_validacao/01_perfil_qualidade.py` | Perfil das 8 tabelas-chave + 10 extrações agregadas (séries mensais, chaves, famílias, equipamentos, produtos, deals) |
| `notebooks/00_validacao/02_validar_chaves.py` + `src/pipeline/chaves.py` | Taxa de casamento das chaves S360 ↔ Protheus ↔ Zoho (T03, §2); `chave_erp`, `chave_grupo`, `raiz_cnpj`, `taxa_casamento` |
| `notebooks/00_validacao/02_engenharia_reversa_planilhas.py` | Gera os números desta página |
| `notebooks/40_backtest/01_backtest_baselines.py` | Backtest dos baselines nos KPIs 1 e 2 (total e por cliente) |
| `scripts/fabric_deploy.py` | Wheel + notebooks `.ipynb`; com `--aplicar`, publica no workspace |
| `tests/` | 24 testes, incluindo os casos de borda de 6 meses e 90 dias e as réplicas das planilhas |

Execução local: `python -m pytest`, depois `python notebooks/00_validacao/02_engenharia_reversa_planilhas.py`. O perfil exige a porta 1433 liberada. Extrações de dados vão para `data/`, que fica fora do git.

## 4. Bloqueios e pendências
- **Conectividade (T01, 2026-10-27, 13:23, rede atual):** `Test-NetConnection` ao endpoint `j2qfysdun5iebf3ezw2l7ke4eu-vpyatc664ptezeejap7oap22qu.datawarehouse.fabric.microsoft.com` (IP 191.235.225.198) retornou `TcpTestSucceeded: True` nas portas **1433** e **443**. A 1433 não está bloqueada nesta rede; o perfil de T02 pode rodar daqui com `scripts/fabric_probe.py` ou `src/pipeline/fabric.py`. A ressalva anterior ("1433 bloqueada, timeout") não se confirmou hoje: se voltar a ocorrer em outra rede, as alternativas são VPN/outra rede, pedido de liberação ao TI ou execução dentro do Fabric via `scripts/fabric_deploy.py` sem `--aplicar`.
- **Testes:** `python -m pytest` com 24 testes passando (2026-10-27). A tarefa não tem código novo.
- **Publicação no Fabric:** o único workspace com acesso é `O&L Global - Prod - DA` (produção). Publicar cria 3 notebooks `als_*` e grava em `Files/als_oilmodel/` do `LakehouseOeL`. Decidir com o Caio se vai para lá ou para um workspace/lakehouse de desenvolvimento (`lh_forecast`).
- Confirmar com Diego/Keli a fórmula de março no Forecast 27 e se o status manual (os ~9% fora da regra) deve ser preservado.
