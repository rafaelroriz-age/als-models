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

## 2. Chaves entre fontes (a confirmar no perfil de dados)
| Fonte | Campo | Observação |
|---|---|---|
| Protheus `notassaida` | `cod_cliente` + `loja` | = ERP ID do Customer Status |
| Zoho `accounts` | `erp_id`, `id_protheus`, `cnpj` | ponte Zoho ↔ Protheus |
| S360 `cliente` | `codigo_legado`, `id_cigam`, `sam_id` | **sem CNPJ**; candidato a ERP ID: `codigo_legado` |
| S360 `equipamento` | `familia_equipamento_id` | **sem `cliente_id`**: o vínculo com o cliente sai de amostra → compartimento → equipamento; não há tabela de nome da família |

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
| `notebooks/00_validacao/02_engenharia_reversa_planilhas.py` | Gera os números desta página |
| `notebooks/40_backtest/01_backtest_baselines.py` | Backtest dos baselines nos KPIs 1 e 2 (total e por cliente) |
| `scripts/fabric_deploy.py` | Wheel + notebooks `.ipynb`; com `--aplicar`, publica no workspace |
| `tests/` | 24 testes, incluindo os casos de borda de 6 meses e 90 dias e as réplicas das planilhas |

Execução local: `python -m pytest`, depois `python notebooks/00_validacao/02_engenharia_reversa_planilhas.py`. O perfil exige a porta 1433 liberada. Extrações de dados vão para `data/`, que fica fora do git.

## 4. Bloqueios e pendências
- **Porta 1433 bloqueada na rede atual.** O DNS resolve e a 443 abre, mas o SQL endpoint dá timeout. O perfil roda de outra rede/VPN ou dentro do Fabric.
- **Publicação no Fabric:** o único workspace com acesso é `O&L Global - Prod - DA` (produção). Publicar cria 3 notebooks `als_*` e grava em `Files/als_oilmodel/` do `LakehouseOeL`. Decidir com o Caio se vai para lá ou para um workspace/lakehouse de desenvolvimento (`lh_forecast`).
- Confirmar com Diego/Keli a fórmula de março no Forecast 27 e se o status manual (os ~9% fora da regra) deve ser preservado.
