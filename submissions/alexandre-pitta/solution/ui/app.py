"""Ponto de entrada da interface: `streamlit run ui/app.py`."""

import streamlit as st

from filters import keep_filter_state

st.set_page_config(page_title="Pipeline — Priorização", page_icon="🎯", layout="wide")
keep_filter_state()

pages = [
    st.Page("views/pipeline.py", title="Pipeline", icon="📋", default=True),
    st.Page("views/opportunity.py", title="Oportunidade", icon="🔎", url_path="oportunidade"),
    st.Page("views/documentation.py", title="Documentação", icon="📖", url_path="documentacao"),
]
st.navigation(pages).run()
