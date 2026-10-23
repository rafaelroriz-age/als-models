# Documentação Técnica — Projeto de Ciência de Dados (Forecast de Amostras e Vendas)

> Fonte: PDF original · Oct 16, 2026 · @Icaro Guerra
> Conversão fiel do documento para Markdown.

## Objetivo e escopo

O projeto entrega previsibilidade para a área comercial a partir dos dados da LS. Nesta primeira fase, o escopo são dois KPIs, nesta ordem de dependência:

1. **Forecast de consumo de amostras** — prever quantas amostras cada cliente/equipamento vai gerar.
2. **Forecast de vendas** — prever o faturamento, derivado do consumo.

Outros temas (hub de notícias/mercado por setor, camada de segmentação de informação estratégica) ficam para fases seguintes.

**Entregável esperado:** um modelo consumível pelo ambiente (modelo semântico no Fabric ou API/endpoint), não um notebook — notebook é só para testes. A forma final de entrega faz parte da investigação.

## Contexto de negócio

Consumo puxa a venda. O pedido de compra do cliente é gerado pelo consumo do equipamento (horas trabalhadas → necessidade de coleta de óleo). Historicamente a LS projetava pela compra; a direção quer projetar pelo consumo.

- **Predict revenue.** O forecast de vendas deve ser atualizado idealmente por semana, não só por mês, e mira o EBIT, não apenas o preço de venda.
- **Limitação-chave:** a integração com o cliente (S360) é só de envio, sem retorno. Não há feedback automático se a máquina foi vendida, parou ou mudou de área — a previsão terá que inferir pelo próprio histórico do equipamento.
- **Volume:** a LS processa ~5 milhões de amostras/ano; a base de amostras no Power BI começa em 2022, o que torna cálculos ao vivo pesados — um motivo para mover a inteligência para o modelo/pipeline.

---

## KPI 1 — Forecast de consumo de amostras

**Definição.** Prever o volume de amostras (análises de óleo) que cada cliente vai gerar em um período, com base no consumo dos equipamentos. Duas visões:

- **Real** — o esperado pelo histórico/consumo do próprio cliente.
- **Potencial** — o que o cliente poderia gerar se monitorasse tudo (oportunidade comercial).

### Lógica da previsão real

Vem do plano de manutenção, por tipo de equipamento e segmento:

- **Driver:** horas trabalhadas (horímetro) e meses trabalhados/ano.
- **Coleta por compartimento** (motor, hidráulico, transmissão, arrefecimento, redução final), em intervalos de horas (ex.: motor 250h, hidráulico/transmissão 500h, arrefecimento 1000h).
- **Preventiva (ex.: 500h) x meia preventiva (ex.: 250h):** a meia preventiva dobra a coleta e é o que a LS sugere para ganhar amostras.

**Saída:** amostras/ano e amostras/mês por equipamento; convertida em faturamento via ticket médio por serviço e taxa de conversão em serviço.

### Potencial

Compara equipamentos cadastrados x monitorados (% atingido) e usa benchmark de clientes semelhantes (mesmo tipo de equipamento, mesmo segmento, monitoramento mais ativo). Ex.: cliente faz 200 amostras/mês, similares fazem 400 → potencial 400.

**Granularidade:** cliente → equipamento → compartimento, agregável por tipo de equipamento, setor e segmento.

**Sinais de ação:** queda >20% nas amostras do cliente; compartimento que deixou de ser coletado ("compartimento churn").

### Sazonalidade

Meses trabalhados/ano variam por segmento:

- Cana para nov–mar.
- Mato Grosso tem múltiplas sazonalidades (algodão/Cotton Picker ~500h/ano, milho safra+safrinha, soja).
- Indústria coleta por tempo (mensal/bimestral).
- Locomotiva semanal.

**Parâmetros atuais (a revisar):** ticket médio ≈ R$ 1.950 por serviço e conversão em serviço ≈ 5% — ambos de out/2022.

---

## KPI 2 — Forecast de vendas

**Definição.** Previsibilidade de faturamento (predict revenue), idealmente semanal, mirando o EBIT. Derivado do consumo.

### Composição (planilha Forecast)

A receita mensal estimada é a soma dos componentes, com ajuste e cross-check:

| Componente | Lógica | Efeito |
|-----------|--------|--------|
| Receita recorrente | clientes com padrão regular de compra | + |
| Receita não recorrente ativa | compram poucas vezes, volume alto | + |
| Receita novos clientes | valor médio do 1º faturamento | + |
| Receita reativados | voltaram a comprar após +1 ano | + |
| Perda de receita (churn) | >6 meses sem comprar; média dos 6 meses anteriores | − |
| Variável de mercado/cenário | ajuste mensal por sazonalidade/cenário | ± |

- **Cross-check mensal:** antes do total, retira do estimado quem já faturou no mês, tem pedido pendente ou oportunidade aberta no Zoho (evita dupla contagem).
- **Regra do cliente recorrente:** comprou em ≥6 meses distintos nos últimos 12 e última compra <90 dias. A taxa de conversão de 70% que existia foi removida (a base já é venda faturada, não orçamento). Inclui média ponderada, tendência e sazonalidade por cliente.
- **Projeção por amostra processada:** a planilha já traz, em paralelo, uma projeção de vendas baseada nas amostras — é a correlação consumo→venda que o modelo deve estudar e quantificar.

---

## Fontes de dados e chaves de ligação

Acesso via **lakehouse no Microsoft Fabric**. O espelhamento do LIMS/S360 é simples (botão no próprio Fabric); faturamento (ERP/Proteus) e vendas já estão disponíveis.

| Fonte | Conteúdo | Usado em |
|-------|----------|----------|
| LIMS / S360 | amostras processadas, equipamentos cadastrados/monitorados, compartimentos, setor, segmento | Consumo |
| ERP / Proteus | faturamento e vendas (API em tempo real) | Vendas |
| Zoho CRM | segmentação, oportunidades, pedidos em aberto | Vendas (cross-check) |

**Chaves de ligação entre as fontes:**

| Chave | Liga | Observação |
|-------|------|------------|
| Raiz CNPJ | todas as fontes | identificador do cliente |
| ERP ID | ERP ↔ base de clientes | código do cliente no ERP |
| ID de equipamento (S360) | S360 ↔ calculadora | campo exato a confirmar |
| Setor / Segmento | dimensões comuns | agregação |

> Dicionário de campos completo (campo a campo, com tipo, origem e status) está no arquivo "Dicionário de Dados", entregue à parte.

---

## Arquivos existentes e sua estrutura

Três planilhas já carregam a lógica de negócio e servem de ponto de partida — não começar do zero.

| Arquivo | O que faz | Campos principais |
|---------|-----------|-------------------|
| Calculadora de amostras (Bahia, out/2022) | amostras/ano por tipo de equipamento | segmento, tipo de equipamento, horas trabalhadas, meses/ano, ponto de coleta, período de coleta, total de coletas, amostras/ano e /mês, ticket médio, conversão |
| Customer Status 2026 | base de clientes (2.388; 1.479 ativos; 233 recorrentes), um por linha | Raiz CNPJ, ERP ID, Sales Reps, Sector, Segment, Last Date Sales/Sample, vendas e amostras por período, Annual Sample Potential, % Achieved, equipamentos testados, Faturamento 12 meses |
| Forecast (Keli/Diego) | receita mensal estimada por componente | Receita Recorrente, Não Recorrente Ativa, Novos, Reativados, Churn, Receita Total, Variáveis de Mercado, Novo Total, Projeção por Amostra |

> O Customer Status é onde venda × amostra × equipamento × potencial já se cruzam por cliente. O campo **Annual Sample Potential** aparece como valor colado (sem fórmula) — ver pontos em aberto.

---

## Pontos em aberto e a validar

A maioria das demais métricas já está documentada nos arquivos; na reunião são confirmações, não lacunas.

| Ponto | Situação | Responsável |
|-------|----------|-------------|
| Origem do Annual Sample Potential | valor colado no Customer Status, sem fórmula; confirmar se vem da calculadora ou do benchmark de clientes similares | Bahia / Keli |
| Parâmetros da calculadora | ticket médio e conversão de out/2022; atualizar | Bahia |
| Acurácia histórica | nunca medida retroativamente (previsto x realizado) | time + cientista |

---

## Acurácia e validação do modelo

Hoje não há medição de assertividade. Proposta:

- **Snapshot mensal:** congelar o forecast previsto a cada mês e comparar com o faturamento/consumo realizado.
- **Reconstrução retroativa:** aplicar a regra atual "como se fosse" cada mês passado sobre o histórico do Fabric e comparar com o realizado, para já ter uma linha de base.
- **Métricas de erro:** erro percentual (ex.: MAPE) por mês, por segmento e por cliente; acompanhar a convergência ao longo do mês (a planilha atual converge perto do dia 20).
- **Validação de dados:** great expectations / pytest nos notebooks, como parte da metodologia.

---

## Considerações técnicas e de abordagem

- **Postura:** medir todas as métricas que os times usam (carregam o conhecimento do negócio), validar se são as mais adequadas para acurácia e propor abordagens alternativas quando houver ganho — sempre validadas antes de entrar no modelo.
- **Dados brutos x agregados:** as planilhas têm agregados; o modelo precisa do histórico cru de amostras (LIMS) e do detalhe de equipamento/horímetro (S360) para treinar.
- **Custo computacional / FinOps:** o ambiente roda em capacidade Fabric (hoje F8) e o agente já consome boa parte dos recursos. Preferir modelos de menor custo (ML clássico quando resolver), mensurar custo × acurácia e comparar modelos. Pré e pós-processamento podem usar LLM de menor custo quando necessário.
- **Entrega:** provavelmente um modelo semântico no Fabric ou uma API/endpoint; notebook só para testes. Espera-se pipeline própria com pré e pós-processamento; joins no pré-processamento (SQL) para unir faturamento e amostras.
- **Flexibilidade:** o time dá autonomia de metodologia e ferramentas, pedindo transparência sobre o que é usado e por quê.

---

## Checklist para a reunião de validação

Antes da reunião, revisar os três arquivos e o dicionário de dados. Perguntas a levar:

1. Annual Sample Potential: vem da calculadora ou do benchmark de clientes similares? Quais parâmetros?
2. Calculadora: ticket médio e conversão atuais (vs. R$ 1.950 / 5% de 2022)?
3. Regra do recorrente confirmada (6+ meses/12, <90 dias, sem a taxa de 70%)?
4. Composição do forecast de vendas continua a mesma?
5. Como mediremos acurácia — existe histórico de forecasts salvos?
6. Acesso ao lakehouse (LIMS/S360, ERP, Zoho) liberado? Quais schemas/tabelas?
7. Chave de equipamento (S360) para o join — qual campo?
8. Sazonalidade por segmento: há curva/dados além do "meses trabalhados/ano"?

---

*Confidencial.*
