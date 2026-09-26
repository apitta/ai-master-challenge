"""Regras de negócio: consulta do pipeline, detalhe explicado e execução de comandos."""

import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app import playbook
from app.models import OPEN_STAGES, Activity, ClosedDeal, Opportunity, Setting
from app.schemas import (
    BandSummary, CommandIn, CommandOut, FilterOptions, OpportunityDetail, OpportunityOut,
    RecommendationOut, Summary, TeamMember,
)
from app.scoring import BANDS, ScoringParams, score_opportunity
from app.seed import PARAMS_KEY


class NotFound(Exception):
    pass


class CommandError(Exception):
    pass


@dataclass
class PipelineFilter:
    agents: list[str] = field(default_factory=list)
    managers: list[str] = field(default_factory=list)
    regions: list[str] = field(default_factory=list)
    products: list[str] = field(default_factory=list)
    bands: list[str] = field(default_factory=list)
    stages: list[str] = field(default_factory=list)
    search: str | None = None
    include_closed: bool = False


# ---------- parâmetros e score ----------

def load_params(session: Session, reference_date: date | None = None) -> ScoringParams:
    params = ScoringParams.model_validate(session.get(Setting, PARAMS_KEY).value)
    return params.model_copy(update={"reference_date": reference_date}) if reference_date else params


def apply_score(opp: Opportunity, params: ScoringParams) -> None:
    r = score_opportunity(opp.stage, opp.engage_date, opp.product_name, params)
    opp.days_engaging, opp.value_points, opp.time_points = r.days_engaging, r.value_points, r.time_points
    opp.multiplier, opp.score, opp.stalled = r.multiplier, r.score, r.stalled
    opp.band = r.band if opp.is_open else None


def rescore_all(session: Session, params: ScoringParams) -> None:
    for opp in session.scalars(select(Opportunity)):
        apply_score(opp, params)
    session.commit()


def history_stats(session: Session, params: ScoringParams) -> playbook.HistoryStats:
    deals = session.scalars(select(ClosedDeal)).all()
    starts = sorted(b.start for b in params.time_bands)
    ends = [s - 1 for s in starts[1:]] + [params.stall_limit_days]
    by_band = {}
    for start, end in zip(starts, ends):
        sample = [d.won for d in deals if start <= d.cycle_days <= end]
        by_band[start] = (sum(sample) / len(sample) if sample else 0.0, len(sample))
    won_cycles = defaultdict(list)
    for d in deals:
        if d.won:
            won_cycles[d.product_name].append(d.cycle_days)
    return playbook.HistoryStats(
        overall_win_rate=sum(d.won for d in deals) / len(deals) if deals else 0.0,
        max_cycle_days=max((d.cycle_days for d in deals), default=0),
        win_rate_by_time_band=by_band,
        median_won_cycle_by_product={p: round(statistics.median(c)) for p, c in won_cycles.items()},
    )


# ---------- consultas ----------

def _band_order():
    return case({b: i for i, b in enumerate(BANDS)}, value=Opportunity.band, else_=len(BANDS))


def query_opportunities(session: Session, f: PipelineFilter) -> list[Opportunity]:
    stmt = select(Opportunity)
    for column, values in [
        (Opportunity.agent, f.agents), (Opportunity.manager, f.managers), (Opportunity.region, f.regions),
        (Opportunity.product_name, f.products), (Opportunity.band, f.bands), (Opportunity.stage, f.stages),
    ]:
        if values:
            stmt = stmt.where(column.in_(values))
    if not f.include_closed:
        stmt = stmt.where(Opportunity.stage.in_(OPEN_STAGES))
    if f.search:
        like = f"%{f.search.strip()}%"
        stmt = stmt.where(Opportunity.id.ilike(like) | Opportunity.account.ilike(like))
    stmt = stmt.order_by(_band_order(), Opportunity.score.desc(), Opportunity.days_engaging.desc(), Opportunity.id)
    return list(session.scalars(stmt))


def to_out(opp: Opportunity, params: ScoringParams) -> OpportunityOut:
    return OpportunityOut(
        id=opp.id, agent=opp.agent, manager=opp.manager, region=opp.region,
        product=opp.product_name, series=opp.product.series, list_price=opp.product.list_price,
        account=opp.account, stage=opp.stage, engage_date=opp.engage_date, close_date=opp.close_date,
        close_value=opp.close_value, lost_reason=opp.lost_reason, days_engaging=opp.days_engaging,
        days_to_stall=playbook.days_to_stall(opp, params), value_points=opp.value_points,
        time_points=opp.time_points, multiplier=opp.multiplier, score=opp.score, stalled=opp.stalled,
        band=opp.band, action=params.rule(opp.band).action if opp.band else None,
        next_step=opp.next_step, next_step_date=opp.next_step_date,
    )


def get_opportunity(session: Session, opp_id: str) -> Opportunity:
    opp = session.get(Opportunity, opp_id)
    if opp is None:
        raise NotFound(opp_id)
    return opp


def detail(session: Session, opp_id: str, params: ScoringParams, stats: playbook.HistoryStats) -> OpportunityDetail:
    opp = get_opportunity(session, opp_id)
    base = to_out(opp, params).model_dump()
    rec, commands = None, []
    if opp.is_open:
        r = playbook.recommend(opp, params, stats)
        rec = RecommendationOut(
            headline=r.headline, steps=r.steps,
            next_step_default_date=playbook.default_next_step_date(opp, params),
        )
        commands = [
            CommandOut(**vars(playbook.COMMANDS[k]), primary=k == r.primary_command)
            for k in r.commands
        ]
    return OpportunityDetail(
        **base,
        explanation=playbook.explain(opp, params, stats),
        recommendation=rec,
        commands=commands,
        activities=opp.activities,
        reference_date=params.reference_date,
    )


def filter_options(session: Session) -> FilterOptions:
    team = session.execute(
        select(Opportunity.agent, Opportunity.manager, Opportunity.region).distinct()
        .order_by(Opportunity.region, Opportunity.manager, Opportunity.agent)
    ).all()
    products = session.scalars(select(Opportunity.product_name).distinct().order_by(Opportunity.product_name))
    return FilterOptions(
        regions=sorted({t.region for t in team}),
        managers=sorted({t.manager for t in team}),
        agents=sorted({t.agent for t in team}),
        products=list(products),
        team=[TeamMember(agent=t.agent, manager=t.manager, region=t.region) for t in team],
        bands=list(BANDS),
    )


def summary(session: Session, f: PipelineFilter, params: ScoringParams) -> Summary:
    opps = query_opportunities(session, PipelineFilter(**{**vars(f), "include_closed": False}))
    bands = []
    for band in BANDS:
        subset = [o for o in opps if o.band == band]
        bands.append(BandSummary(
            band=band, action=params.rule(band).action, count=len(subset),
            pipeline_value=sum(o.product.list_price for o in subset),
            missing_account=sum(1 for o in subset if not o.account),
        ))
    soon = [o for o in opps if (d := playbook.days_to_stall(o, params)) is not None and d <= 30]
    return Summary(
        reference_date=params.reference_date, total=len(opps),
        pipeline_value=sum(b.pipeline_value for b in bands), stalling_soon=len(soon), bands=bands,
    )


# ---------- comandos ----------

def execute_command(
    session: Session, opp_id: str, cmd: CommandIn, params: ScoringParams, stats: playbook.HistoryStats
) -> OpportunityDetail:
    opp = get_opportunity(session, opp_id)
    if not opp.is_open:
        raise CommandError(f"Oportunidade {opp_id} já está fechada ({opp.stage}).")
    allowed = playbook.recommend(opp, params, stats).commands
    if cmd.command not in allowed:
        raise CommandError(f"Comando '{cmd.command}' não se aplica a esta oportunidade (faixa {opp.band}).")

    band_before = opp.band
    today = params.reference_date
    note = cmd.note

    match cmd.command:
        case "log_activity" | "reengage":
            if not (cmd.note or cmd.next_step):
                raise CommandError("Descreva a atividade ou o próximo passo.")
            if cmd.next_step or cmd.next_step_date:
                opp.next_step = cmd.next_step or opp.next_step
                opp.next_step_date = cmd.next_step_date or playbook.default_next_step_date(opp, params)
        case "advance_to_engaging":
            opp.stage, opp.engage_date = "Engaging", cmd.engage_date or today
        case "mark_won":
            opp.stage, opp.close_date = "Won", today
            opp.close_value = cmd.close_value if cmd.close_value is not None else opp.product.list_price
        case "mark_lost" | "close_stalled":
            reason = cmd.reason or ("Parada além do ciclo histórico" if cmd.command == "close_stalled" else None)
            if not reason:
                raise CommandError("Informe o motivo da perda.")
            opp.stage, opp.close_date, opp.close_value, opp.lost_reason = "Lost", today, 0.0, reason
            note = note or reason
        case "requalify":
            opp.stage, opp.engage_date = "Prospecting", None
        case "complete_account":
            if not (cmd.account and cmd.account.strip()):
                raise CommandError("Informe o nome da conta.")
            opp.account = cmd.account.strip()

    if not opp.is_open:
        opp.next_step = opp.next_step_date = None
    apply_score(opp, params)
    session.add(Activity(
        opportunity_id=opp.id, command=cmd.command, kind=cmd.kind, note=note,
        next_step=cmd.next_step, next_step_date=opp.next_step_date if cmd.command in ("log_activity", "reengage") else None,
        band_before=band_before, band_after=opp.band,
    ))
    session.commit()
    session.refresh(opp)
    return detail(session, opp_id, params, stats)
