## Como a aplicação usa o modelo

A aplicação recalcula o score com as mesmas regras e parâmetros da planilha. Os parâmetros são lidos da aba Parâmetros na carga inicial, e os scores das 2.089 oportunidades batem 100% com os valores calculados pelo Excel.

| Faixa / situação | Ação principal na tela de detalhe | Prazo padrão do próximo passo |
|---|---|---|
| A | Registrar atividade | 2 dias |
| B | Registrar atividade | 7 dias |
| C | Registrar atividade | 14 dias |
| D | Registrar atividade | 30 dias |
| Prospecting | Mover para Engaging | — |
| R, multiplicador 0,60 | Reengajar | 7 dias |
| R, multiplicador 0,40 | Requalificar | — |
| R, multiplicador 0,25 | Encerrar | — |

- **Saída da faixa R (regra 2):** "Requalificar" devolve a oportunidade para Prospecting. Quando o cliente reengajar, "Mover para Engaging" registra a nova data de engajamento e a oportunidade volta a ser pontuada como ativa.
- **Registrar contato não muda o score.** Reengajar registra a tentativa e o próximo passo, mas a oportunidade continua em R até ganhar uma nova data de engajamento.
- **Alerta de estouro:** oportunidades ativas em Engaging a 30 dias ou menos do limite de ciclo aparecem destacadas, porque depois dele nenhum negócio do histórico fechou.
- **Histórico:** toda ação fica registrada na oportunidade, com a faixa antes e depois. Isso alimenta os indicadores de governança (seção 10), como a taxa de reativação da faixa R.
