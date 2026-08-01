"""Pydantic request/response schemas. This is the only place dollars (as
seen over the API) convert to integer cents (as used internally) and back."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.services.settle import (
    Breakdown,
    Player,
    ReconciliationFailure,
    SettlementSuccess,
)

CENTS_PER_DOLLAR = 100


def _dollars_to_cents(amount: Decimal) -> int:
    return int(amount * CENTS_PER_DOLLAR)


def _cents_to_dollars(cents: int) -> float:
    # float, not Decimal: this feeds JSON response fields, and Pydantic
    # serializes Decimal as a JSON string rather than a bare number, which
    # doesn't match the PRD's response shape (plain numeric values).
    return float((Decimal(cents) / CENTS_PER_DOLLAR).quantize(Decimal("0.01")))


def _validate_exact_cents(value: Decimal) -> Decimal:
    if value.quantize(Decimal("0.01")) != value:
        raise ValueError("must be a dollar amount with at most 2 decimal places")
    return value


class PlayerInput(BaseModel):
    name: str = Field(min_length=1)
    buy_in: Decimal = Field(ge=0)
    final_balance: Decimal

    @field_validator("buy_in", "final_balance")
    @classmethod
    def exact_cents(cls, value: Decimal) -> Decimal:
        return _validate_exact_cents(value)


class SettlementRequest(BaseModel):
    players: list[PlayerInput] = Field(min_length=2)
    resolve_discrepancy: bool = False

    @field_validator("players")
    @classmethod
    def unique_names(cls, players: list[PlayerInput]) -> list[PlayerInput]:
        names = [p.name for p in players]
        if len(names) != len(set(names)):
            duplicates = sorted({name for name in names if names.count(name) > 1})
            raise ValueError(
                "Duplicate player name(s): "
                f"{', '.join(duplicates)}. Each player needs a unique name."
            )
        return players

    def to_domain_players(self) -> list[Player]:
        return [
            Player(
                name=p.name,
                buy_in=_dollars_to_cents(p.buy_in),
                final_balance=_dollars_to_cents(p.final_balance),
            )
            for p in self.players
        ]


class NetOut(BaseModel):
    name: str
    net: float


class TransactionOut(BaseModel):
    from_player: str = Field(serialization_alias="from")
    to: str
    amount: float


class DebtorCreditorOut(BaseModel):
    name: str
    amount: float


class RoundingAdjustmentOut(BaseModel):
    player: str
    leftover_cents: int
    reason: str


class DiscrepancyAdjustmentOut(BaseModel):
    name: str
    adjustment: float


class DiscrepancyResolutionOut(BaseModel):
    strategy: str
    delta: float
    adjustments: list[DiscrepancyAdjustmentOut]
    excluded_players: list[str]


class BreakdownOut(BaseModel):
    debtors_sorted: list[DebtorCreditorOut]
    creditors_sorted: list[DebtorCreditorOut]
    match_trace: list[str]
    rounding_adjustment: RoundingAdjustmentOut | None
    discrepancy_resolution: DiscrepancyResolutionOut | None


class SettlementSuccessOut(BaseModel):
    nets: list[NetOut]
    transactions: list[TransactionOut]
    breakdown: BreakdownOut


class ReconciliationFailureOut(BaseModel):
    error: str = "nets_do_not_reconcile"
    total_buy_ins: float
    total_final_balances: float
    delta: float
    message: str
    resolvable: bool


def _breakdown_to_response(breakdown: Breakdown) -> BreakdownOut:
    rounding_adjustment = breakdown.rounding_adjustment
    discrepancy_resolution = breakdown.discrepancy_resolution
    return BreakdownOut(
        debtors_sorted=[
            DebtorCreditorOut(name=d.name, amount=_cents_to_dollars(d.amount))
            for d in breakdown.debtors_sorted
        ],
        creditors_sorted=[
            DebtorCreditorOut(name=c.name, amount=_cents_to_dollars(c.amount))
            for c in breakdown.creditors_sorted
        ],
        match_trace=breakdown.match_trace,
        rounding_adjustment=(
            RoundingAdjustmentOut(
                player=rounding_adjustment.player,
                leftover_cents=rounding_adjustment.leftover_cents,
                reason=rounding_adjustment.reason,
            )
            if rounding_adjustment is not None
            else None
        ),
        discrepancy_resolution=(
            DiscrepancyResolutionOut(
                strategy=discrepancy_resolution.strategy,
                delta=_cents_to_dollars(discrepancy_resolution.delta),
                adjustments=[
                    DiscrepancyAdjustmentOut(
                        name=a.name, adjustment=_cents_to_dollars(a.adjustment_cents)
                    )
                    for a in discrepancy_resolution.adjustments
                ],
                excluded_players=discrepancy_resolution.excluded_players,
            )
            if discrepancy_resolution is not None
            else None
        ),
    )


def settlement_success_to_response(result: SettlementSuccess) -> SettlementSuccessOut:
    return SettlementSuccessOut(
        nets=[NetOut(name=n.name, net=_cents_to_dollars(n.net)) for n in result.nets],
        transactions=[
            TransactionOut(
                from_player=t.from_player, to=t.to_player, amount=_cents_to_dollars(t.amount)
            )
            for t in result.transactions
        ],
        breakdown=_breakdown_to_response(result.breakdown),
    )


def reconciliation_failure_to_response(
    result: ReconciliationFailure,
) -> ReconciliationFailureOut:
    return ReconciliationFailureOut(
        total_buy_ins=_cents_to_dollars(result.total_buy_ins),
        total_final_balances=_cents_to_dollars(result.total_final_balances),
        delta=_cents_to_dollars(result.delta),
        message=result.message,
        resolvable=result.resolvable,
    )
