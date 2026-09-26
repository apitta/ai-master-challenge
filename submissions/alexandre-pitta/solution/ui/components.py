"""Elementos visuais compartilhados.

Faixas A→D são ordinais (prioridade): rampa de um só tom de azul, do escuro ao claro.
R é um estado (parada), não um nível: usa a cor de status "serious" com ícone.
A cor nunca carrega o significado sozinha — a letra da faixa sempre aparece.
"""

from datetime import date

import streamlit as st

BAND_STYLE = {
    "A": {"bg": "#184f95", "fg": "#ffffff", "icon": "🔥", "name": "Prioridade máxima"},
    "B": {"bg": "#256abf", "fg": "#ffffff", "icon": "▲", "name": "Cadência padrão"},
    "C": {"bg": "#5598e7", "fg": "#0b0b0b", "icon": "●", "name": "Qualificar"},
    "D": {"bg": "#86b6ef", "fg": "#0b0b0b", "icon": "▽", "name": "Automatizar"},
    "R": {"bg": "#ec835a", "fg": "#0b0b0b", "icon": "♻", "name": "Reciclar"},
}
CLOSED_STYLE = {"bg": "#52514e", "fg": "#ffffff", "icon": "■", "name": "Fechada"}


def band_style(band: str | None) -> dict:
    return BAND_STYLE.get(band or "", CLOSED_STYLE)


def band_badge(band: str | None, label: str | None = None, size: str = "0.9rem") -> str:
    s = band_style(band)
    text = label or (f"{s['icon']} Faixa {band}" if band else f"{s['icon']} Fechada")
    return (
        f"<span style='background:{s['bg']};color:{s['fg']};padding:0.15em 0.6em;border-radius:6px;"
        f"font-weight:600;font-size:{size};white-space:nowrap'>{text}</span>"
    )


def band_cell_css(band: str | None) -> str:
    s = band_style(band)
    return f"background-color:{s['bg']};color:{s['fg']};font-weight:600;text-align:center"


def num(value: float | int) -> str:
    return f"{value:,.0f}".replace(",", ".")


def money(value: float | int | None, compact: bool = False) -> str:
    if value is None:
        return "—"
    if compact and abs(value) >= 1_000_000:
        return f"US$ {value / 1_000_000:.2f} mi".replace(".", ",")
    return f"US$ {num(value)}"


def md(text: str) -> str:
    """Escapa '$': no st.markdown, texto entre dois '$' vira fórmula LaTeX."""
    return text.replace("$", "\\$")


def fmt_date(value: str | date | None) -> str:
    if not value:
        return "—"
    d = date.fromisoformat(value) if isinstance(value, str) else value
    return d.strftime("%d/%m/%Y")
