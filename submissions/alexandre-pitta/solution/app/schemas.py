"""Contratos da API (entrada e saída)."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CommandKey = Literal[
    "log_activity", "advance_to_engaging", "mark_won", "mark_lost",
    "reengage", "requalify", "close_stalled", "complete_account",
]


class OpportunityOut(BaseModel):
    id: str
    agent: str
    manager: str
    region: str
    product: str
    series: str
    list_price: int
    account: str | None
    stage: str
    engage_date: date | None
    close_date: date | None
    close_value: float | None
    lost_reason: str | None
    days_engaging: int | None
    days_to_stall: int | None
    value_points: int
    time_points: int
    multiplier: float
    score: int
    stalled: bool
    band: str | None
    action: str | None
    next_step: str | None
    next_step_date: date | None


class CommandOut(BaseModel):
    key: str
    label: str
    help: str
    primary: bool


class RecommendationOut(BaseModel):
    headline: str
    steps: list[str]
    next_step_default_date: date


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    command: str
    kind: str | None
    note: str | None
    next_step: str | None
    next_step_date: date | None
    band_before: str | None
    band_after: str | None


class OpportunityDetail(OpportunityOut):
    explanation: list[str]
    recommendation: RecommendationOut | None
    commands: list[CommandOut]
    activities: list[ActivityOut]
    reference_date: date


class CommandIn(BaseModel):
    command: CommandKey
    kind: str | None = Field(None, description="Ligação, E-mail, Reunião, Nota…")
    note: str | None = None
    next_step: str | None = None
    next_step_date: date | None = None
    engage_date: date | None = None
    close_value: float | None = Field(None, ge=0)
    reason: str | None = None
    account: str | None = None


class TeamMember(BaseModel):
    agent: str
    manager: str
    region: str


class FilterOptions(BaseModel):
    regions: list[str]
    managers: list[str]
    agents: list[str]
    products: list[str]
    team: list[TeamMember]
    bands: list[str]


class BandSummary(BaseModel):
    band: str
    action: str
    count: int
    pipeline_value: int
    missing_account: int


class Summary(BaseModel):
    reference_date: date
    total: int
    pipeline_value: int
    stalling_soon: int
    bands: list[BandSummary]
