# PROPOSTA COMERCIAL (ALTERNATIVA)
## Previsão de TAT & Volume — ALS Oil & Lubricants

**Preparada para:** ALS Oil & Lubricants
**Preparada por:** Consultor(a) Freelancer de Ciência de Dados
**Data:** Setembro de 2026
**Validade da proposta:** 30 dias a partir da data acima
**Início alternativo proposto:** 19 de outubro de 2026

---

## 1. Resumo executivo

Proposta para desenvolvimento de um **modelo de previsão autônomo** que, estando no meio de um período, prevê como esse período terminará para uma entidade escolhida — tanto o resultado de **TAT / % on-time** quanto o **volume de amostras** — atualizado sob demanda e exposto por um serviço que o agente da ALS consome. **A integração com o agente fica a cargo da ALS.**

O trabalho será conduzido em regime de **meio período**: **4 horas por dia**, durante **40 dias úteis** (com compensação dos feriados brasileiros), à taxa de **R$ 30,00/hora**, distribuído em **2 pagamentos de R$ 2.400,00**.

| Item | Valor |
|------|-------|
| Carga horária diária | 4 horas |
| Duração | 40 dias úteis (≈ 8 semanas) |
| Total de horas | 160 horas |
| Taxa horária | R$ 30,00 |
| **Investimento total** | **R$ 4.800,00** |
| **Forma de pagamento** | **2 parcelas de R$ 2.400,00** |

---

## 2. Escopo do projeto (resumo)

O cliente envia amostras de óleo que passam por três estágios: **CRD** (registro), **Laboratório** (testes) e **Interpretação** (revisão). O TAT corre continuamente (sem pausa em fins de semana/feriados) e re-testes não zeram o relógio. A meta de serviço é **≥ 90% on-time por mês**.

A entrega prevê dois alvos de previsão, por entidade e período flexíveis:

1. **Resultado de TAT / % on-time** — participação de amostras concluídas dentro da faixa de prazo, com sinalização de risco contra a meta de 90%.
2. **Volume de amostras** — número de amostras processadas no período.

**Entidades:** operação inteira, laboratório/local, pacote (plano de análise) ou grupo de trabalho.
**Períodos:** dia, semana, mês (referência principal) ou intervalo personalizado.

**Formato de entrega:** modelo Python autônomo exposto por um serviço (endpoint) com interface documentada, retornando um número claro + intervalo de incerteza. **A conexão ao agente existente é responsabilidade da ALS**, que recebe o serviço, a definição da interface e a documentação de integração.

---

## 3. Abordagem técnica (resumo)

| Preocupação | Escolha proposta |
|-------------|------------------|
| Acesso a dados | Direto ao LIMS S360 (camada prata) |
| Manipulação | Pandas, numpy |
| TAT censurado | Lifelines (Kaplan-Meier / Cox) ou modelo de sobrevivência |
| Previsão de volume | Statsforecast / prophet / gradient boosting |
| Incerteza | Predição conformal / intervalos de predição (calibrados) |
| Avaliação | Harness de backtesting customizado (sem vazamento de futuro) |
| Serviço | Direto na infraestrutura da ALS |
| Testes | Pytest / Great Expectations |

O tratamento de **amostras censuradas** (recebidas mas ainda não concluídas no meio do período) é central e será feito por análise de sobrevivência, não por descarte.

---

## 4. Condições do engajamento

- **Regime:** meio período — 4 horas/dia, em dias úteis.
- **Período:** 40 dias úteis, com os feriados brasileiros acrescentados ao calendário (o prazo se estende na mesma proporção).
- **Taxa:** R$ 30,00/hora. **Total: 160 h × R$ 30,00 = R$ 4.800,00.**
- **Pagamento:** **2 parcelas de R$ 2.400,00** (ver §6).
- **Integração:** a cargo da ALS — entregamos o serviço, a interface e a documentação; a ALS conecta ao agente.
- **Comunicação:** checkpoints curtos ao fim de cada milestone + canal de dúvidas assíncrono.

### Feriados brasileiros considerados no período

Partindo da data proposta de início (19/out/2026), os seguintes feriados nacionais caem em dia útil e são **compensados** no cronograma:

| Feriado | Data | Dia da semana |
|---------|------|----------------|
| Finados | 02/nov/2026 | segunda-feira |
| Dia da Consciência Negra | 20/nov/2026 | sexta-feira |

> Nota: a Proclamação da República (15/nov/2026) cai em domingo e não impacta o calendário de dias úteis.

### Janela do projeto

| Marco | Data |
|-------|------|
| Início proposto | 19 de outubro de 2026 (segunda) |
| Término previsto | 15 de dezembro de 2026 (terça) |
| Duração total de calendário | 58 dias corridos (40 úteis + 2 feriados + fins de semana) |

---

## 5. Cronograma (2 etapas × 20 dias úteis × 80 horas)

| Etapa | Foco | Dias úteis | Horas | Janela (datas) |
|-------|------|-----------|-------|----------------|
| **Etapa 1** | Fundamentação e dados — descoberta, features e backtesting | 20 | 80 h | 19/out → 16/nov |
| **Etapa 2** | Modelagem, serviço e entrega | 20 | 80 h | 17/nov → 15/dez |
| **Total** | | **40** | **160 h** | |

### Etapa 1 — Fundamentação e dados

| Fase | Descrição | Horas | Dias úteis |
|------|-----------|-------|-----------|
| Fase 0 — Descoberta e auditoria de dados | Engenharia reversa do esquema S360, ciclo de vida da amostra, derivação da faixa de prazo, relatório de qualidade | 28 h | 7 |
| Fase 1 — Engenharia de features e dataset | Tabelas-fato período×entidade×amostra, definição de volume, features de calendário/hierarquia/carga | 28 h | 7 |
| Fase 2 — Harness de backtesting | Simulação "dados disponíveis naquele momento", censura fiel, métricas (MAE/MAPE, erro % on-time, calibração, risco) | 24 h | 6 |

### Etapa 2 — Modelagem, serviço e entrega

| Fase | Descrição | Horas | Dias úteis |
|------|-----------|-------|-----------|
| Fase 3 — Modelagem, serviço e calibração | Baseline, modelo de volume, modelo TAT/on-time com censura, calibração dos intervalos, serviço na infraestrutura da ALS | 56 h | 14 |
| Fase 4 — Validação e entrega | Relatório de backtesting, validação da calibração, documentação, entrega | 24 h | 6 |

---

## 6. Milestones e pagamento

O projeto é entregue em **5 milestones**, agrupados em **2 etapas de faturamento**, cada uma de **R$ 2.400,00**. A integração final com o agente é executada pela ALS.

### Milestones por etapa

| # | Milestone | Entregável | Horas | Dias úteis | Janela (datas) | Etapa |
|---|-----------|------------|-------|-----------|----------------|-------|
| M1 | Descoberta & auditoria de dados | Mapa de dados S360 + relatório de qualidade + perguntas em aberto resolvidas | 28 h | 7 | 19/out → 27/out | Etapa 1 |
| M2 | Features & dataset | Tabelas-fato, conjunto de features e definição de volume aprovada | 28 h | 7 | 28/out → 06/nov | Etapa 1 |
| M3 | Harness de backtesting | Harness funcional + relatório de métricas de referência | 24 h | 6 | 09/nov → 16/nov | Etapa 1 |
| M4 | Modelagem, serviço & calibração | Modelos de volume e TAT/on-time com intervalos calibrados (vs. baseline) + serviço na infraestrutura da ALS com interface agente-modelo | 56 h | 14 | 17/nov → 07/dez | Etapa 2 |
| M5 | Validação & entrega | Relatório de backtesting contra os critérios de sucesso + validação da calibração + documentação + entrega | 24 h | 6 | 08/dez → 15/dez | Etapa 2 |
| | | | **160 h** | **40** | | |

### Plano de pagamento (2 parcelas)

| Parcela | Período | Milestones cobertos | Horas | Valor |
|---------|---------|---------------------|-------|-------|
| **Parcela 1** | Etapa 1 (19/out → 16/nov) | M1 + M2 + M3 | 80 h | **R$ 2.400,00** |
| **Parcela 2** | Etapa 2 (17/nov → 15/dez) | M4 + M5 | 80 h | **R$ 2.400,00** |
| | | | **160 h** | **R$ 4.800,00** |

**Condições de pagamento:**

- **Parcela 1 (R$ 2.400,00):** faturada ao fim da Etapa 1 (16/nov), mediante entrega e aceite dos milestones M1–M3.
- **Parcela 2 (R$ 2.400,00):** faturada ao fim da Etapa 2 (15/dez), mediante entrega e aceite dos milestones M4–M5.
- Vencimento em 7 dias corridos após a emissão de cada fatura.
- Valores em reais (BRL); impostos do profissional são de responsabilidade do próprio.

---

## 7. Premissas e riscos

**Premissas principais**

- Acesso ao S360 concedido no início, razoavelmente consultável.
- Dados históricos ≥ 12 meses (necessário para backtesting significativo).
- Atributos da faixa de prazo presentes ou deriváveis.
- Hierarquia de entidades relacionável às amostras sem esforço excessivo de limpeza.
- A ALS realiza a integração com o agente; entregamos um endpoint/interface documentados e simples de consumir.

**Riscos e mitigação**

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Descoberta de dados difícil (sem dicionário) | Prazo | Fase 0 dedicada e checkpoint cedo para reestimativa |
| Profundidade histórica insuficiente | Qualidade do backtest | Avaliação antecipada; métodos com menos dados (cross-val temporal) |
| Definição de "volume" ambígua | Retrabalho | Definir com o cliente já na M1/M2 |
| Interface agente-modelo muda de requisito | Escopo | Congelar o contrato da interface na M4; ajustes posteriores tratados à parte |

---

## 8. Fora de escopo

- **Integração com o agente existente (responsabilidade da ALS)** — entregamos serviço, interface e documentação.
- Treinamento de equipe ou suporte contínuo pós-entrega (pode ser contratado à parte).
- Infraestrutura de produção / hospedagem definitiva do serviço.
- Reformulação do LIMS S360 ou correção estrutural de dados de origem.
- Garantia de atingir a meta de 90% on-time (o entregável é a previsão com acurácia medida via backtesting).

---

## 9. Aceite

Aceito os termos desta proposta:

- Nome: ______________________________
- Assinatura: _________________________
- Data: ____/____/______

---

*Proposta preparada em setembro de 2026. Documento confidencial — ALS Oil & Lubricants.*
