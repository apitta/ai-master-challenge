"""Lista priorizada do pipeline aberto, com filtros e visão por faixa."""

import pandas as pd
import streamlit as st

import api_client
from components import BAND_STYLE, band_badge, band_cell_css, fmt_date, money, num
from filters import sidebar_filters

try:
    params = sidebar_filters()
    rows = api_client.opportunities(params)
    summary = api_client.summary(params)
except api_client.ApiError as e:
    st.error(str(e))
    st.stop()

st.title("Pipeline priorizado")
st.caption(
    f"Oportunidades abertas em {fmt_date(summary['reference_date'])}, ordenadas por prioridade: "
    "faixa primeiro, depois score. Clique em uma linha para ver o detalhe e as ações."
)

# ---------- KPIs ----------
total = summary["total"]
missing = sum(b["missing_account"] for b in summary["bands"])
k1, k2, k3, k4 = st.columns(4)
k1.metric("Oportunidades abertas", num(total), border=True)
k2.metric("Pipeline (preço de lista)", money(summary["pipeline_value"], compact=True), border=True,
          help=money(summary["pipeline_value"]))
k3.metric(
    "Viram paradas em ≤ 30 dias", num(summary["stalling_soon"]), border=True,
    help="Em Engaging e perto do limite de ciclo. Depois dele, nenhum negócio do histórico fechou.",
)
k4.metric("Sem conta cadastrada", num(missing), border=True, help="Oportunidades sem cliente informado.")

# ---------- faixas ----------
cols = st.columns(5)
for col, b in zip(cols, summary["bands"]):
    share = b["count"] / total if total else 0
    with col.container(border=True):
        st.markdown(band_badge(b["band"]), unsafe_allow_html=True)
        st.markdown(f"### {num(b['count'])} <small>({share:.0%})</small>", unsafe_allow_html=True)
        st.caption(money(b["pipeline_value"], compact=True), help=b["action"])

if total and summary["bands"][-1]["count"] / total > 0.5:
    st.info(
        f"♻ **{summary['bands'][-1]['count'] / total:.0%} deste pipeline está parado** (faixa R). "
        "Encerrar ou requalificar essas oportunidades deixa a lista honesta e o foco nas faixas A e B."
    )

# ---------- tabela ----------
if not rows:
    st.warning("Nenhuma oportunidade para os filtros selecionados.")
    st.stop()

df = pd.DataFrame(rows)
table = pd.DataFrame({
    "Faixa": df["band"],
    "Score": df["score"],
    "ID": df["id"],
    "Conta": df["account"].fillna("⚠ sem conta"),
    "Produto": df["product"],
    "Estágio": df["stage"],
    "Dias em Engaging": df["days_engaging"],
    "Vira parada em": df["days_to_stall"],
    "Preço de lista (US$)": df["list_price"],
    "Vendedor": df["agent"],
    "Próximo passo": pd.to_datetime(df["next_step_date"]),
    "Ação recomendada": df["action"],
})

st.subheader(f"{num(len(table))} oportunidades")
event = st.dataframe(
    table.style.map(band_cell_css, subset=["Faixa"]),
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    height=560,
    column_config={
        "Faixa": st.column_config.TextColumn(width="small", help="; ".join(f"{k}: {v['name']}" for k, v in BAND_STYLE.items())),
        "Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d", width="small"),
        "Dias em Engaging": st.column_config.NumberColumn(format="%d", help="Vazio = ainda em Prospecting"),
        "Vira parada em": st.column_config.NumberColumn(format="%d dias", help="Dias até ultrapassar o limite de ciclo"),
        "Preço de lista (US$)": st.column_config.NumberColumn(format="localized"),
        "Próximo passo": st.column_config.DateColumn(format="DD/MM/YYYY"),
    },
    key="pipeline_table",
)

if event.selection.rows:
    opp_id = table.iloc[event.selection.rows[0]]["ID"]
    st.switch_page("views/opportunity.py", query_params={"id": opp_id})

st.download_button(
    "Baixar lista (CSV)", table.to_csv(index=False).encode("utf-8"), "pipeline_priorizado.csv", "text/csv"
)
