# PLANNING.md - Settle-Up

Read this file at the start of every new conversation (per CLAUDE.md). It translates [CLAUDE.md](CLAUDE.md) and [PRD.md](PRD.md) into the concrete architecture, stack, and workflow used to build Settle-Up. If anything here conflicts with the PRD, the PRD wins — update this file to match.

## 1. Product Snapshot

Settle-Up computes who-owes-who at the end of a buy-in-based game night (poker, board games). A player enters each participant's buy-in and final balance; a Flask backend validates the numbers, computes each player's net, and returns the minimum set of transactions to zero everyone out — always showing the underlying math. Built for Nathan and his regular game group; deliberately not a general ledger/expense-splitting app.

Current phase: **M1 — MVP** (see §7). Do not build ahead of the current milestone.

## 2. Architecture

### 2.1 System Shape

```
┌─────────────────────┐         HTTPS/JSON          ┌──────────────────────┐
│  Mobile App (Expo)  │ ───────────────────────────▶ │   Flask API (Python) │
│  React Native       │ ◀─────────────────────────── │   /api/settlement    │
└─────────┬────────────┘                              └──────────┬───────────┘
          │                                                       │
          ▼                                                       ▼
  AsyncStorage (local)                              settle.py — pure function
  recent-game persistence                           (net calc, greedy match,
                                                       breakdown/trace)
```

- **Client is dumb by design.** The mobile app never computes nets or settlements itself — every calculation round-trips through the Flask API (PRD §5.3 design note, CLAUDE.md "Core Domain Rules"). This is a deliberate choice, not a placeholder for a later refactor.
- **The algorithm is isolated.** `backend/app/services/settle.py` is a pure function: plain domain objects (integer cents) in, plain domain objects out. No Flask, no I/O, no Pydantic. This is what makes 100% unit-test coverage tractable and keeps the door open for a future web client to hit the same endpoint unchanged (NFR-009).
- **Validation happens once, at the boundary.** Pydantic models in `models/game.py` are the only place dollars-in-JSON convert to integer-cents-internally. `settle.py` never sees a float or a raw dollar amount.
- **Every response — success or error — carries its full breakdown.** This isn't a debug feature; it's the product's core value proposition (transparency > bare answer). Never trim it, even under pressure to "simplify" a response shape.

### 2.2 Repository Layout (MVP target)

```
Settle-Up/
├── backend/                    # Flask API
│   ├── app/
│   │   ├── __init__.py         # empty
│   │   ├── main.py             # Flask app factory (create_app) + smoke-tested main()
│   │   ├── routes/
│   │   │   ├── __init__.py     # empty
│   │   │   └── settlement.py   # POST /api/settlement — thin glue only
│   │   ├── services/
│   │   │   ├── __init__.py     # empty
│   │   │   └── settle.py       # pure settlement algorithm
│   │   └── models/
│   │       ├── __init__.py     # empty
│   │       └── game.py         # Pydantic request/response schemas, $ -> cents
│   ├── tests/
│   │   ├── __init__.py         # empty
│   │   └── test_settle.py
│   └── pyproject.toml
└── mobile/                     # React Native (Expo)
    ├── src/
    │   ├── screens/             # PlayersScreen, ResultsScreen
    │   ├── components/          # PlayerRow, PrimaryButton, BreakdownSection
    │   ├── domain/               # money/validation helpers, no Flask/IO
    │   ├── storage/             # AsyncStorage — draft-recovery of in-progress game
    │   ├── api/                 # settlement.js + config.js (LAN host resolution)
    │   └── theme.js              # light/dark palettes, useColorScheme-driven
    ├── App.js                   # top-level view state machine (players <-> results)
    └── package.json
```

`web/` joins this tree at M3 as a sibling to `mobile/`, sharing `backend/` unchanged — this is why the API boundary must stay clean from day one (PRD §12.2 project risk).

### 2.3 Data Flow: `POST /api/settlement`

1. Mobile client collects players (name, buy-in, final balance in dollars) and POSTs JSON.
2. Flask route (`routes/settlement.py`) hands the raw body to `SettlementRequest.model_validate(...)`.
3. Pydantic validates: non-negative buy-ins, unique names, well-formed decimals — and converts dollars → integer cents.
4. Route calls `compute_settlement(players)` in `settle.py` (pure, cents-only).
5. `settle.py`:
   - computes net = final_balance − buy_in per player,
   - checks nets sum to zero — if not, returns a reconciliation object (never a bare fail),
   - otherwise splits into debtors/creditors, greedily matches largest-to-largest until zeroed,
   - builds the full breakdown (sorted lists + match trace),
   - handles the defensive fractional-cent fallback if it ever occurs, recording who absorbed it and why.
6. Route serializes the result back to dollars for display and returns `200` (success) or `422` (`nets_do_not_reconcile` or other domain error), always with the full breakdown/reconciliation payload.

### 2.4 Key Architectural Invariants

These are load-bearing and should not be "cleaned up" away:

- **Cents internally, dollars only at the boundary.** Conversion happens exactly once, in `models/game.py`.
- **`settle.py` has no Flask/IO imports.** If it ever needs `request` or `jsonify`, that logic belongs in the route instead.
- **No silent fixes.** The rounding fallback always populates `breakdown.rounding_adjustment`; it's never applied quietly.
- **No client-side settlement math.** Even trivial-looking calculations (e.g. a quick net preview) go through the API, per the deliberate backend-first design decision (PRD §10.1).

## 3. Technology Stack

### 3.1 Backend

| Layer | Choice | Notes |
|---|---|---|
| Language | Python 3.11+ | |
| Package/env manager | uv | `uv sync`, `uv run ...` |
| Web framework | Flask ≥ 3.0.0 | thin route layer only |
| Validation/schemas | Pydantic ≥ 2.0.0 | request/response models, `$` ↔ cents boundary |
| CORS | flask-cors ≥ 6.0.0 | dev-only concern: lets Expo web reach `localhost` across ports; irrelevant to native mobile |
| Testing | pytest ≥ 7.0.0, pytest-cov ≥ 4.0.0 | function-based tests + fixtures, not classes |
| Numeric handling | `Decimal` at the API boundary, `int` (cents) internally | never `float` for money |

### 3.2 Mobile

| Layer | Choice | Notes |
|---|---|---|
| Framework | React Native via Expo | `~57.0.9` (current at scaffold time, Aug 2026); bare workflow explicitly not chosen for MVP |
| Language runtime | Node 18+ | |
| Core deps | `react` 19.x, `react-native` 0.86.x | |
| Local persistence | `@react-native-async-storage/async-storage` ^2.2.0 | recent-game save/restore only, no cloud sync |
| Networking | fetch-based client in `src/api/` calling `/api/settlement` | client owns no settlement logic; `src/api/config.js` derives the LAN host via `expo-constants` for physical-device testing |

### 3.3 Future (not built yet — do not scaffold early)

- **M3:** `web/` — React client joining the monorepo, sharing `backend/`.
- **M4:** shared design system/tokens across mobile + web.
- **M5:** hosted Flask deployment (host TBD), enabling cross-device history and game sharing.

## 4. Development Process / Workflow

### 4.1 TDD Loop (mandatory for `settle.py`)

1. Read PLANNING.md (this file), then check `TASKS.md` and `SCRATCHPAD.md` before starting.
2. Write the failing test(s) in `backend/tests/test_settle.py` first.
3. Run `uv run pytest` and confirm the new tests fail (not error — fail on the actual assertion).
4. Implement the minimum code in `settle.py` to pass.
5. Re-run the full suite plus coverage (`uv run pytest --cov=app --cov-report=term-missing`) — `settle.py` targets 100% coverage.
6. Do not edit a test to make it pass unless the test itself is provably wrong; if so, explain why before changing it.
7. Mark the corresponding item complete in `TASKS.md` immediately — don't batch updates.

Flask routes and Pydantic validation get integration-test coverage but no fixed percentage target. Mobile has no formal coverage target for MVP — manual/exploratory testing in Expo is acceptable.

### 4.2 Required Test Categories (every PR touching `settle.py` or the route)

1. **Unit** — `settle.py` in isolation (net calc, greedy match, breakdown construction).
2. **Integration** — Flask route + Pydantic validation + HTTP status/error shape.
3. **Regression** — the worked 3-player and 4-player PRD examples as fixed fixtures.

Required edge cases (CLAUDE.md "Testing Requirements"): worked 3-/4-player examples, single debtor/creditor, already-settled (all-zero) input, mismatched nets (error path + correct reconciliation math), duplicate names, negative buy-ins, malformed input, and the defensive rounding fallback forced deliberately. Every success and error response must assert the full breakdown/reconciliation fields are present.

### 4.3 Coding Conventions

- PEP 8, type hints on all public functions.
- Docstrings only where behavior isn't obvious from the signature.
- Functions over classes for tests; share setup via pytest fixtures.
- Prefer short, single-purpose functions over long ones.
- `__init__.py` files stay empty.
- No new dependencies outside widely-used packages (Flask/Pydantic/pytest ecosystem, numpy/pandas/scikit-learn if ever needed) — avoid unknown/unvetted GitHub packages.
- Always add a smoke test for any `main()` entry point.

### 4.4 Session Workflow

- Start of every conversation: read `PLANNING.md` → check `TASKS.md` and `SCRATCHPAD.md`.
- Use `SCRATCHPAD.md` to sketch a plan before implementing something non-trivial.
- Update `TASKS.md` the moment a task completes, and add newly discovered tasks there as they surface — don't let it drift from reality.
- Keep `PRD.md` and `CLAUDE.md` in sync as decisions get made; this file (`PLANNING.md`) should be updated alongside them when architecture/stack/process decisions change.
- Solo-project git workflow: commits/branches as convenient, no PR review process required (PRD §8). No CI pipeline required at this stage.
- No formal versioning pre-1.0; tag a release once the MVP is usable at an actual game night.

### 4.5 Definition of Done (per component)

- [ ] Unit tests written and passing, including required edge cases (§4.2)
- [ ] Public functions have type hints
- [ ] Error cases return specific, actionable messages (never generic "invalid input" — NFR-003)
- [ ] Cents/dollars boundary respected — conversion only in `models/game.py`
- [ ] Success and error responses both include full breakdown/reconciliation fields
- [ ] No perceptible delay for a normal-sized game (NFR-005)

## 5. Required Tools

### 5.1 Local Environment

- **Python 3.11+** with **uv** (backend package/env management, task running)
- **Node 18+** with **npm** (mobile package management)
- **Expo CLI** (`npx expo start`) for running the mobile app — no separate global install required
- A simulator/device: iOS Simulator (Xcode) and/or Android Emulator (Android Studio), or the Expo Go app on a physical device
- **git** for version control

### 5.2 Backend Commands

```bash
cd backend
uv sync                                          # install deps
uv run pytest                                    # run tests
uv run pytest --cov=app --cov-report=term-missing  # tests + coverage
uv run flask --app app.main:create_app run --debug  # dev server
```

### 5.3 Mobile Commands

```bash
cd mobile
npm install
npx expo start
```

### 5.4 Not Required at This Stage

- No CI pipeline (manual/exploratory testing acceptable per PRD §6.1).
- No hosting/deployment tooling — that's M5 scope.
- No cross-repo/monorepo tooling (Nx, Turborepo, etc.) — `web/` and the monorepo unification are M3 scope; don't introduce this early.
- No design-system/component-library tooling — that's M4 scope.

## 6. Explicit Non-Goals (carried from PRD/CLAUDE.md — don't build these)

- Multi-currency, recurring shared expenses, accounts (not Splitwise).
- Real money movement / payment integration.
- Cloud sync or account-based history — local device storage only for now.
- Mid-entry editing of a live ledger — entries are a final pass after the game.
- Export/share sheet (nice-to-have, not required).
- Any in-game math (pot-splitting, live running ledger) — buy-in and final balance are always already-known, final numbers by entry time.

## 7. Implementation Phases (status)

- **M1 — MVP** *(current focus)*: backend skeleton, Pydantic models, `settle.py`, `/api/settlement` route, pytest suite, mobile add-player + entry screens, API client, local save/restore, dark mode.
- **M2 — History & Presets**: calculator history grouped by game, presets for recurring games.
- **M3 — Unified Codebase**: `web/` joins the monorepo, shares `backend/`.
- **M4 — Design Language**: shared design system across mobile and web.
- **M5 — Cloud Hosting**: host the Flask backend, cross-device history, game sharing.

Track granular, in-progress work items in `TASKS.md`, not here.

## 8. Resources

- [CLAUDE.md](CLAUDE.md) — project instructions and conventions (this file's sibling; keep in sync)
- [PRD.md](PRD.md) — source of truth for requirements
- `TASKS.md` — task tracker (check/update every session)
- `SCRATCHPAD.md` — working scratchpad for in-session planning
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Expo Documentation](https://docs.expo.dev/)
- [React Native AsyncStorage](https://react-native-async-storage.github.io/async-storage/)
