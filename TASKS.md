# TASKS.md - Settle-Up

Tracks implementation tasks by milestone, per PRD.md §9 and CLAUDE.md's Implementation Phases. Mark tasks `[x]` immediately upon completion. Add newly discovered tasks under the relevant milestone as they come up.

---

## M1 — MVP (Priority 1)

### Backend skeleton
- [x] `backend/pyproject.toml` with Flask, Pydantic deps + pytest, pytest-cov dev deps (uv-managed)
- [x] Flask app factory (`backend/app/__init__.py` empty per convention; app creation in `app/main.py` — run via `uv run flask --app app.main:create_app run --debug`)
- [x] Directory scaffold: `app/routes/`, `app/services/`, `app/models/`, `tests/` (all `__init__.py` kept empty)

### Domain models (`backend/app/models/game.py`)
- [x] `PlayerInput` Pydantic model: name (str), buy_in (Decimal, >= 0), final_balance (Decimal)
- [x] `SettlementRequest` model wrapping `players: list[PlayerInput]`
- [x] Field validator rejecting duplicate player names
- [x] Dollars -> integer cents conversion at this boundary (and nowhere else)
- [x] Response schemas: success (nets, transactions, breakdown) and error (reconciliation) shapes matching PRD §5.3

### Settlement algorithm (`backend/app/services/settle.py`)
- [x] Write failing tests first (see Testing section below) before implementing
- [x] Pure function `compute_settlement(players) -> SettlementSuccess | ReconciliationFailure`, no Flask/IO, cents only
- [x] Net calculation per player (final_balance - buy_in)
- [x] Reconciliation check: nets sum to zero; if not, return full reconciliation (total buy-ins, total final balances, delta) instead of a bare error
- [x] Greedy minimal-transaction match: sort debtors/creditors, match largest-to-largest until zeroed
- [x] Step-by-step match trace construction for breakdown
- [x] Defensive fractional-cent fallback: auto-assign leftover cent to a randomly chosen player, record which player and why in `breakdown.rounding_adjustment`
- [x] Confirm 100% test coverage on this module
- [x] Opt-in discrepancy resolution (FR-020–023): `resolve_discrepancy` request flag, `resolvable` computed eagerly on reconciliation failure, even-split via swappable `DiscrepancyStrategy`, floor guard + exclusion/redistribution, recorded in `breakdown.discrepancy_resolution`

### Route wiring (`backend/app/routes/settlement.py`)
- [x] `POST /api/settlement`: validate via Pydantic -> `compute_settlement` -> `jsonify` response
- [x] Correct HTTP status codes (200 success / 422 validation-type errors)
- [x] Malformed/non-numeric input returns actionable 4xx error, not a stack trace

### Backend testing (`backend/tests/test_settle.py` + route tests)
- [x] Failing tests written before implementation (TDD)
- [x] Worked 3-player example (PRD §5.3) as fixed regression fixture
- [x] Worked 4-player example as fixed regression fixture
- [x] Single debtor / single creditor case
- [x] Already-settled (all-zero net) input
- [x] Mismatched nets (error path) — assert exact reconciliation math (total buy-ins, total final balances, delta)
- [x] Duplicate player names rejected
- [x] Negative buy-in rejected
- [x] Malformed/non-numeric input rejected with actionable message
- [x] Defensive rounding fallback forced deliberately — confirm auto-assignment + reporting, not silent
- [x] Every success and error response asserted to include full breakdown/reconciliation fields
- [x] Integration tests: Flask route + Pydantic validation + HTTP status/error shape
- [x] `uv run pytest --cov=app --cov-report=term-missing` shows 100% coverage on `settle.py`
- [x] Discrepancy resolution: resolvable flag (true/false), even-split success + breakdown fields, floor-guard exclusion, unresolvable fallback, unsupported-strategy defensive branch — all covered

### Mobile app
- [ ] Expo project scaffold under `mobile/` (`package.json`, Expo config)
- [ ] Add-player screen: name, buy-in, final balance entry (numeric keypad, low-friction per NFR-001)
- [ ] Client-side validation: reject negative buy-in, reject duplicate names before hitting the API
- [ ] API client module (`mobile/src/api/`) calling `POST /api/settlement`
- [ ] Results screen: transaction list + reconciliation summary (error case) shown by default
- [ ] Collapsed/expandable "show calculation" section for the full breakdown (FR-012, NFR-004)
- [ ] Actionable error messaging surfaced in UI for each validation failure type (NFR-003)
- [ ] Local save/restore of last game via AsyncStorage
- [ ] Dark mode support (NFR-002)
- [ ] Manual/exploratory pass through golden path + edge cases (no formal mobile coverage target for MVP)

---

## M2 — History & Presets (Priority 2)

- [ ] Local calculator history, grouped by game (extends AsyncStorage persistence beyond "last game only")
- [ ] Presets for recurring games: saved player names, default buy-in amounts
- [ ] UI for selecting/applying a preset when starting a new game
- [ ] Manual/exploratory testing of history and preset flows

---

## M3 — Unified Codebase (Priority 3)

- [ ] Establish monorepo layout: `web/` joins `backend/` + `mobile/`
- [ ] React web client implementing the same core flow (add players -> settle -> breakdown)
- [ ] Confirm backend API boundary needs no changes to serve both clients (validates NFR-009)
- [ ] Shared API client logic factored out where practical between mobile and web

---

## M4 — Design Language (Priority 4)

- [ ] Define shared design system/mood board across mobile and web
- [ ] Apply shared components/styling to mobile app
- [ ] Apply shared components/styling to web app

---

## M5 — Cloud Hosting (Priority 5)

- [ ] Choose hosting provider for Flask backend (open question, PRD §10.2)
- [ ] Deploy backend to chosen host
- [ ] Cross-device history support (requires backend-side persistence beyond local storage)
- [ ] Game-sharing: shareable read-only link/view for a settlement result

---

## Backlog / Nice-to-Haves (not tied to a milestone)

- [ ] Settlement summary export/share sheet (FR-017, explicitly deferred)
- [ ] Revisit rebuy handling if adjusting initial buy-in proves limiting in practice (see PRD §10.1)
- [ ] Proportional discrepancy-split strategy (weighted by buy-in), if the group's buy-in variance ever grows enough to justify it over even-split (see PRD §10.1 "Discrepancy resolution strategy"); `DiscrepancyStrategy` in `settle.py` is already built to accept it

---

## Open Questions Blocking Future Work

- Hosting provider for M5 cloud deployment — undecided (weighing homelab self-host vs. AWS EC2); not blocking, M5 is not current milestone
