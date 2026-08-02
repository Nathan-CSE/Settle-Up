# Development scratchpad

- Use this file to keep notes on ongoing development work.
- When the work is completed, clean it out from this file, so that the contents only reflect ongoing work.

## NOTES

- Backend M1 (skeleton, models, `settle.py`, `/api/settlement`, opt-in discrepancy resolution) is complete: 37 tests passing, 100% coverage on `settle.py`.
- React Native tooling decision resolved: Expo confirmed for MVP mobile development (PRD §10.1, TASKS.md open questions). Hosting provider (homelab vs. AWS EC2) still open but is M5 scope — not blocking M1 work.
- Mobile M1 built on branch `feat/mobile-expo-scaffold`: Expo scaffold (SDK ~57.0.9, not the stale ~51.0.0 doc pin — CLAUDE.md/PLANNING.md updated to match), PlayersScreen + ResultsScreen, API client with LAN-host auto-detection (`expo-constants`), AsyncStorage draft-recovery, dark mode via `useColorScheme`.
- Added `flask-cors` to the backend (dev-only concern) so Expo web can call `localhost` across ports for local testing — irrelevant to native mobile usage.
- Backend confirmed working end-to-end via curl (`POST /api/settlement`) and Metro confirms the web bundle compiles/mounts cleanly. Full manual in-browser click-through pass is still outstanding — GUI scripting (Chrome automation, screenshots) is blocked in this environment (Accessibility/Automation permissions not granted), so this needs a real pass from Nathan: `cd mobile && npx expo start --web`, or Expo Go on a phone via LAN.
- Removed template cruft (`AGENTS.md`, `CLAUDE.md`, `.claude/`, `LICENSE`) that `create-expo-app` dropped into `mobile/` — conflicted with the repo's own root `CLAUDE.md` governance.