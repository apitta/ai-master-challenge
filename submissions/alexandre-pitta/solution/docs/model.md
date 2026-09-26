# Sistema de Lead Scoring de Oportunidades

**Versão:** 1.0 (protótipo)
**Base de dados:** CRM de vendas B2B (`sales_pipeline`, `accounts`, `products`, `sales_teams`)
**Data de referência da calibração:** 31/12/2017, a última data disponível nos arquivos
**Implementação:** planilha `lead_scoring_pipeline.xlsx` (compatível com Google Sheets)

---

## 1. Objetivo

Priorizar as oportunidades abertas do pipeline para que o time comercial concentre esforço onde há **mais valor em jogo** e **melhor momento no ciclo de venda**, e sinalizar as oportunidades **paradas** que precisam ser recicladas.

O score **não** estima a probabilidade de ganho de cada oportunidade. Os dados disponíveis não mostraram poder preditivo para isso (ver seção 3). Ele é um **índice de prioridade** que combina valor e momento.

---

## 2. Escopo

| Item | Definição |
|---|---|
| Unidade avaliada | Oportunidade (`opportunity_id`), não lead nem conta |
| População pontuada | Oportunidades em **Engaging** e **Prospecting** |
| Fora do escopo | Oportunidades já fechadas (**Won** e **Lost**), usadas só como histórico de calibração |
| Frequência sugerida | Recalcular diariamente ou semanalmente, com a data de referência = hoje |

### Volume na calibração

| Estágio | Quantidade | Uso |
|---|---|---|
| Won | 4.238 | Histórico |
| Lost | 2.473 | Histórico |
| Engaging | 1.589 | Pontuada |
| Prospecting | 500 | Pontuada |
| **Total** | **8.800** | |

Taxa de ganho histórica: **63,2%** (4.238 de 6.711 negócios fechados).

---

## 3. Fatos que embasam o desenho

### 3.1 Atributos da conta, do produto e do time não preveem o ganho

A taxa de ganho foi calculada para cada valor de atributo e comparada com a taxa geral (lift = taxa do grupo ÷ taxa geral). Todos os lifts ficaram entre **0,95 e 1,05**, praticamente iguais à média.

| Atributo | Faixa de lift observada |
|---|---|
| Setor | 0,97 – 1,03 |
| Receita da conta (quartis) | 0,97 – 1,04 |
| Número de funcionários (quartis) | 0,97 – 1,02 |
| Idade da empresa (quartis) | 0,99 – 1,02 |
| Sede nos EUA vs. fora | 0,99 – 1,00 |
| Subsidiária vs. independente | 1,00 – 1,01 |
| Produto | 0,95 – 1,03 |
| Série do produto | 0,95 – 1,00 |
| Escritório regional | 0,99 – 1,01 |
| Gerente | 0,98 – 1,02 |

**Teste fora do tempo:** as taxas de ganho foram calculadas com os negócios engajados até maio/2017 e aplicadas aos engajados depois disso. O poder de discriminação (AUC) ficou em **0,50 para conta**, **0,53 para vendedor** e **0,51 para produto**, ou seja, equivalente ao acaso.

**Conclusão:** esses atributos ficam fora do score. Incluí-los daria aparência de precisão sem ganho real.

### 3.2 O valor varia quase 500 vezes entre produtos

| Produto | Série | Preço de lista (US$) |
|---|---|---|
| MG Special | MG | 55 |
| GTX Basic | GTX | 550 |
| GTX Plus Basic | GTX | 1.096 |
| MG Advanced | MG | 3.393 |
| GTX Pro | GTX | 4.821 |
| GTX Plus Pro | GTX | 5.482 |
| GTK 500 | GTK | 26.768 |

Os negócios ganhos fecham em média a **99,6% do preço de lista** (mediana de 99,8%), então o preço de lista é uma boa medida do valor em jogo.

### 3.3 Tempo no ciclo é o único sinal comportamental disponível

A única informação temporal é `engage_date`, a data de entrada em Engaging. Não existem registros de interações, origem do lead nem cargo do contato.

Taxa de ganho por duração do ciclo (negócios fechados):

| Dias entre engajamento e fechamento | Negócios | Taxa de ganho |
|---|---|---|
| 0 – 7 | 1.413 | 53,5% |
| 8 – 14 | 1.393 | 57,5% |
| 15 – 30 | 357 | 72,8% |
| 31 – 60 | 569 | 66,3% |
| 61 – 90 | 1.621 | 66,5% |
| 91 – 138 | 1.358 | 71,1% |

Observações:

- As perdas se concentram nas duas primeiras semanas. Negócios que passam desse ponto ganham com mais frequência.
- **O ciclo mais longo do histórico foi de 138 dias.** Nenhum negócio fechou, ganho ou perdido, depois disso.

### 3.4 Qualidade do pipeline aberto

| Problema | Quantidade | Impacto |
|---|---|---|
| Engaging há mais de 138 dias | **1.291 de 1.589** (81%) | Acima de qualquer ciclo já observado: provavelmente parados |
| Engaging sem conta preenchida | 1.088 de 1.589 (68%) | Sem dados cadastrais da empresa |
| Prospecting sem conta preenchida | 337 de 500 (67%) | Idem |
| Prospecting sem `engage_date` | 500 de 500 | Esperado: ainda não engajado |

### 3.5 Ajustes feitos nos dados

| Ajuste | Motivo |
|---|---|
| `GTXPro` → `GTX Pro` | Grafia diferente entre `sales_pipeline` e `products` |
| `technolgy` → `technology` | Erro de digitação em `accounts.sector` |

---

## 4. Fórmula

```
Score = (Pontos de valor + Pontos de tempo) × Multiplicador de reciclagem
```

Escala de **0 a 100**. Valor responde por até 60 pontos e tempo por até 40.

### 4.1 Pontos de valor (0 – 60)

Escala logarítmica do preço de lista, para que o GTK 500 não esmague a diferenciação entre os demais produtos:

```
Pontos de valor = ROUND( 60 × (LN(preço) − LN(preço mínimo)) / (LN(preço máximo) − LN(preço mínimo)) )
```

| Produto | Preço (US$) | Pontos de valor |
|---|---|---|
| MG Special | 55 | 0 |
| GTX Basic | 550 | 22 |
| GTX Plus Basic | 1.096 | 29 |
| MG Advanced | 3.393 | 40 |
| GTX Pro | 4.821 | 43 |
| GTX Plus Pro | 5.482 | 45 |
| GTK 500 | 26.768 | 60 |

### 4.2 Pontos de tempo (0 – 40)

`Dias em Engaging = Data de referência − engage_date`

| Situação | Pontos | Taxa de ganho histórica | Racional |
|---|---|---|---|
| Prospecting (sem data) | 10 | n/a | Ainda não qualificada |
| Engaging, 0 – 14 dias | 20 | 55,5% | Fase com mais perdas |
| Engaging, 15 – 90 dias | 32 | 67,3% | Ganho estabiliza em cerca de 2/3 |
| Engaging, 91 – 138 dias | 40 | 71,1% | Fase de decisão, maior taxa de ganho |
| Engaging, mais de 138 dias | 0 | n/a | Parada: acima do ciclo máximo |

### 4.3 Multiplicador de reciclagem

Aplicado só às oportunidades **paradas** (Engaging há mais de 138 dias):

| Dias em Engaging | Multiplicador | Orientação |
|---|---|---|
| 0 – 138 | 1,00 | Ativa, sem penalidade |
| 139 – 180 | 0,60 | Parada recente: reengajar |
| 181 – 270 | 0,40 | Requalificar |
| Mais de 270 | 0,25 | Avaliar encerramento |

Como os pontos de tempo de uma parada são zero, o score dela é igual a **Pontos de valor × Multiplicador**. Isso garante duas coisas:

1. Uma oportunidade parada **nunca passa à frente** de uma ativa equivalente.
2. Dentro da fila de reciclagem, a ordem fica por **valor** e por **quão recente é a parada**. Um GTK 500 parado há 150 dias (score 36) aparece antes de um MG Advanced parado há 300 dias (score 10).

---

## 5. Faixas e ações

| Faixa | Critério | Ação recomendada |
|---|---|---|
| **A** | Ativa, score ≥ 75 | Prioridade máxima: próximo passo em até 48h |
| **B** | Ativa, score 55 – 74 | Cadência padrão |
| **C** | Ativa, score 35 – 54 | Cadência leve, com foco em qualificar |
| **D** | Ativa, score < 35 | Automatizar ou vender em lote |
| **R** | Parada (Engaging há mais de 138 dias), qualquer score | Reciclar: requalificar, reengajar ou encerrar |

A meta de calibração é que a **faixa A** reúna de 15% a 20% das oportunidades ativas. Mais que isso dilui a priorização.

### 5.1 Distribuição na calibração (31/12/2017)

| Faixa | Oportunidades | % das oportunidades | Pipeline (US$, preço de lista) | % do pipeline | Sem conta |
|---|---|---|---|---|---|
| A | 112 | 5,4% | 555.707 | 11,2% | 84 |
| B | 148 | 7,1% | 378.906 | 7,6% | 100 |
| C | 299 | 14,3% | 773.758 | 15,6% | 196 |
| D | 239 | 11,4% | 59.180 | 1,2% | 166 |
| R | 1.291 | 61,8% | 3.198.664 | 64,4% | 879 |
| **Total** | **2.089** | **100%** | **4.966.215** | **100%** | **1.425** |

Faixa A entre as ativas: **112 de 798 = 14,0%**.

### 5.2 Produto × faixa

| Produto | A | B | C | D | R |
|---|---|---|---|---|---|
| GTK 500 | 1 | 0 | 0 | 0 | 14 |
| GTX Plus Pro | 36 | 48 | 0 | 0 | 139 |
| GTX Pro | 54 | 2 | 80 | 0 | 197 |
| MG Advanced | 21 | 8 | 86 | 0 | 213 |
| GTX Plus Basic | 0 | 54 | 75 | 0 | 203 |
| GTX Basic | 0 | 36 | 22 | 93 | 279 |
| MG Special | 0 | 0 | 36 | 146 | 246 |

### 5.3 Oportunidades paradas por tempo de parada

| Dias em Engaging | Oportunidades | Multiplicador |
|---|---|---|
| 139 – 180 | 561 | 0,60 |
| 181 – 270 | 358 | 0,40 |
| Mais de 270 | 372 | 0,25 |

**Principal achado:** **64% do valor do pipeline está na faixa R.** A reciclagem é hoje a maior alavanca de receita, maior que a priorização das oportunidades ativas.

---

## 6. Exemplos de cálculo

| Oportunidade | Pontos de valor | Pontos de tempo | Multiplicador | Score | Faixa |
|---|---|---|---|---|---|
| GTK 500, Engaging há 95 dias | 60 | 40 | 1,00 | **100** | A |
| GTX Plus Pro, Engaging há 120 dias | 45 | 40 | 1,00 | **85** | A |
| MG Advanced, Engaging há 30 dias | 40 | 32 | 1,00 | **72** | B |
| GTX Basic, Engaging há 10 dias | 22 | 20 | 1,00 | **42** | C |
| GTX Pro, Prospecting | 43 | 10 | 1,00 | **53** | C |
| MG Special, Prospecting | 0 | 10 | 1,00 | **10** | D |
| GTK 500, Engaging há 150 dias | 60 | 0 | 0,60 | **36** | R |
| GTX Plus Pro, Engaging há 200 dias | 45 | 0 | 0,40 | **18** | R |
| MG Advanced, Engaging há 300 dias | 40 | 0 | 0,25 | **10** | R |

---

## 7. Regras de negócio

1. **Classificação como parada:** uma oportunidade em Engaging com mais dias que o limite de ciclo (hoje, 138) vai para a faixa R, qualquer que seja o score.
2. **Saída da faixa R:** quando o vendedor retoma o contato, deve registrar uma **nova `engage_date`**. A oportunidade volta a ser pontuada como ativa. Sem esse registro, ela continua em R.
3. **Encerramento:** oportunidades em R com mais de 270 dias e sem resposta ao reengajamento devem ser marcadas como Lost, para manter o pipeline limpo e as métricas confiáveis.
4. **Cadastro incompleto:** oportunidades sem conta recebem o score normalmente, porque os dados da conta não alteram a probabilidade de ganho, e ganham o alerta **"Completar cadastro"**.
5. **Prospecting:** recebe pontuação fixa de tempo (10) até ser engajada. Nenhuma Prospecting chega à faixa A: o score máximo possível é 70 (GTK 500).
6. **Ordem de trabalho:** dentro de cada faixa, atender por score decrescente. Em caso de empate, a oportunidade com mais dias em Engaging vem primeiro.

---

## 8. Parâmetros configuráveis

Todos ficam na aba **Parâmetros** da planilha, em células amarelas com texto azul:

| Parâmetro | Valor atual | Quando revisar |
|---|---|---|
| Data de referência | 31/12/2017 | Em produção, trocar por `=HOJE()` |
| Limite de ciclo (dias) | 138 | Trimestralmente, comparando com o ciclo máximo do histórico (calculado ao lado) |
| Pontos máximos de valor | 60 | Se a estratégia mudar (por exemplo, priorizar volume sobre ticket) |
| Pontos fixos de Prospecting | 10 | Se houver critério de qualificação na prospecção |
| Preço de lista por produto | Tabela de produtos | A cada mudança de tabela de preços |
| Cortes de tempo e pontos | 0 / 15 / 91 dias → 20 / 32 / 40 | Quando a taxa de ganho histórica por período (calculada ao lado) mudar de ordem |
| Multiplicadores de reciclagem | 0,60 / 0,40 / 0,25 | Conforme a taxa de sucesso real da reciclagem |
| Cortes das faixas | A ≥ 75, B ≥ 55, C ≥ 35 | Para manter a faixa A entre 15% e 20% das ativas |

---

## 9. Estrutura da planilha

| Aba | Conteúdo |
|---|---|
| **Leia-me** | Lógica, premissas e instruções de uso |
| **Resumo** | Distribuição por faixa, produto × faixa e contagens por vendedor (faixas A a R e valor em A+B) |
| **Parâmetros** | Pesos, cortes e multiplicadores editáveis, com a taxa de ganho histórica ao lado para validação |
| **Pipeline** | Oportunidades abertas pontuadas, com filtro por faixa, vendedor, produto etc. |
| **Histórico** | Negócios fechados usados na calibração, com duração do ciclo e resultado |

Colunas calculadas na aba Pipeline: preço de lista, dias em Engaging, pontos de valor, pontos de tempo, multiplicador, score, parada?, faixa, alerta de cadastro e ação recomendada.

---

## 10. Governança e monitoramento

| Indicador | Meta / leitura esperada | Frequência |
|---|---|---|
| Taxa de ganho por faixa (A, B, C) | Coerente com o histórico do período de tempo | Mensal |
| % de oportunidades ativas na faixa A | 15% – 20% | Mensal |
| Oportunidades na faixa R | Queda contínua | Semanal |
| Taxa de reativação da faixa R | Serve para calibrar os multiplicadores | Mensal |
| % de oportunidades sem conta | Queda contínua | Mensal |
| Ciclo máximo histórico | Serve para recalibrar o limite de ciclo | Trimestral |

---

## 11. Limitações

- **O score não estima a probabilidade de ganho.** Ele ordena por valor e momento, porque os atributos disponíveis não discriminam ganho e perda.
- **Os dados parecem sintéticos.** A falta de sinal nos atributos pode ser uma característica desta base. Com dados reais, refaça o teste de lift (seção 3.1) antes de fixar os pesos.
- **O valor usa o preço de lista** e não reflete negociações futuras. Isso é aceitável porque os negócios fecham em média a ~100% dele.
- **Não há sinais de engajamento** (e-mails, reuniões, respostas). O tempo no estágio é um substituto imperfeito.

---

## 12. Evolução recomendada

1. **Registrar sinais de engajamento:** data da última interação, próximo passo agendado e tipo de contato. É o que permitiria, no futuro, um score preditivo de verdade.
2. **Registrar datas de mudança de estágio:** hoje só existe a entrada em Engaging, e não a de Prospecting.
3. **Exigir conta preenchida** para uma oportunidade avançar a Engaging.
4. **Registrar o motivo de perda**, para descobrir padrões que os atributos atuais não mostram.
5. **Peso estratégico da conta (opcional):** receita já ganha com a conta ou com o grupo econômico (`subsidiary_of`). Não prevê o ganho, mas pode refletir uma decisão de proteger contas-chave.
6. **Com sinais novos disponíveis:** reavaliar com regressão logística e, havendo volume e sinal, migrar para um modelo preditivo.
