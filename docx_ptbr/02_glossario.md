# Glossário

| Termo | Significado |
|-------|-------------|
| TAT | Turnaround Time — tempo total de processamento nas etapas de Laboratório + Interpretação. Corre continuamente; não pausa em fins de semana/feriados. |
| Faixa de prazo (deadline band) | TAT máximo permitido para uma amostra (48 / 72 / 96 / 120 h). Fixo por amostra conforme tipo de óleo, equipamento, compartimento etc. — não é escolhido livremente. |
| Prazo cumprido | Amostra concluída dentro da faixa de prazo, medida a partir do timestamp de recebimento. |
| % On-time | Participação de amostras que cumpriram o prazo. Meta de serviço: ≥ 90% ao mês. |
| Ensaio | Um teste individual executado em uma amostra. Sinônimos: análise, teste. |
| Grupo de trabalho (workgroup) | Um grupo de ensaios. |
| Pacote | Um grupo de grupos de trabalho. Sinônimo: plano de análise. |
| S360 | O LIMS (Sistema de Gerenciamento de Informações de Laboratório) — fonte dos dados. |
| O agente | Sistema automatizado existente ao qual o modelo se conecta; chama o modelo sob demanda para devolver previsões aos usuários. |
| Amostra censurada | Uma amostra recebida mas ainda não concluída no meio do período, cujo TAT final / status on-time é desconhecido. |

## Implicações para a modelagem

- **A faixa de prazo é um atributo por amostra**, derivado do tipo de óleo / equipamento / compartimento — é uma entrada, não uma escolha livre.
- **% On-time** é um resultado binário por amostra (`TAT <= faixa de prazo`) agregado ao longo de um período.
- **TAT** é uma duração contínua medida a partir do timestamp de recebimento, abrangendo apenas Laboratório + Interpretação.
- **Censura** é central: previsões de meio de período precisam lidar com amostras que ainda não têm timestamp de conclusão.
