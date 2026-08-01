import pytest

from app.services.settle import (
    Breakdown,
    DebtorCreditorEntry,
    DiscrepancyStrategy,
    NetEntry,
    Player,
    ReconciliationFailure,
    SettlementSuccess,
    Transaction,
    _distribute_discrepancy,
    _match_debts,
    compute_settlement,
)


@pytest.fixture
def three_player_game():
    # Worked example, PRD.md §5.3 / CLAUDE.md testing pattern.
    return [
        Player(name="Nathan", buy_in=1000, final_balance=1250),
        Player(name="Jason", buy_in=2000, final_balance=1000),
        Player(name="Emily", buy_in=1000, final_balance=1750),
    ]


@pytest.fixture
def four_player_game():
    # Worked 4-player example: two debtors, two creditors, no exact
    # debtor/creditor size match on the first pairing (forces a
    # "still owed" mid-trace state before everyone zeroes out).
    return [
        Player(name="Alex", buy_in=3000, final_balance=500),
        Player(name="Blair", buy_in=3000, final_balance=5000),
        Player(name="Casey", buy_in=2000, final_balance=1000),
        Player(name="Drew", buy_in=2000, final_balance=3500),
    ]


def test_player_net_is_final_balance_minus_buy_in():
    player = Player(name="Nathan", buy_in=1000, final_balance=1250)
    assert player.net == 250


def test_three_player_worked_example_produces_minimal_transactions(three_player_game):
    result = compute_settlement(three_player_game)

    assert isinstance(result, SettlementSuccess)
    assert result.nets == [
        NetEntry(name="Nathan", net=250),
        NetEntry(name="Jason", net=-1000),
        NetEntry(name="Emily", net=750),
    ]
    assert len(result.transactions) == 2
    assert result.transactions == [
        Transaction(from_player="Jason", to_player="Emily", amount=750),
        Transaction(from_player="Jason", to_player="Nathan", amount=250),
    ]
    assert result.breakdown.rounding_adjustment is None


def test_three_player_worked_example_breakdown_matches_prd_trace(three_player_game):
    result = compute_settlement(three_player_game)

    assert result.breakdown.debtors_sorted == [
        DebtorCreditorEntry(name="Jason", amount=1000),
    ]
    assert result.breakdown.creditors_sorted == [
        DebtorCreditorEntry(name="Emily", amount=750),
        DebtorCreditorEntry(name="Nathan", amount=250),
    ]
    assert result.breakdown.match_trace == [
        "Jason (owes $10.00) pays Emily (owed $7.50) -> $7.50; "
        "Jason now owes $2.50, Emily settled",
        "Jason (owes $2.50) pays Nathan (owed $2.50) -> $2.50; "
        "Jason now owes $0.00, Nathan settled",
    ]


def test_four_player_worked_example_settles_to_zero(four_player_game):
    result = compute_settlement(four_player_game)

    assert isinstance(result, SettlementSuccess)
    assert sum(t.amount for t in result.transactions if t.from_player == "Alex") == 2500
    assert sum(t.amount for t in result.transactions if t.from_player == "Casey") == 1000
    assert sum(t.amount for t in result.transactions if t.to_player == "Blair") == 2000
    assert sum(t.amount for t in result.transactions if t.to_player == "Drew") == 1500
    assert len(result.transactions) == 3
    assert result.breakdown.rounding_adjustment is None


def test_four_player_worked_example_trace_reports_partial_creditor_state(four_player_game):
    result = compute_settlement(four_player_game)

    assert result.breakdown.match_trace == [
        "Alex (owes $25.00) pays Blair (owed $20.00) -> $20.00; "
        "Alex now owes $5.00, Blair settled",
        "Casey (owes $10.00) pays Drew (owed $15.00) -> $10.00; "
        "Casey now owes $0.00, Drew still owed $5.00",
        "Alex (owes $5.00) pays Drew (owed $5.00) -> $5.00; "
        "Alex now owes $0.00, Drew settled",
    ]


def test_single_debtor_single_creditor():
    players = [
        Player(name="A", buy_in=1000, final_balance=500),
        Player(name="B", buy_in=500, final_balance=1000),
    ]

    result = compute_settlement(players)

    assert isinstance(result, SettlementSuccess)
    assert result.transactions == [Transaction(from_player="A", to_player="B", amount=500)]
    assert len(result.breakdown.debtors_sorted) == 1
    assert len(result.breakdown.creditors_sorted) == 1


def test_already_settled_all_zero_nets():
    players = [
        Player(name="A", buy_in=1000, final_balance=1000),
        Player(name="B", buy_in=500, final_balance=500),
    ]

    result = compute_settlement(players)

    assert isinstance(result, SettlementSuccess)
    assert result.transactions == []
    assert result.breakdown.debtors_sorted == []
    assert result.breakdown.creditors_sorted == []
    assert result.breakdown.match_trace == []
    assert result.breakdown.rounding_adjustment is None


def test_mismatched_nets_returns_full_reconciliation():
    players = [
        Player(name="A", buy_in=1000, final_balance=1000),
        Player(name="B", buy_in=2000, final_balance=1001),
        Player(name="C", buy_in=1000, final_balance=1750),
    ]

    result = compute_settlement(players)

    assert isinstance(result, ReconciliationFailure)
    assert result.total_buy_ins == 4000
    assert result.total_final_balances == 3751
    assert result.delta == -249
    assert "check entries" in result.message.lower()


def test_mismatched_nets_message_matches_prd_wording():
    # PRD.md §5.3: total_buy_ins=40.00, total_final_balances=40.01, delta=0.01
    players = [
        Player(name="A", buy_in=1000, final_balance=1000),
        Player(name="B", buy_in=2000, final_balance=1000),
        Player(name="C", buy_in=1000, final_balance=2001),
    ]

    result = compute_settlement(players)

    assert isinstance(result, ReconciliationFailure)
    assert result.total_buy_ins == 4000
    assert result.total_final_balances == 4001
    assert result.delta == 1
    assert result.message == (
        "Final balances exceed buy-ins by $0.01 — check entries for a data entry mistake."
    )


def test_reconciliation_failure_reports_shortfall_direction():
    players = [
        Player(name="A", buy_in=1000, final_balance=900),
        Player(name="B", buy_in=1000, final_balance=1000),
    ]

    result = compute_settlement(players)

    assert isinstance(result, ReconciliationFailure)
    assert result.delta == -100
    assert "fall short of" in result.message


def test_match_debts_rounding_fallback_forced_deliberately():
    # settle.py's public entrypoint never reaches this path because
    # compute_settlement rejects nets that don't sum to zero first.
    # Force it directly against the internal matcher to confirm the
    # defensive fallback auto-assigns and reports rather than crashing.
    imbalanced_nets = [
        NetEntry(name="A", net=-60),
        NetEntry(name="B", net=-30),
        NetEntry(name="C", net=100),
    ]

    transactions, trace, rounding_adjustment = _match_debts(imbalanced_nets)

    assert rounding_adjustment is not None
    assert rounding_adjustment.player == "C"
    assert rounding_adjustment.leftover_cents == 10
    assert "C" in rounding_adjustment.reason
    assert sum(t.amount for t in transactions) == 90
    assert len(trace) == 2


def test_breakdown_always_present_on_success(three_player_game):
    result = compute_settlement(three_player_game)
    assert isinstance(result.breakdown, Breakdown)


def test_breakdown_fields_present_on_reconciliation_failure():
    players = [
        Player(name="A", buy_in=1000, final_balance=900),
        Player(name="B", buy_in=1000, final_balance=1000),
    ]
    result = compute_settlement(players)

    assert isinstance(result, ReconciliationFailure)
    assert result.total_buy_ins is not None
    assert result.total_final_balances is not None
    assert result.delta is not None
    assert result.message


# --- Discrepancy resolution (opt-in) ---------------------------------------


def test_reconciliation_failure_reports_resolvable_true_without_opting_in():
    # resolvable is computed eagerly even when resolve_discrepancy isn't set,
    # so the client can decide whether to offer the fix at all.
    players = [
        Player(name="A", buy_in=1000, final_balance=1000),
        Player(name="B", buy_in=2000, final_balance=1000),
        Player(name="C", buy_in=1000, final_balance=2001),
    ]

    result = compute_settlement(players)

    assert isinstance(result, ReconciliationFailure)
    assert result.resolvable is True


def test_reconciliation_failure_reports_resolvable_false_when_unresolvable():
    # Forced via a negative buy-in (rejected by Pydantic at the API boundary,
    # but usable here to exercise the pure function's defensive branch) so
    # there's zero headroom in final balances to claw back from.
    players = [
        Player(name="A", buy_in=-1000, final_balance=0),
        Player(name="B", buy_in=0, final_balance=0),
    ]

    result = compute_settlement(players)

    assert isinstance(result, ReconciliationFailure)
    assert result.resolvable is False


def test_reconciliation_failure_unchanged_when_resolve_discrepancy_not_requested():
    players = [
        Player(name="A", buy_in=1000, final_balance=1000),
        Player(name="B", buy_in=2000, final_balance=1000),
        Player(name="C", buy_in=1000, final_balance=2001),
    ]

    result = compute_settlement(players, resolve_discrepancy=False)

    assert isinstance(result, ReconciliationFailure)
    assert result.delta == 1


def test_resolve_discrepancy_even_split_produces_success_with_zero_summing_nets():
    players = [
        Player(name="Nathan", buy_in=1000, final_balance=1250),
        Player(name="Jason", buy_in=2000, final_balance=1000),
        Player(name="Emily", buy_in=1000, final_balance=1751),
    ]

    result = compute_settlement(players, resolve_discrepancy=True)

    assert isinstance(result, SettlementSuccess)
    assert sum(n.net for n in result.nets) == 0


def test_resolve_discrepancy_records_discrepancy_resolution_in_breakdown():
    players = [
        Player(name="Nathan", buy_in=1000, final_balance=1250),
        Player(name="Jason", buy_in=2000, final_balance=1000),
        Player(name="Emily", buy_in=1000, final_balance=1751),
    ]

    result = compute_settlement(players, resolve_discrepancy=True)

    assert isinstance(result, SettlementSuccess)
    resolution = result.breakdown.discrepancy_resolution
    assert resolution is not None
    assert resolution.strategy == DiscrepancyStrategy.EVEN.value
    assert resolution.delta == 1
    assert sum(a.adjustment_cents for a in resolution.adjustments) == -1
    assert resolution.excluded_players == []
    assert result.breakdown.rounding_adjustment is None


def test_resolve_discrepancy_excludes_player_who_would_go_negative():
    # An even 2-cent split would take 1c from each, but B has nothing to
    # give back — the whole clawback must fall to A.
    players = [
        Player(name="A", buy_in=1000, final_balance=2002),
        Player(name="B", buy_in=1000, final_balance=0),
    ]

    result = compute_settlement(players, resolve_discrepancy=True)

    assert isinstance(result, SettlementSuccess)
    resolution = result.breakdown.discrepancy_resolution
    assert resolution is not None
    assert resolution.excluded_players == ["B"]
    adjustments = {a.name: a.adjustment_cents for a in resolution.adjustments}
    assert adjustments["B"] == 0
    assert adjustments["A"] == -2


def test_resolve_discrepancy_falls_back_to_reconciliation_failure_when_unresolvable():
    players = [
        Player(name="A", buy_in=-1000, final_balance=0),
        Player(name="B", buy_in=0, final_balance=0),
    ]

    result = compute_settlement(players, resolve_discrepancy=True)

    assert isinstance(result, ReconciliationFailure)
    assert result.resolvable is False


def test_distribute_discrepancy_returns_none_when_unresolvable():
    players = [
        Player(name="A", buy_in=-1000, final_balance=0),
        Player(name="B", buy_in=0, final_balance=0),
    ]
    delta = sum(p.final_balance for p in players) - sum(p.buy_in for p in players)

    resolution = _distribute_discrepancy(players, delta, DiscrepancyStrategy.EVEN)

    assert resolution is None


def test_distribute_discrepancy_rejects_unsupported_strategy():
    players = [
        Player(name="A", buy_in=1000, final_balance=1000),
        Player(name="B", buy_in=1000, final_balance=1001),
    ]

    with pytest.raises(NotImplementedError):
        _distribute_discrepancy(players, delta=1, strategy="proportional")


def test_distribute_discrepancy_gives_extra_when_final_balances_fall_short():
    players = [
        Player(name="A", buy_in=1000, final_balance=900),
        Player(name="B", buy_in=1000, final_balance=1000),
    ]
    delta = sum(p.final_balance for p in players) - sum(p.buy_in for p in players)

    resolution = _distribute_discrepancy(players, delta, DiscrepancyStrategy.EVEN)

    assert resolution is not None
    assert sum(a.adjustment_cents for a in resolution.adjustments) == 100
    assert resolution.excluded_players == []
