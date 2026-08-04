# CLAUDE.md - Settle-Up Project Guide

## Project Overview

**Settle-Up** is a mobile app that resolves who-owes-who at the end of a game night (poker, board games, any buy-in-based game). Users enter each player's buy-in and final balance; a Flask backend computes the minimum set of transactions needed to settle all debts, and every result (success or error) shows its underlying math. Target users: Nathan and his regular game group — a casual single-session utility, not a general ledger/expense-splitting app (not Splitwise).

**Version:** 0.1.0 (pre-MVP)
**Backend:** Python 3.11+, uv
**Mobile:** React Native (Expo), Node 18+, npm

Full detail lives in [PRD.md](PRD.md) — treat it as the source of truth for requirements. Keep this file and the PRD in sync as decisions get made during implementation.

## Development Strategy

- Use a test-driven development strategy, developing tests prior to generating solutions to the tests.
- Run the tests and ensure that they fail prior to generating any solutions. Do not create mock versions of the code simply to pass the tests.
- Write code that passes the tests.
- IMPORTANT: Do not modify the tests simply so that the code passes. Only modify the tests if you identify a specific error in the test.

## Notes for Development

- Think about the problem before generating code.
- Always add a smoke test for the main() function.
- Prefer reliance on widely used packages (such as numpy, pandas, and scikit-learn); avoid unknown packages from Github.
- Do not include any code in init.py files.
- Use pytest for testing.
- Write code that is clean and modular. Prefer shorter functions/methods over longer ones.
- Use functions rather than classes for tests. Use pytest fixtures to share resources between tests.

## Session Guidelines

- Always read PLANNING.md at the start of every new conversation.
- Check TASKS.md and SCRATCHPAD.md before starting your work.
- Mark completed tasks immediately within TASKS.md.
- Add newly discovered tasks to TASKS.md.
- Use SCRATCHPAD.md as a scratchpad to outline plans.

## Git Workflow

- Never commit directly to `main`. Every task — feature, fix, refactor — gets its own short-lived branch, even for solo work. This is what makes review possible before anything lands.
- Branch naming: `<category>/<short-description>`, kebab-case. Categories: `feature/`, `fix/`, `chore/`, `refactor/`, `docs/`. E.g. `feature/settlement-algorithm`, `fix/rounding-bug`.
- Commit incrementally within that branch as you go. Commits don't need to be squashed or polished — only the eventual PR needs to read cleanly as a whole.
- When a task is ready for review, open a PR (`gh pr create`) instead of merging directly. Use a draft PR if the work is still in progress but you want visibility into it.
- Nathan reviews via VS Code's GitHub Pull Requests extension (inline comments) and/or files the review into Obsidian via the `pr-to-obsidian` skill. Wait for explicit approval before merging — never merge your own PR unless told to.
- Delete the branch after merge — no exceptions, this is what keeps the branch list from accumulating.
- Exception: trivial doc-only edits (README typo, comment wording) can go straight to `main` if Nathan explicitly says so — don't assume this on your own.

## Core Architecture

### Repository Structure (MVP)
```
poker-calculator/
├── backend/                    # Flask API
│   ├── app/
│   │   ├── __init__.py         # Keep empty
│   │   ├── main.py             # Flask app factory (create_app) + smoke-tested main()
│   │   ├── routes/
│   │   │   ├── __init__.py     # Keep empty
│   │   │   └── settlement.py   # POST /api/settlement
│   │   ├── services/
│   │   │   ├── __init__.py     # Keep empty
│   │   │   └── settle.py       # debt-simplification algorithm (pure function)
│   │   └── models/
│   │       ├── __init__.py     # Keep empty
│   │       └── game.py         # Pydantic request/response schemas
│   ├── tests/
│   │   ├── __init__.py         # Keep empty
│   │   └── test_settle.py
│   └── pyproject.toml
└── mobile/                     # React Native (Expo) app
    ├── src/
    │   ├── screens/
    │   ├── components/
    │   ├── storage/            # AsyncStorage for recent games
    │   └── api/                # client for backend endpoints
    └── package.json
```

`web/` (React) joins this layout at Milestone M3, unifying into a monorepo that shares `backend/`. Keep a clean API boundary between `backend/` and `mobile/` from the start so this migration stays low-friction.

## Core Domain Rules

- **Net** = final balance − buy-in, per player.
- Nets must sum to zero before a settlement is computed. If they don't, return the full reconciliation (total buy-ins, total final balances, exact delta) — never a bare pass/fail.
- **Discrepancy resolution (opt-in only):** the reconciliation failure always includes a `resolvable: bool`, computed eagerly, so the client can decide whether to offer a fix without a second round trip. Resolution itself only runs if the client resends the request with `resolve_discrepancy: true` — never automatic, since the reconciliation error's job is to surface likely data-entry mistakes, not paper over them. When opted in, the delta is split **evenly** across every player's final balance (not proportional to buy-in — see PRD §10.1 for why), implemented as a swappable `DiscrepancyStrategy` (`settle.py`) so a proportional strategy can be added later without an API shape change. A player whose adjusted final balance would go negative is excluded and their share redistributed across the rest; if no split avoids a negative balance, resolution fails and the standard reconciliation error is returned instead. A successful resolution is recorded in `breakdown.discrepancy_resolution` (never silent, same principle as the rounding fallback below).
- Settlement is a **minimal-transaction** match: split into debtors (negative net) and creditors (positive net), greedily match largest debtor to largest creditor until zeroed out. Optimize for fewest transactions, not fewest dollars moved.
- Work in **integer cents** internally — never float — to avoid rounding drift. Only convert to dollars for display.
- Every computed response, success or error, includes a full breakdown: per-player net calculation, sorted debtor/creditor lists, and a step-by-step match trace. The transaction list is never returned without its supporting work. In the UI this breakdown is collapsed by default, expandable on demand ("show calculation").
- Reject negative buy-ins and duplicate player names at input, client and API side.
- The defensive fractional-cent fallback (leftover cent after matching) should not occur in normal operation given exact-cent inputs and the sum-to-zero check — but if it does, auto-assign the cent to a randomly chosen player and record exactly which player and why in the breakdown. Never fix it silently.
- Calculation is server-side by deliberate choice — the mobile app always calls the backend for validation and settlement, never computes locally.
- No in-game math: buy-in and final balance are always already-known, final numbers by the time they're entered. The app never calculates or influences them (no pot-splitting, no live running ledger).

## Explicit Non-Goals (MVP)

- No multi-currency, recurring shared expenses, or accounts (not Splitwise).
- No real money movement / payment integration.
- No cloud sync or account-based history — local device storage only.
- No mid-entry editing of a live ledger — entries are a final pass after the game.
- No export/share sheet (nice-to-have, not required).
- No CI pipeline required at this stage; manual/exploratory testing is acceptable for the mobile UI.

## Key Dependencies

Backend (`backend/pyproject.toml`, managed with uv):
```toml
[dependencies]
flask = ">=3.0.0"
flask-cors = ">=6.0.0"
pydantic = ">=2.0.0"

[dev-dependencies]
pytest = ">=7.0.0"
pytest-cov = ">=4.0.0"
```
`flask-cors` was added when mobile M1 work started, purely to let Expo web (used for local browser testing in dev/sandboxed environments without a simulator) call `localhost` across ports. It has no bearing on native mobile usage, where CORS doesn't apply.

Mobile (`mobile/package.json`, Expo):
```json
{
  "dependencies": {
    "expo": "~57.0.9",
    "expo-constants": "~18.x",
    "expo-status-bar": "~57.0.1",
    "react": "19.x",
    "react-native": "0.86.x",
    "@react-native-async-storage/async-storage": "^2.2.0"
  }
}
```
Versions above are current as of M1 mobile scaffolding (Aug 2026) — the `~51.0.0`/React 18/RN 0.74 pins once documented here predate scaffolding and are obsolete; `npx create-expo-app` pulls whatever's current on npm, and forcing an old pinned SDK isn't worth it for a solo project. Keep this section in sync whenever deps are bumped.

## Core API Design

```python
# models/game.py — Pydantic validates at the boundary, converts dollars -> int cents
class PlayerInput(BaseModel):
    name: str
    buy_in: Decimal = Field(ge=0)
    final_balance: Decimal

class SettlementRequest(BaseModel):
    players: list[PlayerInput]

    @field_validator("players")
    def unique_names(cls, v): ...

# services/settle.py — pure function, cents only, no Flask/IO
def compute_settlement(players: list[Player]) -> SettlementResult:
    """No Flask, no I/O — takes/returns plain domain objects in integer cents."""
    ...

# routes/settlement.py — thin glue
@app.route("/api/settlement", methods=["POST"])
def settlement():
    req = SettlementRequest.model_validate(request.get_json())
    result = compute_settlement(req.to_domain_players())
    return jsonify(result.model_dump()), 200 if result.success else 422
```

The dollars-in-JSON / cents-internally boundary is exactly the Pydantic model layer — conversion happens once, immediately after validation, nowhere else.

```
POST /api/settlement
Request:
{
  "players": [
    { "name": "Nathan", "buy_in": 10.00, "final_balance": 12.50 },
    { "name": "Jason",  "buy_in": 20.00, "final_balance": 5.00 },
    { "name": "Emily",  "buy_in": 10.00, "final_balance": 17.50 }
  ]
}

Response (success):
{
  "nets": [{ "name": "Nathan", "net": 2.50 }, ...],
  "transactions": [{ "from": "Jason", "to": "Nathan", "amount": 2.50 }, ...],
  "breakdown": {
    "debtors_sorted": [...],
    "creditors_sorted": [...],
    "match_trace": ["Jason (owes $15.00) pays Emily (owed $7.50) -> $7.50; ..."],
    "rounding_adjustment": null
  }
}

Response (validation error — nets don't reconcile):
{
  "error": "nets_do_not_reconcile",
  "total_buy_ins": 40.00,
  "total_final_balances": 40.01,
  "delta": 0.01,
  "message": "Final balances exceed buy-ins by $0.01 — check entries for a data entry mistake."
}
```
Full request/response spec, including the rounding-fallback shape, lives in [PRD.md §5.3](PRD.md).

## Testing Requirements

### Coverage Goals
- `settle.py` (the pure settlement algorithm): 100% coverage — this is the one place correctness is non-negotiable.
- Flask routes and Pydantic validation: covered by integration tests, no fixed percentage target.
- Mobile client: no formal coverage target for MVP (manual/exploratory testing is acceptable per the PRD).

### Test Categories
1. **Unit tests** — `settle.py` in isolation: net calculation, greedy matching, breakdown construction.
2. **Integration tests** — Flask route + Pydantic validation + HTTP status/error shape.
3. **Regression tests** — the worked 3-player and 4-player examples from the PRD as fixed fixtures.

### Required Coverage
Worked 3-player and 4-player examples, single debtor/creditor, already-settled (all-zero) input, mismatched nets (error path with correct reconciliation math), duplicate names, negative buy-ins, malformed input, and the defensive rounding fallback forced deliberately. Every success and error response must be asserted to include its full breakdown/reconciliation fields.

### Testing Pattern
```python
import pytest

@pytest.fixture
def three_player_game():
    return [
        Player(name="Nathan", buy_in=1000, final_balance=1250),
        Player(name="Jason", buy_in=2000, final_balance=1000),
        Player(name="Emily", buy_in=1000, final_balance=1750),
    ]

def test_settlement_minimal_transactions(three_player_game):
    # Act
    result = compute_settlement(three_player_game)

    # Assert
    assert len(result.transactions) == 2
    assert result.breakdown.rounding_adjustment is None
```

## Implementation Phases

### Phase 1: M1 — MVP (Priority 1)
- [ ] Backend project skeleton (`pyproject.toml`, Flask app factory)
- [ ] Pydantic request/response models (`models/game.py`)
- [ ] `settle.py`: net calculation, reconciliation check, greedy minimal-transaction match, breakdown/trace
- [ ] `POST /api/settlement` route wiring validation → `settle.py` → response
- [ ] pytest suite for `settle.py` (worked examples + all required edge cases)
- [ ] Mobile: add-player screen, buy-in + final balance entry
- [ ] Mobile: API client calling `/api/settlement`
- [ ] Local save/restore of last game (AsyncStorage)
- [ ] Dark mode

### Phase 2: M2 — History & Presets (Priority 2)
- [ ] Calculator history grouped by game
- [ ] Presets for recurring games (saved names, default buy-ins)

### Phase 3: M3 — Unified Codebase (Priority 3)
- [ ] Monorepo layout: `web/` joins `backend/` + `mobile/`
- [ ] React web client for the same core flow

### Phase 4: M4 — Design Language (Priority 4)
- [ ] Shared design system across mobile and web

### Phase 5: M5 — Cloud Hosting (Priority 5)
- [ ] Host the Flask backend
- [ ] Cross-device history, game sharing

Don't build ahead of the current milestone unless asked.

## Code Quality Standards

### Style Guidelines
- Follow PEP 8.
- Type hints on all public functions.
- Docstrings only where behavior isn't obvious from the signature — don't restate what the code already says.

### Error Handling
- Validate all inputs at the boundary (Pydantic models), not deep inside `settle.py`.
- Every validation failure gives a specific, actionable message — never a generic "invalid input" (NFR-003).
- Use domain-specific error shapes (e.g. `nets_do_not_reconcile`) rather than bare exceptions leaking to the client.

### Performance
- Settlement endpoint should feel instant — no visible loading spinners for a request this small (NFR-005).
- Process a typical game (a handful of players) synchronously; no need for async/background work at this scale.

## Common Pitfalls to Avoid

1. **Floating-point drift** — always compute in integer cents internally; convert to dollars only at the API boundary/display.
2. **Silent rounding fixes** — the defensive fallback must always be recorded in `breakdown.rounding_adjustment`, never silently applied.
3. **Duplicate/ambiguous names** — reject at both client and API before the request reaches `settle.py`.
4. **Skipping the reconciliation step** — never run `compute_settlement` on nets that don't sum to zero; return the full reconciliation instead of a bare error.
5. **Trimming the breakdown** — never return a transaction list (or an error) without its supporting breakdown/reconciliation fields, even to "simplify" a response.

## Validation Checklist

Before considering any component complete:
- [ ] Unit tests written and passing (including the required edge cases above)
- [ ] Public functions have type hints
- [ ] Error cases return actionable messages, not generic failures
- [ ] Cents/dollars boundary is respected (conversion only happens in `models/game.py`)
- [ ] Success and error responses both include their full breakdown/reconciliation fields
- [ ] Performance is acceptable (no perceptible delay for a normal-sized game)

## Common Commands

```bash
# Backend setup (uv)
cd backend
uv sync
uv run pytest
uv run pytest --cov=app --cov-report=term-missing

# Run Flask dev server
uv run flask --app app.main:create_app run --debug

# Mobile setup (Expo)
cd mobile
npm install
npx expo start
```

## Important Notes

1. **Start with TDD** — write failing tests for `settle.py` before implementing it.
2. **Keep it simple** — don't build ahead of the current milestone (see Implementation Phases).
3. **Protect the API boundary** — keep `backend/` and `mobile/` decoupled so `web/` can join at M3 with minimal rework.
4. **Never trim the breakdown** — every response, success or error, shows its underlying math.
5. **Keep docs in sync** — update PRD.md and this file together as decisions are made during implementation.

## Resources

- [PRD.md](PRD.md) — source of truth for requirements
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Expo Documentation](https://docs.expo.dev/)
- [React Native AsyncStorage](https://react-native-async-storage.github.io/async-storage/)

---

Remember: the goal is a fast, trustworthy calculator Nathan actually reaches for at the table — correctness and transparency over features.
