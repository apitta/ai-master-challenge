# Prompts

## Claude 

### Revisão do Scoring

1. pretendo criar um sistema de scoring para priorizar leads do pipeline de vendas. Quero revisar um caminho geral para a solução e refiná-la de acordo com as minhas necessidades.

2. o modelo parece estar no caminho do que eu preciso, porém assume premissas que eu não tenho disponível no meu dataset. Quero disponibilizar os arquivos csv e então revisar a proposta de desenho do modelo. **Anexei os CSV dos datasets do caso de uso do Kaggle**

3. eu pretendo pontuar com penalidade os negócios parados, indicando ao time comercial a necessidade de reciclagem da oportunidade.

4. monte a planilha e me permita fazer o donwload. Eu não tenho uma licença local do excel, vou usar o google sheets para avaliar o resultado.

5. você pode me entregar um arquivo no formato .md com a explicação do sistema de scoring, contendo a estrutura, as faixas, fatos, fórmula, tabelas, regras e todas outras informações que considerar relevante para uma documentação como a que me apresentou?

## Claude Code

### Solução de gestão de oportunidades

1. pretendo criar uma aplicação web de gestão de conversão de oportunidades para o time de vendas. A solução ideal exigiria mais dados mas eu gostaria de usar o arquivo **@asset/lead_scoring_pipeline.xlsx**  em especial a aba Pipeline para permitir que cada vendedor saiba quais oportunidades priorizar, com detalhes e recomendações. Podemos começar com uma página contendo a lista de itens no pipeline com possibilidade de aplicar filtros por vendedor, gerente, regional e produto. Cada oportunidade tem uma página de detalhes contendo informações e possíveis comandos acionáveis de acordo com a classificação de score. Eu pretendo que a aplicação seja em python e possa usar streamlit para criar as interfaces, formulários e dashboards. A camada de serviço pode ser em fastapi. A camada de dados pode ser em sqlalchemy usando um banco em memória, com possibilidade de persistência em arquivo no disco. Essa aplicação será impacotável para uma imagem container e poderá ser utilizado em uma plataforma de serviço como a hailway.

2. no menu da aplicação, além do link da pipeline e das oportunidades, quero incluir um link de documentação, usando como referência para o conteúdo dessa página o arquivo **@docs/model.md**. Essas informações detalhadas e adicionais explicam como funciona o lead score. **Anexei um screenshot do menu como complemento visual**.