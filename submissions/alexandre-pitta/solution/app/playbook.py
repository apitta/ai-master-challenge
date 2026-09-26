"""Tradução do score em explicação ("por que") e ação ("o que fazer agora").

Regras simples e explícitas: cada faixa tem uma recomendação principal, um prazo
para o próximo passo e um conjunto de comandos disponíveis na tela de detalhe.
"""

from dataclasses import dataclass, field
from datetime import timedelta

from app.models import Opportunity
from app.scoring import ScoringParams, multiplier_band, time_band


@dataclass(frozen=True)
class Command:
    key: str
    label: str
    help: str


COMMANDS = {
    c.key: c
    for c in [
        Command("log_activity", "Registrar atividade", "Ligação, e-mail ou reunião e o próximo passo combinado."),
        Command("advance_to_engaging", "Mover para Engaging", "O cliente engajou: inicia o ciclo e a contagem de dias."),
        Command("mark_won", "Marcar como ganha", "Fecha a oportunidade como ganha e registra o valor."),
        Command("mark_lost", "Marcar como perdida", "Fecha a oportunidade como perdida e registra o motivo."),
        Command("reengage", "Reengajar", "Registra a tentativa de retomada e agenda o follow-up."),
        Command("requalify", "Requalificar", "Volta para Prospecting; o ciclo recomeça quando o cliente reengajar."),
        Command("close_stalled", "Encerrar", "Encerra como perdida: parada além do ciclo histórico."),
        Command("complete_account", "Completar cadastro", "Informa a conta (cliente) da oportunidade."),
    ]
}


def fmt_int(value: int) -> str:
    """Milhar no padrão pt-BR: 26768 -> 26.768."""
    return f"{value:,}".replace(",", ".")


def fmt_mult(value: float) -> str:
    return f"{value:g}".replace(".", ",")


# Prazo padrão (dias) para o próximo passo, por faixa
NEXT_STEP_DAYS = {"A": 2, "B": 7, "C": 14, "D": 30, "R": 7}


@dataclass
class HistoryStats:
    """Contexto do histórico de negócios fechados (aba Histórico)."""

    overall_win_rate: float
    max_cycle_days: int
    win_rate_by_time_band: dict[int, tuple[float, int]]  # início da faixa -> (taxa, nº negócios)
    median_won_cycle_by_product: dict[str, int] = field(default_factory=dict)


@dataclass
class Recommendation:
    headline: str
    steps: list[str]
    primary_command: str
    commands: list[str]
    next_step_days: int


def days_to_stall(opp: Opportunity, params: ScoringParams) -> int | None:
    if opp.stage != "Engaging" or opp.days_engaging is None or opp.stalled:
        return None
    return params.stall_limit_days - opp.days_engaging


def explain(opp: Opportunity, params: ScoringParams, stats: HistoryStats) -> list[str]:
    prices = params.product_prices
    cheapest, priciest = min(prices, key=prices.get), max(prices, key=prices.get)
    lines = [
        f"**Valor: {opp.value_points}/{params.max_value_points} pts.** {opp.product_name} tem preço de lista de "
        f"US$ {fmt_int(prices[opp.product_name])}. A escala é logarítmica: {cheapest} (US$ {fmt_int(prices[cheapest])}) vale 0 "
        f"e {priciest} (US$ {fmt_int(prices[priciest])}) vale {params.max_value_points}."
    ]
    max_time = max(b.points for b in params.time_bands)
    if opp.stage == "Prospecting" or opp.days_engaging is None:
        lines.append(
            f"**Tempo: {opp.time_points}/{max_time} pts.** Ainda em Prospecting, sem data de engajamento: "
            "recebe a pontuação fixa de prospecção."
        )
    elif opp.stalled:
        lines.append(
            f"**Tempo: 0/{max_time} pts.** {opp.days_engaging} dias em Engaging, acima do limite de "
            f"{params.stall_limit_days} dias. Nenhum negócio do histórico fechou com ciclo maior que "
            f"{stats.max_cycle_days} dias."
        )
        mb = multiplier_band(opp.days_engaging, params)
        lines.append(
            f"**Multiplicador: ×{fmt_mult(opp.multiplier)}** ({mb.note.lower()}). Parada há "
            f"{opp.days_engaging - params.stall_limit_days} dias além do limite; quanto mais tempo parada, maior a penalidade."
        )
    else:
        tb = time_band(opp.days_engaging, params)
        rate, n = stats.win_rate_by_time_band.get(tb.start, (0.0, 0))
        lines.append(
            f"**Tempo: {opp.time_points}/{max_time} pts.** {opp.days_engaging} dias em Engaging: "
            f"fase \"{tb.rationale.lower()}\". No histórico, {rate:.0%} dos {fmt_int(n)} negócios que fecharam "
            f"nessa fase de ciclo foram ganhos (média geral: {stats.overall_win_rate:.0%})."
        )
    return lines


def recommend(opp: Opportunity, params: ScoringParams, stats: HistoryStats) -> Recommendation:
    band = opp.band
    headline = params.rule(band).action
    price = params.product_prices[opp.product_name]
    median_cycle = stats.median_won_cycle_by_product.get(opp.product_name)
    closing = ["mark_won", "mark_lost"]

    if band == "R":
        mb = multiplier_band(opp.days_engaging, params)
        if mb.multiplier >= 0.6:
            primary, steps = "reengage", [
                "Contato de retomada nesta semana: confirme se o projeto e o orçamento continuam de pé.",
                "Se houver novo interesse, registre o próximo passo com data; sem resposta em 2 tentativas, requalifique.",
            ]
        elif mb.multiplier >= 0.4:
            primary, steps = "requalify", [
                "Refaça a qualificação: dor, decisor, orçamento e prazo mudaram desde o engajamento?",
                "Se ainda houver fit, requalifique (volta para Prospecting e o ciclo recomeça limpo).",
            ]
        else:
            primary, steps = "close_stalled", [
                f"Mais de {mb.start - 1} dias em Engaging: encerre e libere o pipeline para oportunidades vivas.",
                "Se houver sinal concreto de compra, requalifique em vez de encerrar.",
            ]
        commands = ["reengage", "requalify", "close_stalled", "log_activity"]
    elif opp.stage == "Prospecting":
        primary = "advance_to_engaging"
        steps = [
            "Qualifique: confirme dor, decisor, orçamento e prazo.",
            "Quando o cliente engajar, mova para Engaging para iniciar a contagem do ciclo.",
        ]
        if band in ("A", "B"):
            steps.insert(0, f"Produto de alto valor (US$ {fmt_int(price)}): priorize a primeira reunião.")
        commands = ["advance_to_engaging", "log_activity", "mark_lost"]
    else:
        primary = "log_activity"
        steps = {
            "A": [
                "Agende o próximo passo concreto (proposta, demo ou reunião com decisor) em até 48h.",
                "Confirme o processo de decisão e quem assina; antecipe objeções de preço.",
            ],
            "B": [
                "Mantenha contato semanal com um próximo passo sempre agendado.",
                "Mapeie o que falta para a oportunidade avançar para a fase de decisão.",
            ],
            "C": [
                "Qualifique antes de investir tempo: há decisor, orçamento e prazo definidos?",
                "Use cadência leve (e-mail e conteúdo) e reavalie a cada duas semanas.",
            ],
            "D": [
                "Baixo valor: trate em lote ou com cadência automatizada (e-mail, material padrão).",
                "Não deixe roubar tempo das faixas A e B.",
            ],
        }[band]
        commands = ["log_activity", *closing]

    if band == "R":
        headline = f"{headline}. Recomendado agora: {COMMANDS[primary].label.lower()}."
    remaining = days_to_stall(opp, params)
    if remaining is not None and remaining <= 30:
        steps.insert(0, f"⚠️ Faltam {remaining} dias para virar parada (limite de {params.stall_limit_days} dias). Busque a decisão agora.")
    if median_cycle and opp.stage == "Engaging" and not opp.stalled:
        steps.append(f"Referência: negócios ganhos de {opp.product_name} fecham com ciclo mediano de {median_cycle} dias.")
    if not opp.account:
        steps.append("Cadastro incompleto: informe a conta do cliente.")
        commands.append("complete_account")

    return Recommendation(headline, steps, primary, commands, NEXT_STEP_DAYS[band])


def default_next_step_date(opp: Opportunity, params: ScoringParams):
    return params.reference_date + timedelta(days=NEXT_STEP_DAYS.get(opp.band or "D", 7))
