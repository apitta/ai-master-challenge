"""Modelo de dados.

Os campos de score em Opportunity são materializados (recalculados a cada mudança
e no startup) para permitir filtrar, ordenar e agregar direto no banco.
"""

from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

OPEN_STAGES = ("Prospecting", "Engaging")


class Product(Base):
    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(50), primary_key=True)
    series: Mapped[str] = mapped_column(String(20))
    list_price: Mapped[int] = mapped_column(Integer)


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    agent: Mapped[str] = mapped_column(String(80), index=True)
    manager: Mapped[str] = mapped_column(String(80), index=True)
    region: Mapped[str] = mapped_column(String(40), index=True)
    product_name: Mapped[str] = mapped_column(ForeignKey("products.name"), index=True)
    account: Mapped[str | None] = mapped_column(String(120))
    stage: Mapped[str] = mapped_column(String(20), index=True)
    engage_date: Mapped[date | None] = mapped_column(Date)
    close_date: Mapped[date | None] = mapped_column(Date)
    close_value: Mapped[float | None] = mapped_column(Float)
    lost_reason: Mapped[str | None] = mapped_column(String(200))
    next_step: Mapped[str | None] = mapped_column(String(200))
    next_step_date: Mapped[date | None] = mapped_column(Date)

    # Score materializado (ver app.scoring)
    days_engaging: Mapped[int | None] = mapped_column(Integer)
    value_points: Mapped[int] = mapped_column(Integer, default=0)
    time_points: Mapped[int] = mapped_column(Integer, default=0)
    multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    stalled: Mapped[bool] = mapped_column(default=False)
    band: Mapped[str | None] = mapped_column(String(1), index=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    product: Mapped[Product] = relationship(lazy="joined")
    activities: Mapped[list["Activity"]] = relationship(
        back_populates="opportunity", order_by="desc(Activity.id)", cascade="all, delete-orphan"
    )

    @property
    def is_open(self) -> bool:
        return self.stage in OPEN_STAGES


class Activity(Base):
    """Registro de cada comando executado sobre uma oportunidade (trilha de auditoria)."""

    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    opportunity_id: Mapped[str] = mapped_column(ForeignKey("opportunities.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    command: Mapped[str] = mapped_column(String(40))
    kind: Mapped[str | None] = mapped_column(String(40))
    note: Mapped[str | None] = mapped_column(Text)
    next_step: Mapped[str | None] = mapped_column(String(200))
    next_step_date: Mapped[date | None] = mapped_column(Date)
    band_before: Mapped[str | None] = mapped_column(String(1))
    band_after: Mapped[str | None] = mapped_column(String(1))

    opportunity: Mapped[Opportunity] = relationship(back_populates="activities")


class ClosedDeal(Base):
    """Aba Histórico: negócios Won/Lost, base das taxas de ganho por ciclo."""

    __tablename__ = "closed_deals"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    agent: Mapped[str] = mapped_column(String(80), index=True)
    product_name: Mapped[str] = mapped_column(String(50), index=True)
    account: Mapped[str | None] = mapped_column(String(120))
    stage: Mapped[str] = mapped_column(String(10))
    engage_date: Mapped[date] = mapped_column(Date)
    close_date: Mapped[date] = mapped_column(Date)
    cycle_days: Mapped[int] = mapped_column(Integer)
    won: Mapped[bool] = mapped_column()


class Setting(Base):
    """Parâmetros do modelo (aba Parâmetros), guardados como JSON."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)
