"""Pure settlement algorithm: net calculation, minimal-transaction greedy
match, and breakdown/trace construction. No Flask, no I/O — integer cents
only, never float."""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class Player:
    name: str
    buy_in: int  # cents
    final_balance: int  # cents

    @property
    def net(self) -> int:
        return self.final_balance - self.buy_in


@dataclass(frozen=True)
class NetEntry:
    name: str
    net: int  # cents


@dataclass(frozen=True)
class Transaction:
    from_player: str
    to_player: str
    amount: int  # cents


@dataclass(frozen=True)
class DebtorCreditorEntry:
    name: str
    amount: int  # cents, always positive


@dataclass(frozen=True)
class RoundingAdjustment:
    player: str
    leftover_cents: int
    reason: str


class DiscrepancyStrategy(str, Enum):
    """How a reconciliation delta is split across players when the client
    opts in to auto-resolution. Only EVEN exists today; kept as an enum so
    a PROPORTIONAL strategy can be added later without changing callers."""

    EVEN = "even"


@dataclass(frozen=True)
class DiscrepancyAdjustment:
    name: str
    adjustment_cents: int  # signed: negative = clawed back, positive = extra given


@dataclass(frozen=True)
class DiscrepancyResolution:
    strategy: str
    delta: int
    adjustments: list[DiscrepancyAdjustment]
    excluded_players: list[str]


@dataclass(frozen=True)
class Breakdown:
    debtors_sorted: list[DebtorCreditorEntry]
    creditors_sorted: list[DebtorCreditorEntry]
    match_trace: list[str]
    rounding_adjustment: RoundingAdjustment | None
    discrepancy_resolution: DiscrepancyResolution | None = None


@dataclass(frozen=True)
class SettlementSuccess:
    nets: list[NetEntry]
    transactions: list[Transaction]
    breakdown: Breakdown


@dataclass(frozen=True)
class ReconciliationFailure:
    total_buy_ins: int
    total_final_balances: int
    delta: int
    message: str
    resolvable: bool


def _format_dollars(cents: int) -> str:
    return f"${cents / 100:.2f}"


def _sorted_desc(entries: list[DebtorCreditorEntry]) -> list[DebtorCreditorEntry]:
    return sorted(entries, key=lambda e: e.amount, reverse=True)


def _match_debts(
    nets: list[NetEntry],
) -> tuple[list[Transaction], list[str], RoundingAdjustment | None]:
    """Greedily match the largest debtor to the largest creditor, re-picking
    the current largest of each after every match, until one side is empty.

    Assumes nets sum to zero, but doesn't require it: any leftover after
    matching is handled by the defensive rounding fallback (see module
    docstring / CLAUDE.md "Common Pitfalls to Avoid").
    """
    debtors = [[entry.name, -entry.net] for entry in nets if entry.net < 0]
    creditors = [[entry.name, entry.net] for entry in nets if entry.net > 0]

    transactions: list[Transaction] = []
    trace: list[str] = []

    while debtors and creditors:
        debtors.sort(key=lambda d: d[1], reverse=True)
        creditors.sort(key=lambda c: c[1], reverse=True)

        debtor_name, debt_before = debtors[0]
        creditor_name, credit_before = creditors[0]
        amount = min(debt_before, credit_before)

        debt_after = debt_before - amount
        credit_after = credit_before - amount

        creditor_status = (
            f"{creditor_name} settled"
            if credit_after == 0
            else f"{creditor_name} still owed {_format_dollars(credit_after)}"
        )
        trace.append(
            f"{debtor_name} (owes {_format_dollars(debt_before)}) pays {creditor_name} "
            f"(owed {_format_dollars(credit_before)}) -> {_format_dollars(amount)}; "
            f"{debtor_name} now owes {_format_dollars(debt_after)}, {creditor_status}"
        )
        transactions.append(
            Transaction(from_player=debtor_name, to_player=creditor_name, amount=amount)
        )

        if debt_after == 0:
            debtors.pop(0)
        else:
            debtors[0][1] = debt_after

        if credit_after == 0:
            creditors.pop(0)
        else:
            creditors[0][1] = credit_after

    rounding_adjustment = None
    leftover = debtors or creditors
    if leftover:
        stray_name, stray_amount = random.choice(leftover)
        rounding_adjustment = RoundingAdjustment(
            player=stray_name,
            leftover_cents=stray_amount,
            reason=(
                f"Matching left {stray_amount} unassigned cent(s) after debtors and "
                "creditors stopped lining up exactly — auto-assigned to "
                f"{stray_name} because inputs should always net to whole cents "
                "that sum to zero."
            ),
        )

    return transactions, trace, rounding_adjustment


def _even_shares(total_cents: int, names: list[str]) -> dict[str, int]:
    """Split total_cents as evenly as possible across names, same sign as
    total_cents. Names are sorted so any leftover single cents land on the
    same players deterministically (alphabetically first)."""
    sign = 1 if total_cents >= 0 else -1
    magnitude = abs(total_cents)
    base, remainder = divmod(magnitude, len(names))
    return {
        name: sign * (base + 1 if i < remainder else base)
        for i, name in enumerate(sorted(names))
    }


def _distribute_discrepancy(
    players: list[Player], delta: int, strategy: DiscrepancyStrategy
) -> DiscrepancyResolution | None:
    """Split -delta across players' final balances so nets sum to zero.

    A player whose adjusted final balance would go negative is excluded and
    their share redistributed across the rest, looping until stable. Returns
    None if no split leaves every player non-negative — the delta can't be
    auto-resolved and the caller should fall back to the hard error.
    """
    if strategy is not DiscrepancyStrategy.EVEN:
        raise NotImplementedError(f"Unsupported discrepancy strategy: {strategy}")

    total_adjustment = -delta
    remaining = list(players)
    excluded: list[str] = []

    while remaining:
        shares = _even_shares(total_adjustment, [p.name for p in remaining])
        violators = [p for p in remaining if p.final_balance + shares[p.name] < 0]
        if not violators:
            adjustments = [
                DiscrepancyAdjustment(name=p.name, adjustment_cents=shares.get(p.name, 0))
                for p in players
            ]
            return DiscrepancyResolution(
                strategy=strategy.value,
                delta=delta,
                adjustments=adjustments,
                excluded_players=excluded,
            )
        excluded.extend(v.name for v in violators)
        violator_names = {v.name for v in violators}
        remaining = [p for p in remaining if p.name not in violator_names]

    return None


def _apply_discrepancy_resolution(
    players: list[Player], resolution: DiscrepancyResolution
) -> list[Player]:
    adjustment_by_name = {a.name: a.adjustment_cents for a in resolution.adjustments}
    return [
        Player(
            name=p.name,
            buy_in=p.buy_in,
            final_balance=p.final_balance + adjustment_by_name[p.name],
        )
        for p in players
    ]


def compute_settlement(
    players: list[Player],
    resolve_discrepancy: bool = False,
    strategy: DiscrepancyStrategy = DiscrepancyStrategy.EVEN,
) -> SettlementSuccess | ReconciliationFailure:
    """Net calc -> reconciliation check -> greedy minimal-transaction match.

    Never runs the match against nets that don't sum to zero unless the
    caller opts in to auto-resolution (resolve_discrepancy=True) and a valid
    split exists; otherwise returns the full reconciliation instead of a
    bare error.
    """
    total_buy_ins = sum(p.buy_in for p in players)
    total_final_balances = sum(p.final_balance for p in players)
    delta = total_final_balances - total_buy_ins

    resolution = None
    if delta != 0:
        resolution = _distribute_discrepancy(players, delta, strategy)
        if not (resolve_discrepancy and resolution is not None):
            direction = "exceed" if delta > 0 else "fall short of"
            return ReconciliationFailure(
                total_buy_ins=total_buy_ins,
                total_final_balances=total_final_balances,
                delta=delta,
                message=(
                    f"Final balances {direction} buy-ins by {_format_dollars(abs(delta))} "
                    "— check entries for a data entry mistake."
                ),
                resolvable=resolution is not None,
            )
        players = _apply_discrepancy_resolution(players, resolution)

    nets = [NetEntry(name=p.name, net=p.net) for p in players]
    transactions, trace, rounding_adjustment = _match_debts(nets)

    debtors_sorted = _sorted_desc(
        [DebtorCreditorEntry(name=n.name, amount=-n.net) for n in nets if n.net < 0]
    )
    creditors_sorted = _sorted_desc(
        [DebtorCreditorEntry(name=n.name, amount=n.net) for n in nets if n.net > 0]
    )

    breakdown = Breakdown(
        debtors_sorted=debtors_sorted,
        creditors_sorted=creditors_sorted,
        match_trace=trace,
        rounding_adjustment=rounding_adjustment,
        discrepancy_resolution=resolution,
    )
    return SettlementSuccess(nets=nets, transactions=transactions, breakdown=breakdown)
