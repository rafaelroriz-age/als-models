# Dicionário de Dados — Projeto de Ciência de Dados

> Forecast de consumo de amostras e forecast de vendas.
> Fonte: `Dicionario_de_Dados_Projeto_Ciencia_de_Dados.xlsx` (convertido para Markdown).

## Para que serve

Registrar, em um só lugar, os campos que alimentam os dois KPIs do projeto: de onde vêm, o que significam e como se ligam entre as fontes. Serve de base para o cientista de dados e para a validação com os times.

## Como usar

1. Revisar cada campo nas abas **Fontes**, **Chaves** e **Dicionário de Campos**.
2. Preencher as colunas destacadas em amarelo (ex.: tabela/caminho no Fabric).
3. Ajustar a coluna **Status** conforme a validação (Confirmado / A validar / Em aberto).
4. Anotar correções na coluna **Observação**.

## Legenda de status

| Status | Significado |
|--------|-------------|
| Confirmado | regra/campo validado pelo time responsável |
| A validar | entendido a partir dos arquivos, aguardando confirmação |
| Em aberto | ponto que ainda precisa ser definido |

> Células em amarelo = preencher (aqui: coluna "Tabela/Local no Fabric").

---

## Fontes

| Sistema / Fonte | O que contém | Usado em | Acesso | Tabela/Local no Fabric | Status |
|-----------------|--------------|----------|--------|------------------------|--------|
| LIMS / S360 | Amostras processadas, equipamentos cadastrados e monitorados, compartimentos, setor e segmento do cliente | Consumo de amostras | Lakehouse Fabric | *(preencher)* | A validar |
| ERP / Proteus | Faturamento e vendas (via API em tempo real) | Forecast de vendas | Lakehouse Fabric | *(preencher)* | A validar |
| Zoho CRM | Segmentação de cliente, oportunidades e pedidos em aberto | Forecast de vendas (cross-check) | API Zoho | *(preencher)* | A validar |
| Calculadora de amostras (Bahia) | Amostras/ano por tipo de equipamento, horas e coleta por compartimento; conversão em faturamento | Consumo de amostras | Planilha (out/2022) | *(preencher)* | A validar |
| Customer Status 2026 | Base de clientes com venda, amostra, potencial e % atingido por cliente | Ambos | Planilha | *(preencher)* | A validar |
| Forecast (Keli/Diego) | Receita mensal estimada por componente e projeção por amostra | Forecast de vendas | Planilha | *(preencher)* | A validar |

## Chaves de Ligação

| Chave | Descrição | Liga quais fontes | Campo nos arquivos | Status | Observação |
|-------|-----------|-------------------|--------------------|--------|------------|
| Raiz CNPJ | Identificador do cliente (raiz do CNPJ) | LIMS/S360, ERP, Zoho, planilhas | Raiz CNPJ | A validar | |
| ERP ID | Código do cliente no ERP | ERP, Customer Status | ERP ID | A validar | |
| ID de equipamento (S360) | Identificador único do equipamento monitorado | LIMS/S360, Calculadora | (a confirmar) | A validar | |
| Vendedor (Sales Reps) | Responsável comercial pela carteira | ERP, Zoho, Customer Status | Sales Reps | A validar | |
| Setor (Sector) | Setor do cliente | LIMS/S360, Customer Status | Sector | A validar | |
| Segmento (Segment) | Segmento do cliente/equipamento | LIMS/S360, Calculadora, Customer Status | Segment | A validar | |

---

## Dicionário de Campos

Colunas: Campo · Descrição · Tipo · KPI/Área · Fonte · Origem · Tabela no Fabric · Chave? · Status · Observação.

### Cliente / dimensões

| Campo | Descrição | Tipo | Fonte | Origem | Chave? | Status | Observação |
|-------|-----------|------|-------|--------|--------|--------|------------|
| Cliente | Nome/razão social do cliente | Texto | LIMS/S360 · ERP | Customer Status · CLIENT | Não | A validar | |
| Raiz CNPJ | Raiz do CNPJ do cliente | Texto | ERP | Customer Status · Raiz CNPJ | Sim | A validar | |
| ERP ID | Código do cliente no ERP | Texto | ERP | Customer Status · ERP ID | Sim | A validar | |
| Vendedor | Responsável comercial | Texto | Zoho · ERP | Customer Status · Sales Reps | Não | A validar | |
| Cidade / UF | Localização do cliente | Texto | LIMS/S360 | Customer Status · CITY, UF | Não | A validar | |
| Setor | Setor do cliente | Categoria | LIMS/S360 | Customer Status · Sector | Não | A validar | |
| Segmento | Segmento do cliente/equipamento | Categoria | LIMS/S360 | Customer Status · Segment | Não | A validar | |
| Tipo de pagamento | Ex.: pré-pago, pós-pago | Categoria | ERP | Customer Status · Payment Type | Não | A validar | |
| Status real do cliente | Ativo, churn, reativado etc. | Categoria | Derivado | Customer Status · Real Status | Não | A validar | |

### Consumo de amostras

| Campo | Descrição | Tipo | Fonte | Origem | Chave? | Status | Observação |
|-------|-----------|------|-------|--------|--------|--------|------------|
| Amostras processadas (histórico) | Série histórica de amostras por cliente/equipamento | Número | LIMS/S360 | LIMS (lakehouse) | Não | A validar | Base de treino do modelo |
| Data da última amostra | Data da última amostra do cliente | Data | LIMS/S360 | Customer Status · Last Date Sample | Não | A validar | |
| Equipamentos cadastrados | Equipamentos do cliente no S360 | Número | LIMS/S360 | S360 (lakehouse) | Não | A validar | |
| Equipamentos monitorados | Equipamentos com amostra no período | Número | LIMS/S360 | Customer Status · Equipments Tested | Não | A validar | |
| Tipo de equipamento | Modelo/família do equipamento | Categoria | LIMS/S360 | Calculadora | Não | A validar | |
| Horas trabalhadas (horímetro) | Horas trabalhadas da máquina no período | Número | LIMS/S360 | Calculadora · Horas Trabalhadas | Não | A validar | Driver do consumo |
| Meses trabalhados/ano | Meses de operação por ano (sazonalidade) | Número | Derivado | Calculadora | Não | A validar | Varia por segmento |
| Compartimento (ponto de coleta) | Motor, hidráulico, transmissão etc. | Categoria | LIMS/S360 | Calculadora · Ponto de Coleta | Não | A validar | |
| Período de coleta | Intervalo de coleta por compartimento (h) | Número | Regra de manutenção | Calculadora · Período de Coleta | Não | A validar | Preventiva x meia preventiva |
| Total de coletas | Coletas previstas no período | Número | Derivado | Calculadora · Total de Coletas | Não | A validar | |
| Previsão real de amostras | Amostras/ano e /mês esperadas por consumo | Número | Derivado | Calculadora | Não | A validar | Saída da calculadora |
| Ticket médio por serviço | Valor médio por serviço/amostra | Moeda | Parâmetro | Calculadora | Não | A validar | Parâmetro de 2022 — revisar |
| Taxa de conversão em serviço | % de amostra que vira serviço faturado | Percentual | Parâmetro | Calculadora | Não | A validar | Parâmetro de 2022 — revisar |
| Potencial anual de amostras | Quanto o cliente poderia gerar (potencial) | Número | A definir | Customer Status · Annual Sample Potential | Não | Em aberto | Origem a confirmar: calculadora ou benchmark de similares |
| % atingido | Amostras realizadas / potencial anual | Percentual | Derivado | Customer Status · % Achieved | Não | A validar | |

### Forecast de vendas

| Campo | Descrição | Tipo | Fonte | Origem | Chave? | Status | Observação |
|-------|-----------|------|-------|--------|--------|--------|------------|
| Faturamento 12 meses | Faturamento do cliente nos últimos 12 meses | Moeda | ERP | Customer Status · Faturamento 12 meses | Não | A validar | |
| Data da última venda | Data da última compra do cliente | Data | ERP | Customer Status · Last Date Sales | Não | A validar | Usada na regra do recorrente |
| Flag cliente recorrente | Comprou em 6+ meses/12 e última compra < 90 dias | Booleano | Derivado | Forecast (regra) | Não | A validar | Sem a taxa de 70% |
| Receita recorrente estimada | Receita esperada dos clientes recorrentes | Moeda | Derivado | Forecast · Receita Recorrente | Não | A validar | |
| Receita não recorrente ativa | Clientes que compram poucas vezes | Moeda | Derivado | Forecast · Não Recorrente Ativa | Não | A validar | |
| Receita novos clientes | Valor médio do 1º faturamento | Moeda | Derivado | Forecast · Novos Clientes | Não | A validar | |
| Receita clientes reativados | Voltaram a comprar após +1 ano | Moeda | Derivado | Forecast · Reativados | Não | A validar | |
| Perda de receita (churn) | Receita perdida de quem parou de comprar | Moeda | Derivado | Forecast · Churn | Não | A validar | >6 meses sem comprar |
| Variável de mercado/cenário | Ajuste mensal por cenário e sazonalidade | Percentual | Manual/externo | Forecast · Variáveis de Mercado | Não | A validar | |
| Receita total estimada | Soma dos componentes antes do ajuste | Moeda | Derivado | Forecast · Receita Total | Não | A validar | |
| Novo total estimado | Total após variável de mercado | Moeda | Derivado | Forecast · Novo Total Estimado | Não | A validar | |
| Projeção por amostra processada | Receita estimada a partir das amostras | Moeda | Derivado | Forecast · Projeção por Amostra | Não | A validar | Base da correlação consumo→venda |
| Pedido pendente | Pedido em aberto (cross-check) | Booleano | ERP | ERP (lakehouse) | Não | A validar | Evita dupla contagem |
| Oportunidade aberta (Zoho) | Deal em aberto no CRM (cross-check) | Booleano | Zoho | Zoho CRM | Não | A validar | Evita dupla contagem |

---

## Pontos em aberto (do dicionário)

- **Tabela/Local no Fabric** de todas as fontes ainda não preenchida (células amarelas).
- **ID de equipamento (S360)** — campo exato do join a confirmar.
- **Potencial anual de amostras (Annual Sample Potential)** — status **Em aberto**: origem a confirmar (calculadora vs benchmark de similares).
- **Ticket médio** e **taxa de conversão** — parâmetros de 2022, revisar.
