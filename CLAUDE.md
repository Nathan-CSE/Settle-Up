# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project Summary

Settle-Up is a mobile app that resolves who-owes-who at the end of a game night (poker, board games, any buy-in-based game). Users enter each player's buy-in and final balance; a Flask backend computes the minimum set of transactions needed to settle all debts, and every result (success or error) shows its underlying math. Target users: Nathan and his regular game group — a casual single-session utility, not a general ledger/expense-splitting app (not Splitwise).

Full detail lives in [PRD.md](PRD.md) — treat it as the source of truth for requirements. Keep this file and the PRD in sync as decisions get made during implementation.

## Repository Structure (MVP)

```
poker-calculator/
├── backend/                    # Flask API
│   ├── app/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   └── settlement.py   # POST /api/settlement
│   │   ├── services/
│   │   │   └── settle.py       # debt-simplification algorithm (pure function)
│   │   └── models/
│   │       └── game.py         # Player/Game request & response schemas
│   ├── tests/
│   │   └── test_settle.py
│   └── requirements.txt
└── mobile/                     # React Native app
    ├── src/
    │   ├── screens/
    │   ├── components/
    │   ├── storage/            # local/async storage for recent games
    │   └── api/                # client for backend endpoints
    └── package.json
```

`web/` (React) joins this layout at Milestone M3, unifying into a monorepo that shares `backend/`. Keep a clean API boundary between `backend/` and `mobile/` from the start so this migration stays low-friction.

## Core Domain Rules

- **Net** = final balance − buy-in, per player.
- Nets must sum to zero before a settlement is computed. If they don't, return the full reconciliation (total buy-ins, total final balances, exact delta) — never a bare pass/fail.
- Settlement is a **minimal-transaction** match: split into debtors (negative net) and creditors (positive net), greedily match largest debtor to largest creditor until zeroed out. Optimize for fewest transactions, not fewest dollars moved.
- Work in **integer cents** internally — never float — to avoid rounding drift. Only convert to dollars for display.
- Every computed response, success or error, includes a full breakdown: per-player net calculation, sorted debtor/creditor lists, and a step-by-step match trace. The transaction list is never returned without its supporting work. In the UI this breakdown is collapsed by default, expandable on demand ("show calculation").
- Reject negative buy-ins and duplicate player names at input, client and API side.
- The defensive fractional-cent fallback (leftover cent after matching) should not occur in normal operation given exact-cent inputs and the sum-to-zero check — but if it does, auto-assign the cent to a randomly chosen player and record exactly which player and why in the breakdown. Never fix it silently.
- Calculation is server-side by deliberate choice (not required for MVP scope, but preferred for flexibility/learning) — the mobile app always calls the backend for validation and settlement, never computes locally.
- No in-game math: buy-in and final balance are always already-known, final numbers by the time they're entered. The app never calculates or influences them (no pot-splitting, no live running ledger).

## Explicit Non-Goals (MVP)

- No multi-currency, recurring shared expenses, or accounts (not Splitwise).
- No real money movement / payment integration.
- No cloud sync or account-based history — local device storage only.
- No mid-entry editing of a live ledger — entries are a final pass after the game.
- No export/share sheet (nice-to-have, not required).
- No CI pipeline required at this stage; manual/exploratory testing is acceptable for the mobile UI.

## Testing Priorities

- The settlement algorithm (`settle.py`) is the highest-priority test target — isolate it as a pure, independently testable function decoupled from Flask route handling.
- Required coverage: worked 3-player and 4-player examples, single debtor/creditor, already-settled (all-zero) input, mismatched nets (error path with correct reconciliation math), duplicate names, negative buy-ins, malformed input, and the defensive rounding fallback forced deliberately.
- Every success and error response must be asserted to include its full breakdown/reconciliation fields.

## Milestones (for prioritization context)

- **M1 (MVP):** add players, buy-in + final balance entry, `/api/settlement` endpoint, input validation, local save/restore of last game, dark mode, mobile only.
- **M2:** calculator history grouped by game, presets for recurring games.
- **M3:** monorepo unifying mobile + web on the shared Flask backend.
- **M4:** shared design language across mobile/web.
- **M5:** cloud-hosted backend (cross-device history, sharing).

Don't build ahead of the current milestone unless asked.

---

## Development strategy

Use a test-driven development strategy, developing tests prior to generating solutions to the tests.

Run the tests and ensure that they fail prior to generating any solutions. Do not create mock versions of the code simply to pass the tests.

Write code that passes the tests.

IMPORTANT: Do not modify the tests simply so that the code passes. Only modify the tests if you identify a specific error in the test.

## Notes for Development

Think about the problem before generating code.

Always add a smoke test for the main() function.

Prefer reliance on widely used packages (such as numpy, pandas, and scikit-learn); avoid unknown packages from Github.

Do not include any code in init.py files.

Use pytest for testing.

Write code that is clean and modular. Prefer shorter functions/methods over longer ones.

Use functions rather than classes for tests. Use pytest fixtures to share resources between tests.

## Session Guidelines

Always read PLANNING.md at the start of every new conversation.

Check TASKS.md and SCRATCHPAD.md before starting your work.

Mark completed tasks immediately within TASKS.md.

Add newly discovered tasks to TASKS.md.

Use SCRATCHPAD.md as a scratchpad to outline plans.
