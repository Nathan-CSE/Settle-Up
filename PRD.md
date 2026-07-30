---
created: 2026-07-30
updated: 2026-07-30T20:31
---

# Product Requirement Document: Settle-Up

## 1. Executive Summary

**Project Name:** Settle-Up
**Version:** 0.1.0 (pre-MVP)
**Date:** July 2026
**Author:** Nathan

Settle-Up is a mobile app that resolves who-owes-who at the end of a game night (poker, board games, any buy-in-based game). Users enter each player's buy-in and final balance; the app computes the minimum set of transactions needed to settle all debts, backed by a shared Flask API, and always shows its work.

## 2. Project Overview

### 2.1 Purpose
Figuring out who pays whom after a home poker game is manual and error-prone once you have more than 3-4 players. The default fallback — everyone pays everyone — produces far more transactions than necessary. Settle-Up takes buy-in and cash-out numbers and outputs the smallest, clearest set of payments to zero everyone out, with a transparent breakdown of how it got there.

### 2.2 Scope
- Enter per-player buy-in and final balance — these are always already-known, final numbers by the time they're entered; the app never calculates or influences them
- Compute net position and a minimal-transaction settlement
- Persist recent games locally so a session survives closing the app
- Backend-driven calculation via a Flask API from day one (chosen deliberately over on-device calculation, see 5.3)
- Every computed result — success or error — is transparent: the app shows the underlying math, not just a final answer
- Mobile only for MVP; web and monorepo unification are explicit later milestones

### 2.3 Target Users
Nathan and his regular game group. This is a casual utility for a single game session, not a general ledger or expense-splitting app (i.e. not trying to be Splitwise) — no multi-currency, no recurring shared expenses, no accounts in MVP.

## 3. Functional Requirements

### 3.1 Input Handling
- **FR-001:** Accept any number of players (2+), each with a name/string identifier, buy-in amount, and final balance
- **FR-002:** Support decimal currency values (e.g. $12.50)
- **FR-003:** Buy-in is treated as a single fixed number per player for MVP. Rebuys during a session are handled by adjusting that player's initial buy-in rather than logging separate buy-in events (may revisit if this proves limiting in practice)
- **FR-004:** Entries are added during/after the game is manually tracked on paper/verbally, then entered as a final pass — not a live, continuously-edited running ledger. Add/remove-mid-entry editing is not a required MVP flow
- **FR-005:** Reject negative buy-in values at input (client and API validation) — a negative buy-in isn't meaningful and should never reach the settlement calculation
- **FR-006:** Require unique player names/identifiers within a game; reject duplicate names at input rather than letting an ambiguous "which Jason?" reach the settlement output

### 3.2 Settlement Calculation
- **FR-007:** Compute each player's net = final balance − buy-in
- **FR-008:** Validate that all nets sum to zero before computing a settlement. If they don't, show the full reconciliation — total buy-ins, total final balances, and the exact delta — not just a pass/fail error, so the user can see precisely what doesn't add up
- **FR-009:** Compute a minimal-transaction settlement: split players into debtors (negative net) and creditors (positive net), greedily match the largest debtor to the largest creditor until all balances are zero
- **FR-010:** Optimize for fewest transactions, not fewest total dollars moved
- **FR-011:** Settlement calculation runs server-side via the Flask API (not purely client-side), so the mobile app calls the backend for both validation and the settlement result
- **FR-012:** Every computed settlement response — success or error — includes a full breakdown: per-player net calculation, the sorted debtor/creditor lists, and a step-by-step trace of how transactions were matched. The transaction list is never returned as a bare result with no supporting work shown. In the UI, this breakdown is not shown by default — the primary view is just the transaction list (and the reconciliation summary on error). The breakdown is available on demand via an expand/dropdown ("show calculation"), so the detail is always there but never forced on the user
- **FR-013:** Because all inputs are exact-cent numbers (FR-002) and nets are validated to sum to zero (FR-008), the settlement algorithm should never produce a fractional-cent remainder in normal operation — this is a defensive fallback, not an expected case. If a leftover cent ever does occur (e.g. an unanticipated input shape or implementation bug), auto-assign it to a randomly chosen player and record exactly which player and why in the breakdown (FR-012), so the fallback is visible rather than silently "fixed"

### 3.3 History & Persistence (MVP)
- **FR-014:** Save the most recently entered game(s) in local device storage (e.g. AsyncStorage) so state survives the app closing or the phone restarting
- **FR-015:** No cloud sync or account-based history in MVP — local only
- **FR-016:** History is a personal record for Nathan's own reference, not something shared with other players; can be deprioritized/cut if it adds friction (nice-to-have, not core)

### 3.4 Out of Scope for MVP
- **FR-017:** Exporting/sharing a settlement summary (screenshot or share sheet) is a nice-to-have, not required — the target use case is casual, low-stakes game nights where this isn't essential
- **FR-018:** Real money movement or payment integration (Venmo/PayPal deep links, etc.) — the app tells you who pays whom, it does not move funds
- **FR-019:** No in-game math (e.g. splitting a chopped/tied pot between winners) — whatever happens during the game is decided and settled by the players themselves; the app strictly starts from an already-known buy-in and final balance per player

## 4. Non-Functional Requirements

### 4.1 Usability
- **NFR-001:** Input should be low-friction — numeric keypad, minimal taps to add a player — fast enough to use at the table
- **NFR-002:** No settings sprawl; dark mode is the one exception worth including for MVP
- **NFR-003:** Every validation failure (nets don't reconcile, negative buy-in, duplicate name) gives a specific, actionable message — never a generic "invalid input"
- **NFR-004:** The settlement breakdown (FR-012) is presented as a collapsed/expandable section, not inline by default — keeps the main result scannable while still letting the user drill into the math when they want it

### 4.2 Performance
- **NFR-005:** The app should feel instant despite calculation happening server-side — no visible loading spinners for a request this small; keep the settlement endpoint thin and fast

### 4.3 Reliability
- **NFR-006:** Settlement math must be exact to the cent; work in integer cents internally to avoid floating-point drift
- **NFR-007:** Input validation on both client and API (types/ranges of the request body, unique names, non-negative buy-ins, nets summing to zero)

### 4.4 Maintainability
- **NFR-008:** Keep the settlement algorithm isolated as a pure, independently testable function/module in the backend, decoupled from the Flask route handling
- **NFR-009:** Structure the backend so the same endpoints can later serve both the React Native app and a future React web client without changes

### 4.5 Compatibility
- **NFR-010:** Mobile app targets current iOS/Android via React Native (Expo or bare — TBD at implementation time)
- **NFR-011:** Backend targets a standard Python 3.x + Flask setup, deployable to any basic host for the later cloud-hosting milestone

## 5. Technical Architecture

### 5.1 Repository Structure (MVP)
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
Web (`web/`, React) joins this layout at Milestone M3, at which point the tree is unified into a proper monorepo sharing the same `backend/`.

### 5.2 Key Dependencies (indicative, confirm at implementation time)
- **Flask** — backend API
- **React Native** — mobile client
- **AsyncStorage** (`@react-native-async-storage/async-storage`) — local persistence
- **pytest** — backend unit tests

### 5.3 API Design

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
  "nets": [
    { "name": "Nathan", "net": 2.50 },
    { "name": "Jason",  "net": -15.00 },
    { "name": "Emily",  "net": 7.50 }
  ],
  "transactions": [
    { "from": "Jason", "to": "Nathan", "amount": 2.50 },
    { "from": "Jason", "to": "Emily",  "amount": 7.50 }
  ],
  "breakdown": {
    "debtors_sorted": [{ "name": "Jason", "amount": 15.00 }],
    "creditors_sorted": [{ "name": "Emily", "amount": 7.50 }, { "name": "Nathan", "amount": 2.50 }],
    "match_trace": [
      "Jason (owes $15.00) pays Emily (owed $7.50) -> $7.50; Jason now owes $7.50",
      "Jason (owes $7.50) pays Nathan (owed $2.50) -> $2.50; Jason now owes $5.00... continues until zero"
    ],
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
`rounding_adjustment` is populated only in the defensive fallback case (FR-013) and states which player absorbed the leftover cent and why, so that path is never silent.

**Design note:** calculation lives server-side by deliberate choice — it would work equally well fully client-side for MVP, but running it through the Flask API from day one is preferred for flexibility and as a learning exercise, even though it adds a network hop the UI needs to hide.

## 6. Testing Requirements

### 6.1 Test Strategy
- Unit tests for the settlement algorithm (`settle.py`) are the highest priority — this is the one place correctness really matters (worked examples from the original spec, e.g. the 3-player and 4-player cases, make good test fixtures)
- Manual/exploratory testing for the mobile UI is acceptable for MVP given the small scope; no CI pipeline required at this stage

### 6.2 Test Coverage
- Full coverage of the settlement algorithm, including edge cases: single debtor/creditor, already-settled (all zero) input, mismatched nets (error path with correct reconciliation math)
- Validation coverage: duplicate names rejected, negative buy-ins rejected, non-numeric/malformed input rejected
- Breakdown coverage: every success and error response includes the expected breakdown/reconciliation fields (FR-012)
- The defensive rounding fallback (FR-013) should have a test that forces the fallback path even though it isn't expected to occur with valid input, confirming it auto-assigns and reports correctly rather than crashing
- No formal coverage target for the mobile client at MVP

### 6.3 Test Data
- The worked examples from the original spec (3-player and 4-player games) as fixed test cases
- Synthetic cases for: duplicate names, negative buy-in, all-zero nets, mismatched nets

## 7. Documentation Requirements

- **README** per component (`backend/`, `mobile/`) covering setup and running locally
- Keep this PRD and the CLAUDE.md/AGENTS.md project-memory files in sync as decisions get made during implementation
- No public API docs or example notebooks needed — this is a personal project, not a distributed package

## 8. Development Methodology

- Git-based workflow; commits/branches as convenient for a solo project (no PR review process required)
- No strict TDD requirement, but the settlement algorithm should have tests written alongside it given how much correctness matters there (see 6.1)
- No formal versioning scheme needed pre-1.0; tag a release once MVP is usable at an actual game night

## 9. Deliverables / Milestones

**M1 — MVP**
- Add players, enter buy-in + final balance
- Flask `/api/settlement` endpoint computing net + minimal settlement transactions + breakdown
- Input validation: unique names, non-negative buy-ins, nets-reconcile check with full reconciliation math on failure
- Save/restore last game via local storage
- Dark mode
- Mobile only (React Native)

**M2 — History & Presets**
- Calculator history, grouped by game
- Presets for recurring games (saved names, default buy-in amounts)

**M3 — Unified Codebase**
- Monorepo: React Native (mobile) + React (web), sharing the Flask backend
- Web implementation of the same core flow

**M4 — Design Language**
- Shared mood board / design system across mobile and web

**M5 — Cloud Hosting**
- Host the Flask backend for fun/extensibility (enables cross-device history, sharing a game with other players, etc.)

## 10. Open Questions & Decisions Log

### 10.1 Resolved
- **Rebuys:** handled for MVP by adjusting a player's initial buy-in rather than logging discrete rebuy events; may revisit if this proves limiting in practice
- **Mid-entry editing:** not required — entries are a final pass after the game is tracked manually, not a live editable ledger
- **History purpose:** personal record only; low priority, can be cut if it adds unnecessary complexity
- **Settlement export/sharing:** nice-to-have, not required for the target casual/low-stakes use case
- **Backend vs. on-device calculation:** backend (Flask) preferred from MVP, for flexibility and as a learning exercise, despite being more than strictly necessary for MVP scope
- **In-game pot splitting:** not in scope. Final balances and buy-ins are always already-known numbers by the time they're entered — whatever happens during the game (chopped pots, side pots, etc.) is decided by the players themselves. The app never calculates a split; it strictly starts from buy-in + final balance
- **Odd-cent remainder:** given the above, this can't occur through normal use (nets are exact-cent inputs, transactions are just differences of exact numbers). Kept only as a defensive fallback: if it ever happens, auto-assign the leftover cent to a randomly chosen player and always show which player and why (FR-013)
- **Duplicate names:** rejected at input — names must be unique within a game
- **Negative buy-ins:** rejected at input
- **Transparency:** every computed settlement (success or error) includes a full breakdown of the calculation, not just the final answer (FR-012)

### 10.2 Still Open
- Exact React Native tooling choice (Expo vs. bare workflow)
- Hosting provider for the eventual M5 cloud deployment

## 11. Success Criteria

### 11.1 Functional
- A game with 4+ players can be entered and settled in under a minute
- Settlement output always matches manual verification (nets sum to zero, transaction count is minimal)
- Every result, success or error, shows its underlying math clearly enough that Nathan could verify it by hand without re-deriving it himself

### 11.2 Quality
- Settlement algorithm has test coverage for all worked examples plus edge cases (6.2)
- No floating-point rounding bugs in real usage

### 11.3 Adoption
- Nathan actually uses it at the next game night instead of doing the math by hand

## 12. Risk Assessment

### 12.1 Technical Risks
- **Risk:** Floating-point rounding errors in settlement math
  - **Mitigation:** work in integer cents internally; only convert to dollars for display
- **Risk:** Data entry mistakes cause nets to not reconcile
  - **Mitigation:** validate sum-to-zero before computing settlement, surface the full reconciliation math (FR-008)
- **Risk:** Network dependency (backend-driven calc) makes the app feel slow or breaks offline use
  - **Mitigation:** keep the endpoint minimal/fast; consider caching the last computed result locally so a poor connection doesn't block viewing a prior settlement
- **Risk:** Defensive rounding fallback (FR-013) never gets exercised in practice and silently rots
  - **Mitigation:** cover it with an explicit unit test that forces the fallback path (6.2), even though it shouldn't trigger from real input

### 12.2 Project Risks
- **Risk:** Scope creep toward a full ledger/expense-splitting app (Splitwise-like)
  - **Mitigation:** explicitly out of scope (2.3); defer multi-currency, recurring expenses, accounts to a genuinely separate project if ever pursued
- **Risk:** Monorepo migration (M3) becomes messy if backend/mobile are tightly coupled early
  - **Mitigation:** keep a clean API boundary between `backend/` and `mobile/` from the start (5.1) so `web/` can join later with minimal rework

## 13. Future Enhancements (Post-MVP)

- Settlement summary export/share sheet
- Multi-device history sync (enabled by M5 cloud hosting)
- Shared game links so other players can view (not edit) a settlement
- Unified design language across mobile/web (M4)

## 14. Notes

Personal project — no formal sign-off process. This PRD is a living document; update it (and CLAUDE.md/AGENTS.md) as decisions are made during implementation.
