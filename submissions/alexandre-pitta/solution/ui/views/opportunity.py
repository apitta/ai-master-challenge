"""Detalhe da oportunidade: por que tem esse score, o que fazer e os comandos disponíveis."""

from datetime import date

import pandas as pd
import streamlit as st

import api_client
from components import band_badge, fmt_date, md, money

ACTIVITY_KINDS = ["Ligação", "E-mail", "Reunião", "Proposta enviada", "Nota"]
LOST_REASONS = ["Sem orçamento", "Escolheu concorrente", "Sem resposta", "Sem fit com o produto", "Adiou a decisão", "Outro"]
COMMAND_LABELS = {
    "log_activity": "Atividade registrada", "advance_to_engaging": "Movida para Engaging",
    "mark_won": "Ganha", "mark_lost": "Perdida", "reengage": "Reengajamento",
    "requalify": "Requalificada", "close_stalled": "Encerrada (parada)", "complete_account": "Cadastro completado",
}

if st.button("← Voltar ao pipeline", type="tertiary"):
    st.switch_page("views/pipeline.py")

opp_id = st.query_params.get("id")
if not opp_id:
    st.title("Oportunidade")
    st.info("Escolha uma oportunidade na lista do pipeline ou informe o ID.")
    typed = st.text_input("ID da oportunidade")
    if typed:
        st.query_params["id"] = typed.strip().upper()
        st.rerun()
    st.stop()

try:
    opp = api_client.opportunity(opp_id)
except api_client.ApiError as e:
    st.error(str(e))
    st.stop()

if flash := st.session_state.pop("flash", None):
    st.success(flash)

# ---------- cabeçalho ----------
st.title(opp["account"] or "Conta não informada")
st.markdown(
    f"{band_badge(opp['band'], size='1rem')} &nbsp; **{opp['product']}** · {opp['stage']} · "
    f"ID `{opp['id']}` · {opp['agent']} ({opp['manager']}, {opp['region']})",
    unsafe_allow_html=True,
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Score", f"{opp['score']}/100", border=True)
if opp["stage"] == "Engaging":
    m2.metric("Dias em Engaging", opp["days_engaging"], border=True)
else:
    m2.metric("Estágio", opp["stage"], border=True)
if opp["days_to_stall"] is not None:
    m3.metric("Vira parada em", f"{opp['days_to_stall']} dias", border=True)
elif opp["stalled"]:
    m3.metric("Penalidade (parada)", f"×{opp['multiplier']:g}".replace(".", ","), border=True)
else:
    m3.metric("Engajamento", fmt_date(opp["engage_date"]), border=True)
m4.metric("Preço de lista", money(opp["list_price"]), border=True)

# ---------- por quê / o que fazer ----------
left, right = st.columns(2, gap="large")
with left:
    st.subheader("Por que este score")
    st.markdown(f"`({opp['value_points']} valor + {opp['time_points']} tempo) × {opp['multiplier']:g} = {opp['score']}`".replace(".", ","))
    for line in opp["explanation"]:
        st.markdown(f"- {md(line)}")

with right:
    st.subheader("O que fazer agora")
    rec = opp["recommendation"]
    if rec is None:
        closed = f"Fechada como **{opp['stage']}** em {fmt_date(opp['close_date'])}"
        closed += f" · {money(opp['close_value'])}" if opp["stage"] == "Won" else f" · motivo: {opp['lost_reason']}"
        st.info(md(closed))
    else:
        st.markdown(f"**{md(rec['headline'])}**")
        for step in rec["steps"]:
            st.markdown(f"- {md(step)}")
        if opp["next_step"] or opp["next_step_date"]:
            st.markdown(f"📅 Próximo passo: **{opp['next_step'] or '—'}** em {fmt_date(opp['next_step_date'])}")


# ---------- comandos ----------
def submit(payload: dict, message: str) -> None:
    try:
        api_client.run_command(opp["id"], payload)
    except api_client.ApiError as e:
        st.error(str(e))
        return
    st.session_state["flash"] = message
    st.rerun()


def command_form(cmd: dict) -> None:
    key = cmd["key"]
    st.caption(cmd["help"])
    with st.form(f"form_{key}", clear_on_submit=True, border=False):
        payload = {"command": key}
        if key in ("log_activity", "reengage"):
            payload["kind"] = st.selectbox("Tipo", ACTIVITY_KINDS)
            payload["note"] = st.text_area("O que aconteceu", placeholder="Resumo do contato")
            c1, c2 = st.columns([2, 1])
            payload["next_step"] = c1.text_input("Próximo passo", placeholder="Ex.: enviar proposta revisada")
            payload["next_step_date"] = c2.date_input(
                "Data do próximo passo", value=date.fromisoformat(rec["next_step_default_date"]), format="DD/MM/YYYY"
            ).isoformat()
        elif key == "advance_to_engaging":
            payload["engage_date"] = st.date_input(
                "Data do engajamento", value=date.fromisoformat(opp["reference_date"]), format="DD/MM/YYYY"
            ).isoformat()
        elif key == "mark_won":
            payload["close_value"] = st.number_input("Valor fechado (US$)", min_value=0.0, value=float(opp["list_price"]), step=100.0)
        elif key == "mark_lost":
            payload["reason"] = st.selectbox("Motivo da perda", LOST_REASONS)
            payload["note"] = st.text_area("Observação (opcional)")
        elif key == "close_stalled":
            payload["reason"] = st.text_input("Motivo", value="Parada além do ciclo histórico")
        elif key == "requalify":
            payload["note"] = st.text_area("Por que requalificar", placeholder="Ex.: novo decisor, orçamento para o próximo trimestre")
        elif key == "complete_account":
            payload["account"] = st.text_input("Nome da conta (cliente)")

        if st.form_submit_button(cmd["label"], type="primary" if cmd["primary"] else "secondary"):
            submit({k: v for k, v in payload.items() if v not in (None, "")}, f"{cmd['label']}: feito.")


if opp["commands"]:
    st.subheader("Ações")
    commands = sorted(opp["commands"], key=lambda c: not c["primary"])
    tabs = st.tabs([("★ " if c["primary"] else "") + c["label"] for c in commands])
    for tab, cmd in zip(tabs, commands):
        with tab:
            command_form(cmd)

# ---------- histórico ----------
st.subheader("Histórico de atividades")
if opp["activities"]:
    acts = pd.DataFrame(opp["activities"])
    st.dataframe(
        pd.DataFrame({
            "Quando": pd.to_datetime(acts["created_at"]),
            "Ação": acts["command"].map(COMMAND_LABELS),
            "Tipo": acts["kind"],
            "Nota": acts["note"],
            "Próximo passo": acts["next_step"],
            "Data próximo passo": pd.to_datetime(acts["next_step_date"]),
            "Faixa": acts["band_before"].fillna("—") + " → " + acts["band_after"].fillna("fechada"),
        }),
        hide_index=True,
        column_config={
            "Quando": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
            "Data próximo passo": st.column_config.DateColumn(format="DD/MM/YYYY"),
        },
    )
else:
    st.caption("Nenhuma atividade registrada ainda.")
