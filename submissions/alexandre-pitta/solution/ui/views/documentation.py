"""Documentação do modelo de lead scoring (docs/model.md + docs/aplicacao.md)."""

from pathlib import Path

import streamlit as st

from components import md

DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"


@st.cache_data
def load_sections() -> tuple[str, list[tuple[str, str]]]:
    """Separa o documento em introdução e seções de nível 2 (## ...)."""
    text = "\n\n".join((DOCS_DIR / name).read_text(encoding="utf-8") for name in ("model.md", "aplicacao.md"))
    intro, sections, current = [], [], None
    for line in text.splitlines():
        if line.startswith("## "):
            current = (line[3:].strip(), [])
            sections.append(current)
        elif current is None:
            intro.append(line)
        else:
            current[1].append(line)
    return "\n".join(intro), [(title, "\n".join(body).strip().removesuffix("---").strip()) for title, body in sections]


intro, sections = load_sections()

st.sidebar.header("Nesta página")
st.sidebar.markdown("\n".join(f"- [{title}](#secao-{i})" for i, (title, _) in enumerate(sections, 1)))

# Linhas de metadados (**Versão:** ...) precisam de quebra explícita para não virarem um só parágrafo
st.markdown(md(intro.replace("\n---", "").replace("\n**", "  \n**")))
for i, (title, body) in enumerate(sections, 1):
    st.header(title, anchor=f"secao-{i}", divider="gray")
    st.markdown(md(body))
