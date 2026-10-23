# Notas sobre os Dados (S360)

## Fonte

- **S360** — o LIMS, fonte da verdade.
- Provavelmente contém tudo o que é necessário; se algo estiver faltando, o cliente fornecerá conforme nossos requisitos.
- **Sem dicionário de dados** — precisamos fazer engenharia reversa das estruturas das tabelas por conta própria.

## Problemas esperados de qualidade dos dados

- Valores ausentes
- Outliers ocasionais
- Erros de digitação
- → Perceber e lidar com isso faz parte do trabalho.

## Censura (consideração crítica de modelagem)

No meio do período, muitas amostras foram recebidas mas ainda não concluídas. Seu TAT final e status on-time são desconhecidos. A forma como essas amostras em andamento (censuradas) são tratadas afeta materialmente a previsão.

Amostras censuradas devem ser tratadas com uma abordagem fundamentada — por exemplo, análise de sobrevivência, estimativas de conclusão esperada ou modelagem explícita de "risco" — em vez de serem descartadas ou assumidas como concluídas.

## Elementos de dados a descobrir no S360

- ID da amostra e timestamp de recebimento (CRD).
- Timestamps de conclusão por estágio (Laboratório, Interpretação).
- Eventos de re-teste / loops.
- Faixa de prazo por amostra (ou os atributos necessários para derivá-la: tipo de óleo, equipamento, compartimento).
- Mapeamento da hierarquia ensaio → grupo de trabalho → pacote.
- Identificador de laboratório / local.

## Plano de descoberta de dados

1. Explorar a lista de tabelas e os esquemas no S360.
2. Rastrear o ciclo de vida de uma amostra de ponta a ponta pelas tabelas.
3. Confirmar as junções da hierarquia (ensaios → grupos de trabalho → pacotes → laboratório).
4. Confirmar a derivação da faixa de prazo.
5. Construir um relatório inicial de qualidade (ausências, outliers, sanidade dos timestamps).
