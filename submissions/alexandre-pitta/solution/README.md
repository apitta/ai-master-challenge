# Pipeline: priorização de oportunidades

Aplicação web para o vendedor abrir na segunda de manhã e saber **onde focar**: o pipeline aberto ordenado por prioridade, com o **porquê** de cada score e **ações** que ele executa ali mesmo.

Usa a planilha [`data/lead_scoring_pipeline.xlsx`](data/lead_scoring_pipeline.xlsx) (abas Pipeline, Parâmetros e Histórico) como carga inicial.

## Como rodar

**Local (Python 3.10+)**, a partir da raiz do repositório:

```bash
cd solution
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
./start.sh                      # UI em http://localhost:8501 · API em http://localhost:8000/docs
pytest                          # 17 testes, incluindo o score batendo com o Excel
```

O `start.sh` pode ser chamado de qualquer diretório (por exemplo, `./solution/start.sh` da raiz) e usa a `.venv` da pasta, se ela existir. Se a pasta `solution/` for movida, recrie a `.venv`: os executáveis dela guardam o caminho absoluto de onde foi criada.

Também dá para subir cada camada separadamente, de dentro de `solution/`:
- `uvicorn app.api:app --reload`
- `streamlit run ui/app.py`

**Container**

```bash
docker build -t pipeline-app solution               # ou, de dentro de solution/: docker build -t pipeline-app .
docker run -p 8501:8501 pipeline-app                                  # banco em memória
docker run -p 8501:8501 -e DATABASE_URL=sqlite:////data/app.db \
           -v pipeline-data:/data pipeline-app                        # persistido em disco
docker compose -f solution/docker-compose.yml up --build   # API e UI como serviços separados, com volume
```

**Railway**: conecte o repositório e defina o *Root Directory* do serviço como `/solution`. O `railway.toml` já configura o build pelo Dockerfile e o healthcheck. A Railway injeta a variável `PORT`, e o `start.sh` a usa. Para persistir os dados:
1. Crie um volume montado em `/data`.
2. Defina `DATABASE_URL=sqlite:////data/app.db`.
3. Defina `RAILWAY_RUN_UID=0`, porque o volume é criado com dono root e a imagem roda como usuário não-root.

### Variáveis de ambiente

| Variável | Padrão | Uso |
|---|---|---|
| `DATABASE_URL` | `sqlite://` (memória) | `sqlite:////data/app.db` persiste em disco; qualquer URL SQLAlchemy (ex.: Postgres) também funciona |
| `REFERENCE_DATE` | da planilha (31/12/2017) | Data "de hoje" usada no cálculo de dias em Engaging |
| `SEED_FILE` | `data/lead_scoring_pipeline.xlsx` | Planilha da carga inicial |
| `PORT` | `8501` | Porta pública da interface |
| `API_URL` | `http://127.0.0.1:8000` | Endereço da API, visto pela interface |

## Arquitetura

```
Streamlit (ui/)  ──HTTP──▶  FastAPI (app/api.py)  ──▶  services.py ──▶ SQLAlchemy ──▶ SQLite (memória ou disco)
  lista + detalhe            contratos (schemas.py)     playbook.py   scoring.py (funções puras)
```

- **`app/scoring.py`**: o modelo de score em funções puras, sem banco nem I/O.
- **`app/playbook.py`**: traduz o score em explicação ("por que") e em recomendação e comandos ("o que fazer").
- **`app/services.py`**: consultas, filtros e execução de comandos. Cada comando grava uma `Activity` com a faixa antes e depois, o que forma uma trilha de auditoria.
- **`app/seed.py`**: lê da planilha **apenas as células de entrada** (dados e premissas). Nunca lê os resultados das fórmulas; o score é sempre recalculado.
- **`ui/`**: não acessa o banco; tudo passa pela API. Tem três páginas: Pipeline, Oportunidade e Documentação.
- **`docs/`**: `model.md` (documentação completa do modelo de score) e `aplicacao.md` (como a aplicação usa o modelo). A página Documentação renderiza os dois arquivos; para mudar o conteúdo, edite-os.

No container, a API escuta só em `127.0.0.1` e a interface é o único serviço exposto. Se qualquer um dos dois processos cair, o container encerra e a plataforma o reinicia.

A persistência funciona assim: em memória, cada start recarrega a planilha do zero; em disco, a carga só roda se o banco estiver vazio, então as ações dos vendedores sobrevivem a reinícios (há teste para isso).

## Lógica de scoring

É a réplica fiel do modelo da planilha. Os parâmetros vêm da aba **Parâmetros**, não do código:

```
Score = (Pontos de valor + Pontos de tempo) × Multiplicador      (0–100)
```

| Componente | Regra | Por quê |
|---|---|---|
| **Valor (0–60)** | Preço de lista em escala log: MG Special (US$ 55) = 0 … GTK 500 (US$ 26.768) = 60 | Os preços variam 500×; a escala log evita que só o GTK 500 importe. Os negócios fecham em média a ~100% do preço de lista. |
| **Tempo (0–40)** | Dias em Engaging: 0–14 → 20 · 15–90 → 32 · 91–138 → 40. Prospecting = 10 fixo | Taxa de ganho histórica por fase do ciclo: 55% → 67% → 71% |
| **Multiplicador** | Até 138 dias ×1 · 139–180 ×0,6 · 181–270 ×0,4 · 271+ ×0,25 | **Nenhum negócio do histórico fechou com ciclo maior que 138 dias** |
| **Faixa** | A ≥ 75 · B ≥ 55 · C ≥ 35 · D < 35 · **R** = parada (> 138 dias) | Cada faixa tem uma ação e um prazo para o próximo passo |

O arquivo [`tests/test_scoring.py`](tests/test_scoring.py) compara as 2.089 oportunidades com os valores calculados pelo Excel: **100% idênticas**. Isso inclui o arredondamento `ROUND` do Excel (0,5 para longe do zero), que difere do `round()` do Python.

A planilha também documenta o que **não** entra no score: setor, porte, receita, país, produto e vendedor não mostraram poder preditivo sobre o ganho (lift entre 0,95 e 1,05; AUC fora do tempo ≈ 0,50).

### Recomendações e comandos por faixa

| Faixa | Recomendação | Comando principal | Prazo padrão do próximo passo |
|---|---|---|---|
| A | Próximo passo concreto em até 48h | Registrar atividade | +2 dias |
| B | Cadência semanal | Registrar atividade | +7 dias |
| C | Qualificar antes de investir tempo | Registrar atividade | +14 dias |
| D | Automatizar ou tratar em lote | Registrar atividade | +30 dias |
| Prospecting | Qualificar e mover para Engaging | Mover para Engaging | — |
| R ×0,6 | Parada recente | Reengajar | +7 dias |
| R ×0,4 | Parada há mais tempo | Requalificar (volta para Prospecting) | — |
| R ×0,25 | Mais de 270 dias | Encerrar | — |

Além desses, cada oportunidade pode receber:
- **Alerta de estouro**: aviso quando faltam 30 dias ou menos para a oportunidade virar parada.
- **Ciclo de referência**: a mediana do ciclo dos negócios ganhos do mesmo produto.
- **Completar cadastro**: comando disponível quando falta a conta.

## Limitações e próximos passos

- **Os dados param em 31/12/2017.** A "data de hoje" é a data de referência; o dia real é usado só para registrar o momento das atividades.
- **O score não enxerga atividade.** O tempo conta a partir da data de engajamento. Um contato registrado não "descongela" uma oportunidade parada; só requalificar (voltar para Prospecting) reinicia o ciclo. Com dados de última interação do CRM, o tempo desde o último contato seria um sinal melhor.
- **Não há dados de contato do cliente** (e-mail, telefone, decisor, cargo). Por isso as ações são registros e lembretes, não disparos de mensagens.
- **Não há autenticação.** O filtro por vendedor é uma conveniência, não um controle de acesso. Para produção, seria preciso SSO e escopo por vendedor ou gerente.
- **Os parâmetros são lidos só na carga inicial.** Uma tela de parâmetros (com recálculo, que já existe em `rescore_all`) é uma extensão natural.
- **SQLite atende um único processo de API.** Para escalar horizontalmente, basta trocar `DATABASE_URL` por Postgres; nenhum código muda.
