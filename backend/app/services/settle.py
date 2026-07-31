"""Pure settlement algorithm: net calculation, minimal-transaction greedy
match, and breakdown/trace construction. No Flask, no I/O — integer cents
only, never float."""

from __future__ import annotations

import random
from dataclasses import dataclass


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


@dataclass(frozen=True)
class Breakdown:
    debtors_sorted: list[DebtorCreditorEntry]
    creditors_sorted: list[DebtorCreditorEntry]
    match_trace: list[str]
    rounding_adjustment: RoundingAdjustment | None


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


def compute_settlement(players: list[Player]) -> SettlementSuccess | ReconciliationFailure:
    """Net calc -> reconciliation check -> greedy minimal-transaction match.

    Never runs the match against nets that don't sum to zero; returns the
    full reconciliation instead of a bare error in that case.
    """
    total_buy_ins = sum(p.buy_in for p in players)
    total_final_balances = sum(p.final_balance for p in players)
    delta = total_final_balances - total_buy_ins

    if delta != 0:
        direction = "exceed" if delta > 0 else "fall short of"
        return ReconciliationFailure(
            total_buy_ins=total_buy_ins,
            total_final_balances=total_final_balances,
            delta=delta,
            message=(
                f"Final balances {direction} buy-ins by {_format_dollars(abs(delta))} "
                "— check entries for a data entry mistake."
            ),
        )

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
    )
    return SettlementSuccess(nets=nets, transactions=transactions, breakdown=breakdown)
