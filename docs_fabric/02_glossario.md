# Glossário

| Termo | Significado |
|-------|-------------|
| Amostra | Coleta de óleo/fluido de um compartimento de um equipamento, enviada para análise. Unidade básica do consumo. |
| Análise de óleo | Teste realizado na amostra; sinônimo de ensaio. |
| Compartimento | Ponto de coleta do equipamento (motor, hidráulico, transmissão, arrefecimento, redução final). |
| Horímetro | Medidor de horas trabalhadas do equipamento — o driver principal do consumo. |
| Meses trabalhados/ano | Quantidade de meses que o equipamento opera por ano (varia por segmento/sazonalidade). |
| Coleta preventiva / meia preventiva | Intervalos de coleta em horas (ex.: 500h preventiva; 250h meia preventiva — que dobra a coleta). |
| Ticket médio | Valor médio por serviço (~R$ 1.950 em out/2022; a revisar). |
| Conversão em serviço | Taxa de amostras que viram serviço/faturamento (~5% em out/2022; a revisar). |
| Segmento / Setor | Classificação do cliente (ex.: cana, grãos/soja/milho, indústria, locomotiva) — define sazonalidade. |
| CNPJ (Raiz) | Identificador do cliente, usado como chave em todas as fontes. |
| ERP ID | Código do cliente no ERP (Proteus). |
| Consumo Real | Amostras esperadas pelo histórico/consumo do próprio cliente. |
| Consumo Potencial | Amostras que o cliente poderia gerar se monitorasse tudo (benchmark de similares). |
| % Achieved (atingido) | Equipamentos cadastrados × monitorados — grau de cobertura do monitoramento. |
| Annual Sample Potential | Campo do Customer Status com potencial anual de amostras por cliente (origem a confirmar). |
| Churn (perda de receita) | Cliente >6 meses sem comprar; desconta-se a média dos 6 meses anteriores. |
| Cliente recorrente | Comprou em ≥6 meses distintos nos últimos 12 e última compra <90 dias. |
| Cliente reativado | Voltou a comprar após +1 ano. |
| EBIT | Lucro antes de juros e impostos — referência do forecast de vendas (não só preço de venda). |
| Cross-check mensal | Retirar do estimado quem já faturou, tem pedido pendente ou oportunidade aberta no Zoho (evita dupla contagem). |
| S360 | LIMS do cliente; fonte de amostras/equipamentos. Integração só de envio, sem retorno. |
| Zoho CRM | CRM — segmentação, oportunidades e pedidos em aberto (usado no cross-check de vendas). |
| Proteus | ERP — faturamento e vendas (API em tempo real). |
| Microsoft Fabric | Plataforma unificada de dados/analytics (lakehouse, warehouse, Data Factory, Power BI) onde o projeto roda. |
| OneLake | Camada de armazenamento unificada do Fabric (arquivos/Delta). |
| Lakehouse | Combinação de lake (arquivos) + warehouse (SQL/Delta) em um único item do Fabric. |
| Espelhamento (Mirroring) | Replicação contínua de um banco (S360) para o Fabric com um clique — sem pipeline de cópia. |
| Medallion | Arquitetura bronze (bruto) → silver (limpo) → gold (agregado/pronto para consumo). |
| Modelo semântico | Camada de modelagem do Power BI/Fabric que expõe métricas (DirectLake sobre Delta). |
| DirectLake | Modo de conexão do Power BI que lê Delta/Parquet do OneLake sem importar. |
| MLflow | Ferramenta de rastreamento/registro de experimentos e modelos (nativa no Fabric). |
| FinOps | Gestão de custo em nuvem — aqui, usar a capacidade F8 com eficiência. |
