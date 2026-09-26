"""Modelo de score — réplica fiel das fórmulas da planilha lead_scoring_pipeline.xlsx.

    Score = (Pontos de valor + Pontos de tempo) × Multiplicador de reciclagem   (0–100)

- Pontos de valor (0–60): preço de lista do produto em escala logarítmica.
- Pontos de tempo (0–40): dias em Engaging até a data de referência, por faixa;
  Prospecting recebe pontuação fixa; acima do limite de ciclo vale 0.
- Multiplicador: só penaliza oportunidades paradas (dias > limite de ciclo).
- Faixas: A/B/C/D pelos cortes de score; R (Reciclar) para as paradas.

Funções puras, sem acesso a banco: fáceis de testar e de reaproveitar.
"""

import math
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from pydantic import BaseModel

BANDS = ("A", "B", "C", "D", "R")


class TimeBand(BaseModel):
    start: int  # dias (inclusive)
    points: int
    rationale: str = ""


class MultiplierBand(BaseModel):
    start: int  # dias (inclusive)
    multiplier: float
    note: str = ""


class BandRule(BaseModel):
    band: str
    min_score: int | None  # None para R (definida por estar parada, não pelo score)
    criterion: str
    action: str


class ScoringParams(BaseModel):
    reference_date: date
    stall_limit_days: int = 138
    max_value_points: int = 60
    prospecting_points: int = 10
    product_prices: dict[str, int]
    time_bands: list[TimeBand]
    multiplier_bands: list[MultiplierBand]
    band_rules: list[BandRule]

    def rule(self, band: str) -> BandRule:
        return next(r for r in self.band_rules if r.band == band)


@dataclass(frozen=True)
class ScoreResult:
    days_engaging: int | None
    value_points: int
    time_points: int
    multiplier: float
    score: int
    stalled: bool
    band: str


def excel_round(x: float) -> int:
    """ROUND do Excel arredonda .5 para longe do zero; round() do Python não."""
    return int(Decimal(str(x)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def value_points(product: str, params: ScoringParams) -> int:
    prices = params.product_prices
    lo, hi = math.log(min(prices.values())), math.log(max(prices.values()))
    return excel_round(params.max_value_points * (math.log(prices[product]) - lo) / (hi - lo))


def _lookup(bands, days: int):
    """Equivalente ao MATCH(..., 1) do Excel: última faixa cujo início ≤ dias."""
    return [b for b in sorted(bands, key=lambda b: b.start) if b.start <= days][-1]


def time_band(days: int, params: ScoringParams) -> TimeBand | None:
    if days > params.stall_limit_days:
        return None
    return _lookup(params.time_bands, days)


def multiplier_band(days: int, params: ScoringParams) -> MultiplierBand:
    return _lookup(params.multiplier_bands, days)


def band_for(score: int, stalled: bool, params: ScoringParams) -> str:
    if stalled:
        return "R"
    for rule in sorted((r for r in params.band_rules if r.min_score is not None), key=lambda r: -r.min_score):
        if score >= rule.min_score:
            return rule.band
    return "D"


def score_opportunity(stage: str, engage_date: date | None, product: str, params: ScoringParams) -> ScoreResult:
    vp = value_points(product, params)
    if stage == "Prospecting" or engage_date is None:
        days, tp, mult, stalled = None, params.prospecting_points, 1.0, False
    else:
        days = (params.reference_date - engage_date).days
        tb = time_band(days, params)
        tp = tb.points if tb else 0
        mult = multiplier_band(days, params).multiplier
        stalled = days > params.stall_limit_days
    score = excel_round((vp + tp) * mult)
    return ScoreResult(days, vp, tp, mult, score, stalled, band_for(score, stalled, params))
