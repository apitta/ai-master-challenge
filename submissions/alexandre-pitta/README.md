# Submissão — [Alexandre Pitta] — Challenge [003]

## Sobre mim

- **Nome:** Alexandre Pitta
- **LinkedIn:** https://www.linkedin.com/in/alexandrepitta
- **Challenge escolhido:** challenge 3 - lead score

---

## Executive Summary

Para aumentar a eficiência do time de vendas, desenvolvemos um modelo de score que prioriza objetivamente as oportunidades comerciais. O modelo pontua cada oportunidade com base em três critérios: valor potencial, tempo no funil e um fator de reciclagem, que indica a chance de reativar negócios parados. As oportunidades são agrupadas por faixa de score, e cada faixa tem uma recomendação de ação clara para o time comercial. Para colocar isso em prática, estamos lançando um sistema web de gestão de oportunidades que apoia a classificação, o acompanhamento e o fechamento dos negócios. O próximo passo é implantar com o time comercial até segunda-feira e acompanhar a taxa de conversão e o ciclo de venda para medir o impacto da iniciativa.

---

## Solução

A plataforma de gestão de oportunidades apoia o time comercial em todo o ciclo de vida da oportunidade, do primeiro contato ao fechamento da venda. Cada oportunidade recebe um score calculado a partir de três critérios: tempo no funil, valor da oportunidade e um fator de reciclagem, que indica o potencial de reativar negócios parados. As oportunidades são agrupadas por faixa de score, e cada faixa tem recomendações de ação específicas, para que o vendedor saiba onde concentrar o esforço. No dia a dia, o time atualiza o cadastro dos clientes e registra cada ação comercial por lead, mantendo o histórico centralizado. Para a gestão, a plataforma reúne os principais indicadores da operação comercial, o que permite acompanhar o desempenho e ajustar prioridades.

### Abordagem

Comecei explorando o dataset para entender quais informações estavam disponíveis e quais delas indicavam potencial de fechamento. Dividi o problema em três etapas: (1) definir um modelo de score com base em tempo, valor e fator de reciclagem, (2) validar esse modelo em planilha e (3) transformar o resultado em algo utilizável pelo time comercial. Priorizei validar a lógica do score antes de construir qualquer interface, para garantir que a ordenação das oportunidades fazia sentido. Com o modelo validado, concentrei o esforço em uma aplicação web que coloca a priorização no dia a dia do gerente de conta, porque o valor está na execução da venda, e não só na classificação. Reconheço que o modelo foi limitado às dimensões do dataset. Com dados de um CRM, ele poderia incorporar outras variáveis do cliente.


### Resultados / Findings

Findings

O dataset tem 2089 oportunidades abertas, que o score distribuiu em [A: 5% · B: 7% · C: 14%].
O grupo A concentra [11%] do valor total em apenas [5%] das oportunidades, o que mostra onde o time deve focar.
1291 oportunidades estavam paradas há mais de 128 dias, mas têm alto potencial de reciclagem.

O que foi construído

Modelo de score: [link da planilha]. Combina tempo, valor e fator de reciclagem em uma nota de 0 a 100.
Plataforma de gestão de oportunidades: [link]. Mostra a fila priorizada por vendedor, o histórico de interações, alertas de conversão, disparo de ações de engajamento e indicadores gerenciais.
[Screenshot 1: fila priorizada] · [Screenshot 2: detalhe da oportunidade] · [Screenshot 3: painel gerencial]

### Recomendações

Atacar já as oportunidades do grupo de maior score. Elas concentram 34% do valor da pipeline em 26% das oportunidades. É o maior retorno com o menor esforço, e não depende de nenhuma tecnologia nova.

Rodar um piloto da plataforma com um time comercial por [4–6 semanas]. Medir a conversão e o ciclo de venda em comparação com o time sem a ferramenta. O patrocínio da liderança comercial é importante para garantir a adoção.

Reativar as oportunidades com alto potencial de reciclagem. São 1291 oportunidades paradas há mais de 128 dias, que representam receita potencialmente recuperável.

Completar o cadastro com dados de contato e decisor. Isso habilita o engajamento direto pela plataforma e melhora a precisão do score.

Calibrar os pesos do score com o histórico de ganhos e perdas, antes de escalar para toda a área comercial.

Médio prazo: integrar com o CRM e evoluir para recomendações agênticas personalizadas por cliente. A ideia que estava na seção Workflow cabe bem aqui.

### Limitações

Dados de contato do cliente. O dataset não traz telefone, e-mail, WhatsApp, cargo nem identificação do decisor. Por isso, a plataforma não dispara ações de engajamento diretamente. Esses dados também poderiam enriquecer o score, por exemplo com o peso de ter o decisor mapeado.

Validação do score. Os pesos de tempo, valor e reciclagem foram definidos por critério de negócio e [não foram / foram parcialmente] validados contra o histórico de oportunidades ganhas e perdidas. Com mais dados, seria possível calibrá-los estatisticamente.

Dimensões limitadas. O modelo usa só as variáveis do dataset. Com dados de CRM, poderia incorporar segmento, histórico de compras e engajamento.

Validação com usuários. A plataforma não foi testada com vendedores reais, então a usabilidade e a aderência das recomendações ainda precisam ser verificadas.

---

## Process Log — Como usei IA

Ferramentas: Claude ([claude.ai / Claude Code]) e VS Code.

1. Modelagem do score: usei o Claude para discutir abordagens de priorização e estruturar a fórmula em planilha. A escolha dos critérios (tempo, valor e reciclagem) e dos pesos foram sugeridas pelo modelo e eu decidi por usar um fator de reciclagem para cada oportunidade, com base no tempo da oportunidade na pipeline. 

2. Validação: Validei o resultado da planilha pessoalmente, verificando manualmente uma amostra de 50 oportunidades.

3. Desenvolvimento do app: o Claude gerou a estrutura inicial / componentes / integração com os dados no VS Code. A aplicação foi criada com stack completa em python, separando o frontend e interface com streamlit, com a base a partir dos datasets e da planilha com o modelo de score em uma conexão com um banco em memória. Além de uma visão geral das oportunidades da pipeline, é possível verificar os detalhes e disparar ações para avançar com a oportunidade. 

4. Documentação: usei o Claude para revisar a clareza e a estrutura dos documentos e relatórios.

5. Erros e intervenções: como usei prompts curtos e com contexto específico, não identifiquei erros relevantes do modelo. Ainda assim, validei manualmente os resultados da planilha e o comportamento da aplicação.

6. Aprendizado: a IA acelerou a prototipação do modelo e do app, o que me permitiu concentrar o esforço nas decisões de produto e na validação dos resultados.


### Ferramentas usadas

_Liste as ferramentas de IA que usou e para quê._

| Ferramenta | Para que usou |
|------------|--------------|
| Claude (Opus 5.5 medium) | Exploração conceitual, proposição e validação do modelo, prototipação e uso funcional no excel |
| Claude Code (VSC) | Criação do sistema de gestão de vendas |

### Workflow

| Etapa | O que eu fiz | Onde a IA entrou |
|-------|--------------|------------------|
| 1 | Entendimento do desafio | Li o enunciado e explorei o dataset para identificar os sinais de potencial de fechamento; Apoio na leitura e na interpretação do dataset |
| 2	| Definição do modelo de score | Escolhi incluir o fator de reciclagem, baseado no tempo na pipeline; O Claude sugeriu os critérios de tempo e valor e os pesos |
| 3 | Prototipação em planilha	| Montei o modelo e as faixas de score. Estruturação das fórmulas |
| 4	| Validação	| Conferi manualmente uma amostra de 50 oportunidades. |
| 5	| Desenvolvimento do app | Defini as funcionalidades, revisei e testei. O Claude gerou o código em Python/Streamlit no VS Code |
| 6 | Documentação | Escrevi o documentos e relatório. O Claude revisou a clareza e a estrutura |

### O que eu adicionei que a IA sozinha não faria

Fator de reciclagem: a IA sugeriu critérios de tempo e valor. Eu acrescentei um fator de reciclagem baseado no tempo da oportunidade na pipeline, porque oportunidades antigas não estão necessariamente perdidas e podem ser reativadas com a abordagem certa.

Validar antes de construir: decidi validar o modelo em planilha, conferindo manualmente 50 oportunidades, antes de gerar qualquer código. Assim o app foi construído sobre uma lógica já testada.

Do score à execução: uma classificação sozinha não fecha venda. Por isso direcionei a solução para uma ferramenta operacional, em que o vendedor vê a fila priorizada, o histórico e a próxima ação, e o gestor acompanha os indicadores.

Visão de evolução: identifiquei que a falta de dados de contato e de decisor limita tanto o engajamento quanto o próprio score, e desenhei a próxima evolução (a aba de comunicação com templates).

---

## Evidências

_Anexe ou linke as evidências do processo:_

- [ ] Screenshots das conversas com IA
- [ ] Screen recording do workflow
- [ ] Chat exports
- [ ] Git history (se construiu código)
- [ ] Outro: _____________

---

_Submissão enviada em: [26/09/2026]_
