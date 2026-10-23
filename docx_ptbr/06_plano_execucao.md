# Plano de Execução

> Abordagem proposta, ferramentas e estimativa de esforço para o engajamento de Previsão de TAT & Volume da ALS.

## Abordagem proposta (resumo)

Um **modelo de previsão com duas saídas** por trás de uma fina camada de serviço:

1. **Volume** — previsão de série temporal (amostras por período) por entidade, com variáveis de calendário.
2. **TAT / % on-time** — modelo de tempo de conclusão com tratamento explícito de censura (estilo sobrevivência), agregado ao % on-time por período, mais uma sinalização de risco contra a meta de 90%.

Ambos embrulhados com **intervalos de incerteza**, validados por **backtesting** e expostos por meio de um **serviço Python** que o agente pode chamar.

## Ferramentas / bibliotecas propostas

| Preocupação | Escolha | Por quê |
|-------------|---------|---------|
| Acesso a dados | SQLAlchemy / driver direto para o S360 | puxar dados sob demanda |
| Manipulação de dados | pandas, numpy | padrão |
| TAT censurado | `lifelines` (Kaplan-Meier / Cox) ou modelo de sobrevivência explícito | trata amostras em andamento corretamente |
| Previsão de volume | `statsforecast` / `prophet` / gradient boosting | robusto, incerteza embutida |
| Incerteza | predição conformal ou intervalos de predição | intervalos calibrados (critério de sucesso declarado) |
| Avaliação | harness de backtesting customizado | simula "dados disponíveis naquele momento" |
| Serviço | FastAPI | o agente pode chamar um endpoint limpo |
| Testes | pytest | segurança contra regressões |

## Fases e tarefas do trabalho

### Fase 0 — Descoberta e auditoria de dados (primeiro, antes de se comprometer)
- Explorar o esquema do S360; fazer engenharia reversa das tabelas.
- Confirmar o ciclo de vida da amostra, os timestamps, a derivação da faixa de prazo e as junções da hierarquia.
- Construir relatório de qualidade dos dados (ausências, outliers, sanidade dos timestamps).
- **Saída:** mapa de dados + perguntas em aberto resolvidas.

### Fase 1 — Engenharia de features e de dataset
- Construir as tabelas-fato "período x entidade x amostra".
- Definir o alvo de volume (recebidas vs concluídas) com o cliente.
- Engenheirar features: calendário, hierarquia de entidade, contagem de re-testes, indicadores de carga de trabalho.

### Fase 2 — Harness de backtesting (construir antes dos modelos)
- Reproduzir a censura fielmente em cada ponto de referência (as-of).
- Sem vazamento de informação futura.
- Métricas: MAE/MAPE (volume), erro no % on-time, precisão/revocação de risco, calibração.

### Fase 3 — Modelagem
- Baseline: ingênuo (volume do último período; % on-time corrente) para superar.
- Modelo de volume com incerteza.
- Modelo de TAT/on-time com tratamento de censura.
- Calibrar os intervalos de confiança.

### Fase 4 — Serviço e integração
- Endpoint FastAPI: (entidade, data de referência, período-alvo) → previsão + intervalo.
- Saída simples e legível por humanos.
- Definir a interface agente-modelo em conjunto com o cliente.

### Fase 5 — Validação e entrega
- Relatório de backtesting contra os critérios de sucesso.
- Documentação das premissas e limitações.
- Entrega para integração com o agente.

## Estimativa de esforço (premissas)

| Fase | Estimativa |
|------|-----------|
| Fase 0 — Descoberta e auditoria de dados | 2–3 dias |
| Fase 1 — Engenharia de features | 2–3 dias |
| Fase 2 — Harness de backtesting | 2–3 dias |
| Fase 3 — Modelagem + calibração | 4–6 dias |
| Fase 4 — Serviço e integração | 2–3 dias |
| Fase 5 — Validação e entrega | 1–2 dias |
| **Total** | **~13–20 dias úteis** |

**Premissas principais:**
- O acesso aos dados do S360 é concedido cedo e é razoavelmente consultável.
- Os dados históricos abrangem ≥ 12 meses (necessário para backtesting significativo).
- Os atributos da faixa de prazo estão presentes ou são deriváveis.
- A hierarquia de entidades é relacionável às amostras sem grande esforço de limpeza.
- O ponto de integração com o agente é uma simples API de requisição/resposta.

> O esforço aumenta se a descoberta de dados for difícil, a profundidade histórica for pequena ou a integração exigir mais do que um endpoint simples.

## Perguntas em aberto para o cliente

1. Definição exata de "volume" (recebidas vs concluídas)?
2. Quais timestamps existem no S360 para cada estágio + re-testes?
3. Como a faixa de prazo é armazenada/derivada?
4. Profundidade histórica disponível para backtesting?
5. Como é a interface agente-modelo hoje (HTTP síncrono, fila de mensagens)?
6. Ambiente de implantação preferido para o serviço durante a entrega?
