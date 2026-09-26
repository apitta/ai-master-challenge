FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY ui ./ui
COPY data ./data
COPY docs ./docs
COPY .streamlit ./.streamlit
COPY start.sh .

RUN useradd --create-home appuser && mkdir -p /data && chown appuser /data
USER appuser

# Padrão: banco em memória (recarrega da planilha a cada start).
# Para persistir: DATABASE_URL=sqlite:////data/app.db com um volume em /data.
ENV DATABASE_URL=sqlite:// \
    PORT=8501

EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/_stcore/health')"

CMD ["./start.sh"]
