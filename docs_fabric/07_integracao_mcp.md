# Integração via MCP (Model Context Protocol)

> Como conectar o "agente" da ALS ao modelo entregue no Microsoft Fabric, usando MCP como camada fina de integração.

## Contexto

O modelo de forecast (consumo + vendas) será entregue como **modelo semântico do Fabric** e/ou **API/endpoint**. O agente precisa consultá-lo sob demanda e devolver um número + intervalo de confiança para o usuário final. O **MCP (Model Context Protocol)** é o protocolo padrão que permite ao agente chamar "ferramentas" externas — no caso, consultar o Fabric.

**Princípio**: o MCP é "cola", não o core. Primeiro define-se o entregável (semântico vs endpoint); depois adiciona-se o MCP por cima.

## Arquitetura alvo

```
Usuário ──► Agente (Foundry/Semantic Kernel)
                 │  (MCP client)
                 ▼
        MCP Server (Fabric)
                 │  tools: query_semantic_model (DAX), query_lakehouse (SQL), run_pipeline, list_items
                 ▼
   ┌─────────────────────────────────────┐
   │ Microsoft Fabric (workspace)        │
   │  · Modelo Semântico (DirectLake)    │
   │  · Lakehouse Gold (tabelas Delta)   │
   │  · SQL analytics endpoint           │
   │  · Pipelines (agendadas)            │
   └─────────────────────────────────────┘
```

## Opções de MCP para Fabric

| MCP | Tipo | Foco | Quando usar |
|-----|------|------|-------------|
| `microsoft/fabric-rti-mcp` | Oficial | Real-Time Intelligence / Eventhouse (KQL) | alertas, eventos, monitoramento em tempo real |
| Fabric **data agent** (nativo) | Nativo Fabric | Q&A em linguagem natural sobre semântico/lakehouse | se o agente já estiver dentro do ecossistema Fabric |
| `santhoshravindran7/Fabric-Analytics-MCP` | Comunidade | Modelo semântico / analytics (DAX) | consumo de previsões já materializadas no semântico |
| `Augustab/microsoft_fabric_mcp` | Comunidade | Wrapper da Fabric REST API (workspaces, itens, pipelines) | orquestração/disparo de pipeline via agente |
| `ksylvan/fabric-mcp` | Comunidade | AI Skills do Fabric | expor skills/agentes do Fabric |

## Critérios de escolha (recomendado)

Decidir na reunião de validação o formato de entrega, depois escolher:

| Entrega final | MCP recomendado | Por quê |
|---------------|-----------------|---------|
| Modelo semântico (Power BI/DirectLake) | `Fabric-Analytics-MCP` **ou** Fabric data agent nativo | consulta DAX direto sobre métricas prontas |
| API/endpoint sob demanda | `microsoft_fabric_mcp` (REST) + endpoint próprio | controle fino, menos acoplamento |
| Alertas/eventos (Eventhouse) | `microsoft/fabric-rti-mcp` | KQL/streaming |

**Recomendação para este projeto**: entregar **modelo semântico (DirectLake)** com as previsões materializadas na camada Gold, e usar o **Fabric data agent nativo** (ou `Fabric-Analytics-MCP`) como ponte. É o caminho de menor custo e menor manutenção, alinhado ao FinOps da capacidade F8.

## Exemplo de configuração (MCP client → servidor)

Configuração típica de um cliente MCP (formato JSON, `stdio`):

```json
{
  "mcpServers": {
    "fabric-analytics": {
      "command": "npx",
      "args": ["-y", "fabric-analytics-mcp"],
      "env": {
        "FABRIC_TENANT_ID": "<tenant-id>",
        "FABRIC_CLIENT_ID": "<service-principal-id>",
        "FABRIC_CLIENT_SECRET": "<client-secret>",
        "FABRIC_WORKSPACE_ID": "<workspace-id>",
        "FABRIC_SEMANTIC_MODEL_ID": "<model-id>"
      }
    }
  }
}
```

## Segurança e governança

- Autenticar via **service principal** (Entra ID) com escopo mínimo (leitura do semântico/lakehouse).
- Nunca expor segredos no repo; usar cofre/segredo do agente.
- MCP só lê as **tabelas de saída do Forecast** (`lh_forecast`; nunca Bronze/Silver nem a Gold do agente atual), limitando superfície de dados sensíveis. Detalhes em [09_conexao_e_consumo_fabric.md](09_conexao_e_consumo_fabric.md).
- Opção recomendada para contrato estável: MCP fino próprio (FastMCP) com tools de leitura parametrizada.
- Auditar chamadas (quem consultou o quê) via logs do agente/Fabric.

## FinOps (capacidade F8)

- Consultas DAX/SQL sobre DirectLake consomem CU da capacidade F8, compartilhada com o agente.
- Preferir **agregados pré-calculados na Gold** (evitar DAX pesado em tempo real).
- Cachear resultados de previsão (o forecast não muda entre execuções de pipeline).
- MCP em si tem custo ~zero; o custo está nas consultas — manter leves e esparsas.

## Integração ao plano de execução (novo item)

Adicionar à **Fase 5 — Entrega e handoff**:

1. Definir formato de entrega (semântico vs endpoint) na reunião de validação.
2. Escolher o MCP correspondente (tabela acima).
3. Provisionar service principal + escopos mínimos no Fabric.
4. Configurar o MCP client no agente (arquivo de configuração + segredos).
5. Testar o fluxo ponta-a-ponta: pergunta do usuário → DAX/SQL → previsão + intervalo.
6. Validar custo (CU) das consultas na F8 e ajustar agregações se necessário.
