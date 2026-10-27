# Backlog executável — ALS OilModel

Cada tarefa é independente o bastante para virar **uma sessão (ou um agente em background)**. O bloco `Prompt` é copiável como está.
Visão geral e ordem automática: `python scripts/backlog.py list` e `python scripts/backlog.py next`.

## Como usar

| Quero | Comando / ação |
|---|---|
| Ver tudo e o que está liberado | `python scripts/backlog.py list` |
| Ver o próximo lote que pode rodar em paralelo | `python scripts/backlog.py next` (filtre com `--ambiente offline`) |
| Copiar o prompt de uma tarefa | `python scripts/backlog.py show T07` |
| Atualizar status | `python scripts/backlog.py set T07 done` (`todo`, `doing`, `done`, `blocked`) |
| Rodar o lote em background aqui no Code | Peça: "execute em background o lote offline do `backlog.py next`, um agente por tarefa, cada um em worktree isolado" |

**Campos:** `Depende` = tarefas que precisam estar `done`. `Ambiente` = `offline` (roda sem Fabric, seguro em background), `fabric` (precisa de acesso ao Fabric: API na 443 ou SQL endpoint na 1433; exige o login Azure em cache nesta máquina) ou `humano` (depende de decisão de pessoas; o Claude prepara o material e deixa rascunho, não envia). `Toca` = arquivos/pastas que a tarefa escreve; duas tarefas com `Toca` sobreposto não entram no mesmo lote.

## Regra de pronto (vale para toda tarefa)

1. Com código: `python -m pytest` verde, com testes novos para o que foi criado.
2. Registrar o resultado no doc indicado em `Doc` (fatos, números, caminhos). Sem opinião sem dado.
3. Em lote paralelo, **não editar `BACKLOG.md` nem os docs 06/12/13**: o status é atualizado com `backlog.py set` e o **Fechamento de lote** (abaixo) consolida.
4. Dados reais ficam em `data/` (fora do git). No Fabric: ler à vontade e gravar só em `Files/als_oilmodel/` e em notebooks `als_*`. **Nunca alterar dados que já existem** (tabelas, schemas, views): a barreira `scripts/fabric_guard.py` bloqueia isso nos hooks e no `fabric_deploy.py`; só uma pessoa libera, com `ALS_FABRIC_ESCRITA=1`.
5. Não reintroduzir TAT nem perguntas já resolvidas ([13](docs_fabric/13_revisao_alinhamento_reuniao_2026-10-21.md)).

## Fechamento de lote (Organizador)

Rodar depois que um lote terminar, antes do próximo:

```text
Atue como @organizador (AGENTS.md). Rode `git status` e `git log` para ver o que o último lote mudou. Para cada tarefa concluída: marque o item correspondente em docs_fabric/06_plano_execucao.md, atualize o status em docs_fabric/12_plano_trabalho_esboco.md, mova decisões, hipóteses e descobertas novas para docs_fabric/13_revisao_alinhamento_reuniao_2026-10-21.md (§1 a §3, e tire do §5 o que foi respondido), e inclua docs novos no docs_fabric/LEIA-ME.md. Confira se BACKLOG.md reflete os status reais (`python scripts/backlog.py list`). Não altere código.
```

---

## Bloco A — Acesso e Fase 0 (dados reais)

### T01 · Diagnosticar a conectividade com o SQL endpoint
- **Status:** done
- **Papel:** @engenheiro-software
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** baixa
- **Toca:** docs_fabric/14_fase0_engenharia_reversa_e_base_de_codigo.md
- **Doc:** docs_fabric/14_fase0_engenharia_reversa_e_base_de_codigo.md §4
- **Pronto:** 1433 e 443 testadas na rede atual, com caminho recomendado para rodar o perfil (outra rede/VPN, pedido ao TI ou execução dentro do Fabric).
- **Prompt:**
```text
Tarefa T01 do BACKLOG.md. Leia AGENTS.md, scripts/fabric_probe.py, src/pipeline/fabric.py e docs_fabric/14 §4. Teste a conectividade com o endpoint SQL do LakehouseOel nas portas 1433 e 443 (Test-NetConnection) e registre o resultado com data. Se a 1433 continuar bloqueada, liste as alternativas concretas (VPN/outra rede, pedido de liberação ao TI com o texto pronto, execução dos notebooks dentro do Fabric via scripts/fabric_deploy.py sem --aplicar) e recomende uma. Siga a "Regra de pronto" do BACKLOG.md.
```

### T02 · Rodar o perfil de qualidade das tabelas-chave
- **Status:** done
- **Papel:** @analista-dados
- **Depende:** T01
- **Ambiente:** fabric
- **Dificuldade:** media
- **Toca:** data/perfil, docs_fabric/08_dicionario_de_dados_discovery.md
- **Doc:** docs_fabric/08_dicionario_de_dados_discovery.md, docs_fabric/04_notas_dados.md
- **Pronto:** `data/perfil/` preenchido e achados resumidos (nulos, duplicatas, datas fora do intervalo, volume e período por tabela).
- **Prompt:**
```text
Tarefa T02 do BACKLOG.md. Leia AGENTS.md e docs_fabric/14 §3. Execute notebooks/00_validacao/01_perfil_qualidade.py com acesso ao Fabric (somente leitura): direto pelo SQL endpoint se a 1433 estiver liberada (T01) ou, se não, pelo executor de notebooks via API da T25 (conclua a T25 antes). Resuma em docs_fabric/08_dicionario_de_dados_discovery.md e docs_fabric/04_notas_dados.md: volume, período, nulos, duplicatas e outliers de horímetro por tabela-chave, e liste os achados que afetam KPI 1 e KPI 2. Rascunhe quais verificações viram gates G0/G1. Siga a "Regra de pronto" do BACKLOG.md.
```

### T03 · Validar as chaves entre fontes
- **Status:** done
- **Papel:** @analista-dados
- **Depende:** T02
- **Ambiente:** fabric
- **Dificuldade:** media
- **Toca:** docs_fabric/14_fase0_engenharia_reversa_e_base_de_codigo.md
- **Doc:** docs_fabric/14_fase0_engenharia_reversa_e_base_de_codigo.md §2
- **Pronto:** taxa de casamento medida para cada chave, com os casos que não casam quantificados.
- **Prompt:**
```text
Tarefa T03 do BACKLOG.md. Leia AGENTS.md e docs_fabric/14 §2. Com os dados reais (somente leitura), meça a taxa de casamento de: raiz CNPJ ↔ ERP ID (S360 ↔ Protheus), cliente ↔ equipamento ↔ compartimento ↔ amostra no S360, e cliente Zoho ↔ cliente S360. Informe os percentuais, os principais motivos de não casamento e o impacto em KPI 1 e 2. Atualize a tabela de chaves de docs_fabric/14 §2 trocando "a confirmar" pelo medido. Siga a "Regra de pronto" do BACKLOG.md.
```

### T04 · Preencher a matriz de cobertura dos insumos
- **Status:** done
- **Papel:** @analista-dados
- **Depende:** T02, T03
- **Ambiente:** fabric
- **Dificuldade:** media
- **Toca:** docs_fabric/15_matriz_cobertura.md
- **Doc:** docs_fabric/15_matriz_cobertura.md (novo)
- **Pronto:** nenhuma linha da matriz com ❓; lacunas com plano (derivar, pedir ao time de dados ou aceitar).
- **Prompt:**
```text
Tarefa T04 do BACKLOG.md. Leia AGENTS.md e a Etapa 1 de docs_fabric/12_plano_trabalho_esboco.md. Crie docs_fabric/15_matriz_cobertura.md com a matriz insumo × fonte da Etapa 1, cada linha com status (✅ existe, ⚠️ parcial, ❌ falta, ❓ não verificado), tabela/coluna real, granularidade, histórico e evidência numérica vinda do perfil (T02) e das chaves (T03). Para cada ⚠️ e ❌, proponha o plano: derivar, pedir ao time de dados ou aceitar a limitação. Siga a "Regra de pronto" do BACKLOG.md.
```

### T05 · Descobrir a origem do Annual Sample Potential e o status ativo do equipamento
- **Status:** done
- **Papel:** @especialista-dados
- **Depende:** T02
- **Ambiente:** fabric
- **Dificuldade:** alta
- **Toca:** docs_fabric/13_revisao_alinhamento_reuniao_2026-10-21.md
- **Doc:** docs_fabric/13_revisao_alinhamento_reuniao_2026-10-21.md §3
- **Pronto:** origem do potencial (RN-07) e critério de equipamento ativo definidos por dados, com exemplos numéricos.
- **Prompt:**
```text
Tarefa T05 do BACKLOG.md. Leia AGENTS.md, docs_fabric/13 §3, docs_fabric/10 (RN-07) e data/planilhas/engenharia_reversa.json. Com os dados reais, procure a origem do Annual Sample Potential (coluna no S360/Zoho, planilha Customer Status ou derivável de frota × intervalos) e defina por dados quando um equipamento é ativo (coluna de ativo, tempo desde a última coleta, vida útil por família). Entregue a regra proposta com 3 exemplos numéricos e a % de equipamentos cadastrados que ficam inativos. Registre em docs_fabric/13 §3. Siga a "Regra de pronto" do BACKLOG.md.
```

### T25 · Executor de notebooks no Fabric via API (sem depender da porta 1433)
- **Status:** done
- **Papel:** @engenheiro-software
- **Depende:** —
- **Ambiente:** fabric
- **Dificuldade:** alta
- **Toca:** scripts/fabric_run.py, tests/test_fabric_run.py, docs_fabric/09_conexao_e_consumo_fabric.md
- **Doc:** docs_fabric/09_conexao_e_consumo_fabric.md
- **Pronto:** `python scripts/fabric_run.py <notebook als_*>` publica (via fabric_deploy), executa o notebook no Fabric pela API (443), espera terminar e baixa as saídas de `Files/als_oilmodel/` para `data/`; reautenticação possível pelo celular (device code).
- **Prompt:**
```text
Tarefa T25 do BACKLOG.md. Leia AGENTS.md, scripts/fabric_deploy.py, scripts/fabric_guard.py e docs_fabric/09. Crie scripts/fabric_run.py: (1) executa um notebook `als_*` já publicado pela API de jobs do Fabric (POST /workspaces/{id}/items/{itemId}/jobs/instances?jobType=RunNotebook), acompanha o status pelo header Location até concluir e imprime o resultado; (2) baixa de Files/als_oilmodel/ no OneLake os arquivos de saída para data/; (3) recusa qualquer notebook que não comece com `als_` ou que a barreira fabric_guard bloqueie; (4) aceita ALS_AUTH=device para autenticar por device code (login pelo navegador do celular) além do login interativo em cache. Só leitura de dados existentes; escreva apenas em Files/als_oilmodel/. Teste com mocks de requests em tests/test_fabric_run.py. Valide a execução real somente com o notebook de perfil já publicado e documente o resultado e o tempo em docs_fabric/09. Siga a "Regra de pronto" do BACKLOG.md.
```

---

## Bloco B — Código que não depende de dados reais

### T06 · Testes e contrato de dados dos gates G0/G1
- **Status:** done
- **Papel:** @engenheiro-software
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** src/gates, tests/test_gates.py
- **Doc:** docs_fabric/10_estrutura_do_projeto.md
- **Pronto:** G0 (fontes) e G1 (tabela-base) com fixtures sintéticas cobrindo passa/falha de cada verificação.
- **Prompt:**
```text
Tarefa T06 do BACKLOG.md. Leia AGENTS.md, src/gates/checks.py e a seção de gateways em docs_fabric/10. Crie tests/test_gates.py com fixtures sintéticas pequenas: um DataFrame válido e, para cada verificação de G0 e G1, um caso que deve falhar. Acrescente em src/gates/checks.py o que faltar para as verificações listadas em docs_fabric/10 (nulos em chaves, duplicatas, datas fora do intervalo, cobertura de join), sem acessar o Fabric. Documente o contrato (colunas e regras) em docs_fabric/10. Siga a "Regra de pronto" do BACKLOG.md.
```

### T07 · Features de série temporal por entidade e mês
- **Status:** done
- **Papel:** @especialista-dados
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** src/features/series.py, tests/test_series.py
- **Doc:** docs_fabric/10_estrutura_do_projeto.md
- **Pronto:** função que recebe a tabela mensal e devolve lags 1/2/3/12, médias móveis, sazonalidade, segmento e status, com teste que prova ausência de vazamento.
- **Prompt:**
```text
Tarefa T07 do BACKLOG.md. Leia AGENTS.md, src/features/regras.py, src/models/baselines.py e a Etapa 4 de docs_fabric/12. Crie src/features/series.py: dada uma tabela mensal (entidade, mês, valor, segmento), gere lags 1/2/3/12, médias móveis 3 e 12, mês do ano (seno/cosseno), tendência curta e status do cliente reaproveitando src/features/regras.py. Todas as janelas devem usar só dados anteriores ao mês alvo. Crie tests/test_series.py com um teste de vazamento (alterar um valor futuro não pode mudar a feature do mês) e use dados sintéticos. Parametrize o que depende de RN ainda não aprovada. Siga a "Regra de pronto" do BACKLOG.md.
```

### T08 · Alertas de queda >20% e compartimento churn
- **Status:** done
- **Papel:** @especialista-dados
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** baixa
- **Toca:** src/features/alertas.py, tests/test_alertas.py
- **Doc:** docs_fabric/10_estrutura_do_projeto.md
- **Pronto:** alertas calculados com base de comparação parametrizável, testados em casos de borda.
- **Prompt:**
```text
Tarefa T08 do BACKLOG.md. Leia AGENTS.md, docs_fabric/10 (RN-05 e RN-06), docs_fabric/02_glossario.md e src/features/regras.py. Crie src/features/alertas.py com: (1) alerta de queda maior que 20% do consumo contra uma base de comparação configurável (mesmo mês do ano anterior, média móvel 3 ou 12 meses), e (2) compartimento churn pela regra do projeto. Crie tests/test_alertas.py com bordas (exatamente 20%, série curta, mês sem coleta). Registre em docs_fabric/10 que a base de comparação é decisão pendente com o negócio e qual o padrão adotado. Siga a "Regra de pronto" do BACKLOG.md.
```

### T09 · Classificação de clientes (Fase 1b) sobre o Customer Status
- **Status:** done
- **Papel:** @cientista-dados
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** src/features/classificacao.py, tests/test_classificacao.py, notebooks/10_preprocessamento/12_classificacao_clientes.py
- **Doc:** docs_fabric/13_revisao_alinhamento_reuniao_2026-10-21.md §3
- **Pronto:** protótipo classificando os 2.388 clientes em recorrente, não recorrente ativo e menor atividade, com a distribuição e a concordância com o status manual.
- **Prompt:**
```text
Tarefa T09 do BACKLOG.md. Leia AGENTS.md, a Fase 1b de docs_fabric/06, data/planilhas/customer_status.parquet e docs_fabric/14 §1. Prototipe a classificação de clientes antes da previsão: regra baseada em recorrência, faturamento, nº de máquinas e potencial (pirâmide) e, se agregar valor, uma árvore de decisão interpretável comparada com a regra. Crie src/features/classificacao.py, tests/test_classificacao.py e o notebook notebooks/10_preprocessamento/12_classificacao_clientes.py. Reporte a distribuição por classe e a concordância com o status manual (os ~9% fora da regra). Registre em docs_fabric/13 §3 como hipótese validada por dados parciais. Siga a "Regra de pronto" do BACKLOG.md.
```

### T10 · Modelos estatísticos plugáveis no harness
- **Status:** done
- **Papel:** @cientista-dados
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** src/models/estatisticos.py, tests/test_estatisticos.py, pyproject.toml
- **Doc:** docs_fabric/12_plano_trabalho_esboco.md (Etapa 3)
- **Pronto:** ETS, Theta e Croston/SBA/TSB funcionando com a mesma interface dos baselines, rodando no harness em série sintética.
- **Prompt:**
```text
Tarefa T10 do BACKLOG.md. Leia AGENTS.md, src/models/baselines.py, src/backtest/harness.py e a Etapa 3 de docs_fabric/12. Crie src/models/estatisticos.py com ETS, Theta e Croston/SBA/TSB (statsforecast ou statsmodels; adicione um extra opcional `stats` no pyproject.toml) com a mesma interface dos baselines para entrar no harness. Crie tests/test_estatisticos.py com séries sintéticas (sazonal, intermitente, curta) provando que rodam no rolling origin e que a série curta degrada para um fallback sem erro. Registre dependências e custo observado em docs_fabric/12 (Etapa 3). Siga a "Regra de pronto" do BACKLOG.md.
```

### T11 · Modelo ML global com quantis
- **Status:** done
- **Papel:** @cientista-dados
- **Depende:** T07
- **Ambiente:** offline
- **Dificuldade:** alta
- **Toca:** src/models/ml_global.py, tests/test_ml_global.py, pyproject.toml
- **Doc:** docs_fabric/12_plano_trabalho_esboco.md (Etapa 3)
- **Pronto:** LightGBM global gerando p10/p50/p90 com as features de T07, plugado no harness, sem vazamento.
- **Prompt:**
```text
Tarefa T11 do BACKLOG.md. Leia AGENTS.md, src/features/series.py (T07), src/backtest/harness.py e a Etapa 3 de docs_fabric/12. Crie src/models/ml_global.py: LightGBM global com regressão quantílica (p10, p50, p90) treinado em todas as séries, com a mesma interface dos baselines e treino estritamente anterior à origem do backtest. Adicione o extra opcional `ml` no pyproject.toml. Crie tests/test_ml_global.py em dados sintéticos verificando a ordem dos quantis, a cobertura do intervalo e a ausência de vazamento. Registre os hiperparâmetros iniciais e o custo em docs_fabric/12 (Etapa 3). Siga a "Regra de pronto" do BACKLOG.md.
```

### T12 · Snapshot mensal e reconstrução retroativa
- **Status:** done
- **Papel:** @engenheiro-software
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** src/backtest/snapshot.py, tests/test_snapshot.py
- **Doc:** docs_fabric/05_criterios_sucesso.md
- **Pronto:** snapshot do forecast por data de corte e reconstrução retroativa sobre histórico, com MAPE por mês/segmento/cliente.
- **Prompt:**
```text
Tarefa T12 do BACKLOG.md. Leia AGENTS.md, docs_fabric/05_criterios_sucesso.md e src/backtest/harness.py. Crie src/backtest/snapshot.py com: (1) gravação de snapshot mensal do forecast (data de corte, versão do modelo e dos dados), (2) reconstrução retroativa que reexecuta o modelo com os dados disponíveis em cada data de corte passada, e (3) MAPE/WAPE por mês, segmento e cliente, incluindo a convergência ao longo do mês. Crie tests/test_snapshot.py com dados sintéticos. Atualize docs_fabric/05 com o formato do snapshot. Siga a "Regra de pronto" do BACKLOG.md.
```

### T13 · Reconciliação hierárquica Cliente → Equipamento → Compartimento
- **Status:** done
- **Papel:** @cientista-dados
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** alta
- **Toca:** src/models/hierarquia.py, tests/test_hierarquia.py
- **Doc:** docs_fabric/12_plano_trabalho_esboco.md (Etapa 3)
- **Pronto:** bottom-up e top-down por proporções históricas, com teste de coerência (os níveis somam).
- **Prompt:**
```text
Tarefa T13 do BACKLOG.md. Leia AGENTS.md e a Etapa 3 de docs_fabric/12 (item hierárquicos). Crie src/models/hierarquia.py com reconciliação bottom-up e top-down por proporções históricas na hierarquia Cliente → Equipamento → Compartimento, agregável por tipo de equipamento, setor e segmento. Crie tests/test_hierarquia.py provando que os níveis somam exatamente e que a agregação por segmento bate com a soma dos clientes. Deixe MinT como extensão documentada, sem implementar. Siga a "Regra de pronto" do BACKLOG.md.
```

---

## Bloco C — Modelagem com dados reais

### T14 · Tabela-base por entidade e mês
- **Status:** done
- **Papel:** @engenheiro-software
- **Depende:** T03, T07
- **Ambiente:** fabric
- **Dificuldade:** alta
- **Toca:** notebooks/10_preprocessamento/10_base_amostras.py, docs_fabric/10_estrutura_do_projeto.md
- **Doc:** docs_fabric/10_estrutura_do_projeto.md
- **Pronto:** tabela mensal por entidade com amostras, faturamento e oportunidades, passando em G1; amostras avulsas identificadas e limpas.
- **Prompt:**
```text
Tarefa T14 do BACKLOG.md. Leia AGENTS.md, docs_fabric/14 §2–3, src/pipeline/fabric.py, src/features/series.py e src/gates/checks.py. Crie notebooks/10_preprocessamento/10_base_amostras.py: limpeza, join S360 × Protheus × Zoho (somente leitura), identificação e limpeza de amostras avulsas, e a tabela-base por entidade e mês, validada pelo gate G1. Salve a saída em data/ (fora do git) e registre cobertura de join e linhas descartadas em docs_fabric/10. Siga a "Regra de pronto" do BACKLOG.md.
```

### T15 · Backtest do KPI 1 com os candidatos em dados reais
- **Status:** done
- **Papel:** @cientista-dados
- **Depende:** T10, T11, T14
- **Ambiente:** fabric
- **Dificuldade:** alta
- **Toca:** notebooks/20_kpi1_consumo, docs_fabric/12_plano_trabalho_esboco.md
- **Doc:** docs_fabric/12_plano_trabalho_esboco.md (Etapa 3)
- **Pronto:** tabela modelo × nível × segmento (WAPE, viés, cobertura) comparando baselines, estatísticos e ML global.
- **Prompt:**
```text
Tarefa T15 do BACKLOG.md. Leia AGENTS.md, src/backtest/harness.py, notebooks/40_backtest/01_backtest_baselines.py e a tabela da T14. Crie notebooks em notebooks/20_kpi1_consumo que rodem no mesmo harness os baselines, os modelos de src/models/estatisticos.py e src/models/ml_global.py em rolling origin (horizontes 1, 3 e 6 meses), com resultados no MLflow. Entregue a tabela modelo × nível (cliente/equipamento/compartimento) × segmento com WAPE, viés e cobertura do intervalo, e diga quais candidatos batem os baselines (gate G3). Siga a "Regra de pronto" do BACKLOG.md.
```

### T16 · KPI 1 Potencial: benchmark por similares e % Achieved
- **Status:** done
- **Papel:** @cientista-dados
- **Depende:** T05, T14
- **Ambiente:** fabric
- **Dificuldade:** alta
- **Toca:** notebooks/20_kpi1_consumo/23_potencial.py, src/models/potencial.py, tests/test_potencial.py, docs_fabric/13_revisao_alinhamento_reuniao_2026-10-21.md
- **Doc:** docs_fabric/13_revisao_alinhamento_reuniao_2026-10-21.md §3
- **Pronto:** potencial por cliente via similares, com a definição de "similar" explícita e % Achieved calculado pela definição unificada (D6).
- **Prompt:**
```text
Tarefa T16 do BACKLOG.md. Leia AGENTS.md, docs_fabric/13 (D6 e §3), docs_fabric/02_glossario.md e o resultado da T05. Implemente src/models/potencial.py e o notebook notebooks/20_kpi1_consumo/23_potencial.py: potencial de amostras por cliente com benchmark de clientes similares (segmento, tipo e nº de equipamentos), e % Achieved pela definição unificada. Teste em tests/test_potencial.py. Reporte a distribuição do % Achieved por segmento e a sensibilidade à definição de "similar". Siga a "Regra de pronto" do BACKLOG.md.
```

### T17 · KPI 2: correlação consumo → venda e composição da receita
- **Status:** doing
- **Papel:** @cientista-dados
- **Depende:** T14
- **Ambiente:** fabric
- **Dificuldade:** alta
- **Toca:** notebooks/30_kpi2_vendas, src/features/receita.py, tests/test_receita.py, docs_fabric/13_revisao_alinhamento_reuniao_2026-10-21.md
- **Doc:** docs_fabric/13_revisao_alinhamento_reuniao_2026-10-21.md §2–3
- **Pronto:** receita por amostra (kit vs análise) medida, e a receita decomposta em recorrente, não recorrente ativa e churn, reproduzindo o Forecast 27 como baseline.
- **Prompt:**
```text
Tarefa T17 do BACKLOG.md. Leia AGENTS.md, docs_fabric/14 §1 (Forecast 27), docs_fabric/13 (D2, D3, H1 e H2) e a tabela da T14. Meça a correlação entre consumo de amostras e faturamento (receita por amostra; kit vs análise) e decomponha a receita em recorrente, não recorrente ativa e churn (novos e reativados fora do escopo). Reproduza o Forecast 27 como baseline em notebooks/30_kpi2_vendas, com funções reutilizáveis em src/features/receita.py e testes em tests/test_receita.py. Trate faturamento e EBIT como targets separados. Registre o resultado nas hipóteses H1/H2 de docs_fabric/13. Siga a "Regra de pronto" do BACKLOG.md.
```

### T18 · KPI 2: cross-check com Zoho sem dupla contagem
- **Status:** todo
- **Papel:** @especialista-dados
- **Depende:** T17
- **Ambiente:** fabric
- **Dificuldade:** media
- **Toca:** notebooks/30_kpi2_vendas/32_crosscheck_zoho.py, docs_fabric/13_revisao_alinhamento_reuniao_2026-10-21.md
- **Doc:** docs_fabric/13_revisao_alinhamento_reuniao_2026-10-21.md §2
- **Pronto:** comparação das oportunidades acima de 80% somadas versus descontadas do forecast, com o efeito em erro de previsão.
- **Prompt:**
```text
Tarefa T18 do BACKLOG.md. Leia AGENTS.md, docs_fabric/13 §2 (hipótese sobre oportunidades >80%) e a saída da T17. Crie notebooks/30_kpi2_vendas/32_crosscheck_zoho.py comparando, no histórico, as duas variantes: somar as oportunidades com probabilidade acima de 80% ao forecast, ou descontá-las para evitar dupla contagem. Meça o erro de cada variante e o risco de dupla contagem com o faturamento recorrente. Atualize a hipótese em docs_fabric/13 §2 com o resultado. Siga a "Regra de pronto" do BACKLOG.md.
```

### T19 · Documento de decisão de modelos
- **Status:** todo
- **Papel:** @cientista-dados
- **Depende:** T15, T17
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** docs_fabric/16_decisao_modelos.md
- **Doc:** docs_fabric/16_decisao_modelos.md (novo)
- **Pronto:** tabela modelo × critério e uma recomendação por problema (KPI 1 real, potencial, KPI 2, alertas), com experimentos seguintes priorizados.
- **Prompt:**
```text
Tarefa T19 do BACKLOG.md. Leia AGENTS.md, a Etapa 3 de docs_fabric/12 e os resultados das tarefas T15 e T17 (MLflow e docs). Crie docs_fabric/16_decisao_modelos.md com a tabela modelo × critério (acurácia por nível e segmento, calibração do intervalo, série curta/esparsa, explicabilidade, custo em CU, operação no Fabric), 2–3 candidatos escolhidos por problema além dos baselines, o protocolo de avaliação fechado e a lista priorizada de próximos experimentos. Só afirme o que os resultados sustentam. Siga a "Regra de pronto" do BACKLOG.md.
```

---

## Bloco D — Entrega

### T20 · Protótipo H1: dashboard HTML + SQL
- **Status:** doing
- **Papel:** @engenheiro-ia
- **Depende:** T15
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** src/serving, docs_fabric/07_integracao_mcp.md, docs_fabric/13_revisao_alinhamento_reuniao_2026-10-21.md
- **Doc:** docs_fabric/13_revisao_alinhamento_reuniao_2026-10-21.md §2 (H3)
- **Pronto:** HTML estático com forecast de consumo (Real e Potencial), alertas e filtros por segmento, mais as consultas SQL que o alimentam.
- **Prompt:**
```text
Tarefa T20 do BACKLOG.md. Leia AGENTS.md, docs_fabric/13 §2 (H3), docs_fabric/07 e o design do skill dataviz se for usar gráficos. Em src/serving, gere um dashboard HTML estático (um arquivo, sem backend) a partir de um CSV/parquet de forecast com colunas definidas por você e documentadas: consumo Real e Potencial por cliente/equipamento/segmento, intervalo p10/p90, alertas de queda e churn, filtro por segmento e período (semana/mês). Escreva também as consultas SQL (T-SQL) que produziriam essas tabelas no Fabric. Use dados da saída do T15 ou, se indisponível, dados sintéticos claramente marcados. Registre em docs_fabric/13 o que o protótipo mostra para a escolha do cliente. Siga a "Regra de pronto" do BACKLOG.md.
```

### T21 · Comparativo das opções de entrega
- **Status:** todo
- **Papel:** @gestor-projetos
- **Depende:** T20
- **Ambiente:** offline
- **Dificuldade:** baixa
- **Toca:** docs_fabric/13_revisao_alinhamento_reuniao_2026-10-21.md
- **Doc:** docs_fabric/13_revisao_alinhamento_reuniao_2026-10-21.md §2 (H3)
- **Pronto:** quadro HTML+SQL × modelo semântico × MCP/API com esforço, custo em CU, manutenção e aderência ao agente do CRM, para o cliente escolher.
- **Prompt:**
```text
Tarefa T21 do BACKLOG.md. Leia AGENTS.md, docs_fabric/07, docs_fabric/13 §2 (H3) e o protótipo da T20. Monte o quadro comparativo das três opções de entrega (dashboard HTML + SQL, modelo semântico, MCP/API) com esforço, custo em CU na F8, manutenção, latência e aderência ao objetivo de longo prazo (agente do CRM). Termine com uma recomendação e as perguntas objetivas para o cliente decidir. Registre em docs_fabric/13 §2 (H3). Siga a "Regra de pronto" do BACKLOG.md.
```

### T22 · FinOps: custo em CU por experimento
- **Status:** doing
- **Papel:** @engenheiro-software
- **Depende:** T15
- **Ambiente:** fabric
- **Dificuldade:** media
- **Toca:** docs_fabric/06_plano_execucao.md
- **Doc:** docs_fabric/06_plano_execucao.md (Fase 5)
- **Pronto:** custo em CU e tempo por modelo e por execução completa, com a janela estimada para agendar na F8.
- **Prompt:**
```text
Tarefa T22 do BACKLOG.md. Leia AGENTS.md e a Fase 5 de docs_fabric/06. Meça tempo e consumo de CU de cada modelo candidato do T15 e de uma execução completa do pipeline (use a métrica de capacidade do Fabric quando houver acesso, ou tempo × núcleos como proxy, dizendo qual). Entregue custo × acurácia por modelo e uma estimativa da janela de CU para agendamento na F8. Registre em docs_fabric/06 (Fase 5). Siga a "Regra de pronto" do BACKLOG.md.
```

---

## Bloco E — Decisões e comunicação

### T23 · Pauta de decisões para o time
- **Status:** done
- **Papel:** @gestor-projetos
- **Depende:** —
- **Ambiente:** humano
- **Dificuldade:** baixa
- **Toca:** docs_fabric/13_revisao_alinhamento_reuniao_2026-10-21.md
- **Doc:** docs_fabric/13_revisao_alinhamento_reuniao_2026-10-21.md §5
- **Pronto:** pauta de uma página com cada decisão, opções, recomendação e quem decide.
- **Prompt:**
```text
Tarefa T23 do BACKLOG.md. Leia AGENTS.md, docs_fabric/13 §5 e docs_fabric/14 §4. Redija para o time (Caio, Diego, Keli e demais) uma pauta de uma página com as decisões pendentes: meta numérica de MAPE por KPI e horizontes, cadência semanal obrigatória ou desejável, hierarquia matriz/filial do Zoho, janela de CU na F8, fórmula de março no Forecast 27 e preservação do status manual (~9%), e destino da publicação (produção ou workspace de desenvolvimento). Para cada uma: contexto em duas linhas, opções, recomendação e quem decide. Não invente respostas. Salve a pauta em docs_fabric/ e, se o conector do Outlook estiver disponível, crie um rascunho de e-mail para o time (nunca envie). Siga a "Regra de pronto" do BACKLOG.md.
```

### T24 · Regerar a apresentação executiva com o escopo atual
- **Status:** done
- **Papel:** @organizador
- **Depende:** T23
- **Ambiente:** offline
- **Dificuldade:** baixa
- **Toca:** docs_fabric/Apresentacao_Executiva_Forecast_Amostras_Vendas_Fabric-v2.md
- **Doc:** docs_fabric/13_revisao_alinhamento_reuniao_2026-10-21.md §4
- **Pronto:** apresentação em markdown sem os pontos desatualizados (6 componentes, EBIT único, % Achieved antigo, entrega via semântico + MCP).
- **Prompt:**
```text
Tarefa T24 do BACKLOG.md. Leia AGENTS.md, docs_fabric/13 (§1 a §4) e a apresentação docs_fabric/Apresentacao_Executiva_Forecast_Amostras_Vendas_Fabric-v2.md. Reescreva o markdown da apresentação com o escopo atual: KPI 1 (Real e Potencial) e KPI 2 derivado do consumo, faturamento e EBIT como targets separados, novos e reativados fora do escopo, % Achieved unificado, entrega por protótipos (H3) e as decisões já tomadas. Não mexa no .pptx nem no .pdf (anote em docs_fabric/13 §4 que continuam na versão anterior até regerar). Siga a "Regra de pronto" do BACKLOG.md.
```
