"""API FastAPI — camada de serviço consumida pela interface Streamlit.

Documentação interativa em /docs.
"""

from collections.abc import Iterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app import services
from app.config import Settings, get_settings
from app.db import Database
from app.schemas import CommandIn, FilterOptions, OpportunityDetail, OpportunityOut, Summary
from app.seed import seed_if_empty


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        db = Database(settings.database_url)
        db.create_all()
        with db.session_factory() as session:
            seed_if_empty(session, settings.seed_file)
            params = services.load_params(session, settings.reference_date)
            services.rescore_all(session, params)
            app.state.stats = services.history_stats(session, params)
        app.state.db, app.state.params = db, params
        yield
        db.engine.dispose()

    app = FastAPI(title="Pipeline — Priorização de Oportunidades", version="0.1.0", lifespan=lifespan)

    def get_session(request: Request) -> Iterator[Session]:
        yield from request.app.state.db.session()

    def pipeline_filter(
        agent: list[str] = Query(default=[]),
        manager: list[str] = Query(default=[]),
        region: list[str] = Query(default=[]),
        product: list[str] = Query(default=[]),
        band: list[str] = Query(default=[]),
        stage: list[str] = Query(default=[]),
        q: str | None = None,
        include_closed: bool = False,
    ) -> services.PipelineFilter:
        return services.PipelineFilter(agent, manager, region, product, band, stage, q, include_closed)

    @app.get("/health")
    def health(request: Request):
        return {"status": "ok", "reference_date": request.app.state.params.reference_date}

    @app.get("/filters", response_model=FilterOptions)
    def filters(session: Session = Depends(get_session)):
        return services.filter_options(session)

    @app.get("/opportunities", response_model=list[OpportunityOut])
    def list_opportunities(
        request: Request, f: services.PipelineFilter = Depends(pipeline_filter), session: Session = Depends(get_session)
    ):
        params = request.app.state.params
        return [services.to_out(o, params) for o in services.query_opportunities(session, f)]

    @app.get("/summary", response_model=Summary)
    def summary(
        request: Request, f: services.PipelineFilter = Depends(pipeline_filter), session: Session = Depends(get_session)
    ):
        return services.summary(session, f, request.app.state.params)

    @app.get("/opportunities/{opp_id}", response_model=OpportunityDetail)
    def get_opportunity(opp_id: str, request: Request, session: Session = Depends(get_session)):
        try:
            return services.detail(session, opp_id, request.app.state.params, request.app.state.stats)
        except services.NotFound:
            raise HTTPException(404, f"Oportunidade {opp_id} não encontrada")

    @app.post("/opportunities/{opp_id}/commands", response_model=OpportunityDetail)
    def run_command(opp_id: str, cmd: CommandIn, request: Request, session: Session = Depends(get_session)):
        try:
            return services.execute_command(session, opp_id, cmd, request.app.state.params, request.app.state.stats)
        except services.NotFound:
            raise HTTPException(404, f"Oportunidade {opp_id} não encontrada")
        except services.CommandError as e:
            raise HTTPException(400, str(e))

    @app.get("/parameters")
    def parameters(request: Request):
        return request.app.state.params

    return app


app = create_app()
