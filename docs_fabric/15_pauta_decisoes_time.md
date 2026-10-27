# Pauta de decisões pendentes: forecast de amostras e vendas

> Para: Caio, Diego, Keli e demais do time. Origem: T23 do [BACKLOG](../BACKLOG.md) e §5 do [13](13_revisao_alinhamento_reuniao_2026-10-21.md) (pontos sem resposta) e §4 do [14](14_fase0_engenharia_reversa_e_base_de_codigo.md) (pendências).
> Regra: nada aqui é resposta. "Recomendação" é a proposta da equipe técnica para discussão; a decisão é de quem está indicado em "Quem decide".

## 1. Meta de MAPE por KPI e horizontes

- **Contexto:** a reunião de 21/10 não fixou meta numérica de acurácia. As hipóteses serão comparadas por backtest, mas não há critério de aprovação.
- **Opções:**
  - (a) Meta única para os dois KPIs.
  - (b) Meta por KPI (KPI 1 consumo de amostras; KPI 2 vendas/faturamento) e por horizonte (ex.: 1, 3 e 6 meses).
  - (c) Definir a meta depois do primeiro backtest de referência (réplica do Forecast 27 e baselines).
- **Recomendação:** (b) com valor provisório pelo backtest de referência, ratificado pelo time. Sem meta, não há critério para escolher o modelo.
- **Quem decide:** Caio (cliente). Insumo: @cientista-dados.

## 2. Cadência semanal: obrigatória ou desejável?

- **Contexto:** a pergunta "semanal é requisito ou desejável?" segue aberta. A cadência define o custo de execução na F8.
- **Opções:**
  - (a) Semanal obrigatória.
  - (b) Semanal desejável, com fechamento mensal obrigatório.
  - (c) Mensal apenas, sem semanal.
- **Recomendação:** (b) no MVP. Reavaliar (a) quando o custo de CU por execução estiver medido.
- **Quem decide:** Caio.

## 3. Hierarquia matriz/filial do Zoho

- **Contexto:** o caso de referência são grupos com várias usinas (ex.: 8 usinas de um grupo). A tabela Zoho `accounts` traz `cnpj`, `id_protheus` e `erp_id` (ponte Zoho ↔ Protheus), mas não há confirmação de que a matriz/filial esteja modelada.
- **Opções:**
  - (a) Agrupar pelo CNPJ raiz (8 primeiros dígitos), se o dado confirmar.
  - (b) Agrupar por cadastro manual de grupos.
  - (c) Não agrupar: cada conta é uma unidade de previsão.
- **Recomendação:** (a) se o perfil de dados (T03) confirmar que o CNPJ raiz casa com os grupos. Caso contrário, (c) no MVP.
- **Quem decide:** Diego e Keli confirmam se o dado existe; Caio decide a regra de agrupamento.

## 4. Janela de CU na capacidade F8

- **Contexto:** a meta de custo é medida em CU na F8, e a janela define quando os pipelines rodam. A janela livre ainda não foi informada.
- **Opções:**
  - (a) Janela noturna fixa.
  - (b) Janela fixa em horário de baixo uso da capacidade, definida pela administração da F8.
  - (c) Execução sob demanda, sem janela.
- **Recomendação:** (a), depois de medir o CU real de uma execução de referência. Hoje não há medição.
- **Quem decide:** Caio, com quem administra a capacidade F8 (a confirmar).

## 5. Fórmula de março no Forecast 27

- **Contexto:** a réplica em Python reproduz a planilha de setembro a fevereiro ao centavo. Em março, a célula `C8 = B8 + E5/2 + F5/2 + E2/2` soma ½ dos novos de setembro: +R$ 100 mil no recorrente e +R$ 92 mil no total. Parece erro de fórmula, mas não foi confirmado.
- **Opções:**
  - (a) Replicar a planilha como está, para comparar com o histórico.
  - (b) Corrigir a fórmula, excluindo o termo de setembro.
  - (c) Replicar como referência, documentando a divergência, até a confirmação.
- **Recomendação:** (c). Não corrigir a regra por suposição; a comparação com o baseline fica registrada.
- **Quem decide:** Diego e Keli (regra de negócio). Caio, para o baseline.

## 6. Preservação do status manual (~9%)

- **Contexto:** cerca de 9% dos clientes ficam fora da regra do Forecast 27 por ajuste manual de status. Não está decidido se esse ajuste entra no modelo.
- **Opções:**
  - (a) Preservar como camada separada, com flag, para comparar com a regra pura.
  - (b) Preservar como override fixo na previsão.
  - (c) Descartar e usar só a regra.
- **Recomendação:** (a). Permite medir o efeito do ajuste manual no backtest sem contaminar a regra.
- **Quem decide:** Diego e Keli.

## 7. Destino da publicação: produção ou desenvolvimento

- **Contexto:** o único workspace com acesso é `O&L Global - Prod - DA` (produção). Publicar cria 3 notebooks `als_*` e grava em `Files/als_oilmodel/` do `LakehouseOel`. Também há bloqueio da porta 1433 na rede atual (ver [14](14_fase0_engenharia_reversa_e_base_de_codigo.md) §4).
- **Opções:**
  - (a) Publicar direto em produção.
  - (b) Desenvolver e validar em workspace/lakehouse de desenvolvimento (`lh_forecast`) e só depois promover.
  - (c) Rodar os notebooks dentro do Fabric sem publicar (`scripts/fabric_deploy.py` sem `--aplicar`).
- **Recomendação:** (b), com (c) para os testes enquanto a 1433 estiver bloqueada. Nenhuma publicação em produção sem confirmação explícita.
- **Quem decide:** Caio.

## Resumo para decisão

| # | Tema | Quem decide | Bloqueia |
|---|---|---|---|
| 1 | Meta MAPE e horizontes | Caio | Backtest e escolha de modelo |
| 2 | Cadência semanal | Caio | Custo de CU (F8) |
| 3 | Hierarquia Zoho | Diego/Keli + Caio | Agrupamento de clientes |
| 4 | Janela de CU na F8 | Caio + admin da F8 | Agendamento de pipelines |
| 5 | Fórmula de março | Diego/Keli | Baseline do Forecast 27 |
| 6 | Status manual (~9%) | Diego/Keli | Regra final de receita |
| 7 | Destino da publicação | Caio | Qualquer publicação no Fabric |
