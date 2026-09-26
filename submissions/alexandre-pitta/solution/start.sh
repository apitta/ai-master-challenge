#!/usr/bin/env bash
# Sobe a API (interna) e a interface (pública) no mesmo container.
# Se qualquer um dos dois cair, o container encerra e a plataforma reinicia.
set -euo pipefail

API_PORT="${API_PORT:-8000}"
export API_URL="${API_URL:-http://127.0.0.1:${API_PORT}}"

uvicorn app.api:app --host "${API_HOST:-127.0.0.1}" --port "$API_PORT" &

streamlit run ui/app.py \
  --server.port "${PORT:-8501}" \
  --server.address 0.0.0.0 \
  --server.headless true \
  --browser.gatherUsageStats false &

wait -n
exit $?
