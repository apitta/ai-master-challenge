"""Filtros do pipeline na barra lateral, em cascata: Regional → Gerente → Vendedor."""

import streamlit as st

import api_client

KEYS = {
    "region": "flt_region",
    "manager": "flt_manager",
    "agent": "flt_agent",
    "product": "flt_product",
    "band": "flt_band",
    "stage": "flt_stage",
    "q": "flt_q",
}


def keep_filter_state() -> None:
    """O Streamlit descarta o estado de widgets de uma página ao trocar de página.
    Reatribuir as chaves no script principal mantém os filtros ao voltar do detalhe."""
    for key in KEYS.values():
        if key in st.session_state:
            st.session_state[key] = st.session_state[key]


def _multiselect(label: str, key: str, options: list[str], **kwargs) -> list[str]:
    # Remove seleções que deixaram de existir nas opções (ex.: gerente de outra regional)
    if key in st.session_state:
        st.session_state[key] = [v for v in st.session_state[key] if v in options]
    return st.sidebar.multiselect(label, options, key=key, placeholder="Todos", **kwargs)


def _clear() -> None:
    for key in KEYS.values():
        st.session_state.pop(key, None)


def sidebar_filters() -> dict:
    opts = api_client.filters()
    team = opts["team"]
    st.sidebar.header("Filtros")

    regions = _multiselect("Regional", KEYS["region"], opts["regions"])
    in_region = [t for t in team if not regions or t["region"] in regions]
    managers = _multiselect("Gerente", KEYS["manager"], sorted({t["manager"] for t in in_region}))
    in_team = [t for t in in_region if not managers or t["manager"] in managers]
    agents = _multiselect("Vendedor", KEYS["agent"], sorted({t["agent"] for t in in_team}))
    products = _multiselect("Produto", KEYS["product"], opts["products"])

    st.sidebar.divider()
    bands = _multiselect("Faixa", KEYS["band"], opts["bands"])
    stages = _multiselect("Estágio", KEYS["stage"], ["Engaging", "Prospecting"])
    q = st.sidebar.text_input("Buscar conta ou ID", key=KEYS["q"])
    st.sidebar.button("Limpar filtros", on_click=_clear, width="stretch")

    return {
        "region": regions, "manager": managers, "agent": agents, "product": products,
        "band": bands, "stage": stages, "q": q or None,
    }
