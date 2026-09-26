"""Carga inicial a partir da planilha.

Lê apenas as células de entrada (dados e premissas editáveis) — nunca os resultados
das fórmulas. O score é sempre recalculado por app.scoring, então a planilha e a
aplicação não podem divergir silenciosamente (ver tests/test_scoring.py).
"""

from datetime import date, datetime
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ClosedDeal, Opportunity, Product, Setting
from app.scoring import BandRule, MultiplierBand, ScoringParams, TimeBand

PARAMS_KEY = "scoring_params"


def _as_date(value) -> date | None:
    if value is None or value == "":
        return None
    return value.date() if isinstance(value, datetime) else value


def _rows(ws: Worksheet, first: int, last: int) -> list[tuple]:
    return [tuple(c.value for c in row) for row in ws.iter_rows(min_row=first, max_row=last)]


def read_params(ws: Worksheet, products: list[tuple]) -> ScoringParams:
    """Aba Parâmetros. Células com fórmula (ex.: A33 = B6+1) são derivadas aqui."""
    stall_limit = int(ws["B6"].value)
    time_bands = [
        TimeBand(start=int(start), points=int(points), rationale=rationale or "")
        for start, _end, points, _rate, _n, rationale in _rows(ws, 24, 26)
    ]
    multiplier_notes = [ws[f"D{r}"].value for r in range(32, 36)]
    multiplier_starts = [0, stall_limit + 1, int(ws["A34"].value), int(ws["A35"].value)]
    multiplier_bands = [
        MultiplierBand(start=start, multiplier=float(ws[f"C{r}"].value), note=note or "")
        for start, r, note in zip(multiplier_starts, range(32, 36), multiplier_notes)
    ]
    band_rules = [
        BandRule(
            band=band,
            min_score=int(min_score) if isinstance(min_score, (int, float)) else None,
            criterion=criterion,
            action=action,
        )
        for band, min_score, criterion, action, *_ in _rows(ws, 39, 43)
    ]
    return ScoringParams(
        reference_date=_as_date(ws["B5"].value),
        stall_limit_days=stall_limit,
        max_value_points=int(ws["B8"].value),
        prospecting_points=int(ws["B9"].value),
        product_prices={name: int(price) for name, _series, price in products},
        time_bands=time_bands,
        multiplier_bands=multiplier_bands,
        band_rules=band_rules,
    )


def read_workbook(path: Path) -> dict:
    wb = load_workbook(path, read_only=False)  # read_only não expõe acesso por coordenada ("B5")
    params_ws = wb["Parâmetros"]
    products = [r[:3] for r in _rows(params_ws, 13, 19)]

    pipeline_ws = wb["Pipeline"]
    opportunities = [
        dict(
            id=r[0], agent=r[1], manager=r[2], region=r[3], product_name=r[4],
            account=r[5] or None, stage=r[6], engage_date=_as_date(r[7]),
        )
        for r in _rows(pipeline_ws, 2, pipeline_ws.max_row)
        if r[0]
    ]

    history_ws = wb["Histórico"]
    closed = []
    for r in _rows(history_ws, 2, history_ws.max_row):
        if not r[0]:
            continue
        engage, close = _as_date(r[5]), _as_date(r[6])
        closed.append(dict(
            id=r[0], agent=r[1], product_name=r[2], account=r[3], stage=r[4],
            engage_date=engage, close_date=close, cycle_days=(close - engage).days, won=r[4] == "Won",
        ))

    return dict(
        params=read_params(params_ws, products),
        products=[dict(name=n, series=s, list_price=int(p)) for n, s, p in products],
        opportunities=opportunities,
        closed_deals=closed,
    )


def seed_if_empty(session: Session, path: Path) -> bool:
    """Popula o banco na primeira execução. Com banco em disco, preserva o estado existente."""
    if session.scalar(select(func.count()).select_from(Opportunity)):
        return False
    data = read_workbook(path)
    session.add(Setting(key=PARAMS_KEY, value=data["params"].model_dump(mode="json")))
    session.add_all(Product(**p) for p in data["products"])
    session.flush()
    session.add_all(Opportunity(**o) for o in data["opportunities"])
    session.add_all(ClosedDeal(**c) for c in data["closed_deals"])
    session.commit()
    return True
