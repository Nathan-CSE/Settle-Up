# Development scratchpad

- Use this file to keep notes on ongoing development work.
- When the work is completed, clean it out from this file, so that the contents only reflect ongoing work.

## NOTES

- Backend M1 and mobile M1 (Expo scaffold, PlayersScreen/ResultsScreen, API client, AsyncStorage draft-recovery, dark mode) are both merged into `main` via PR #8. Manual in-browser/device click-through pass is still outstanding — still needs a real pass from Nathan (`cd mobile && npx expo start --web`, or Expo Go via LAN) before M1 mobile is considered fully verified.
- Hosting provider for M5 (homelab vs. AWS EC2) still open — not blocking, M5 is not current milestone.
- In progress on branch `docs/readme-reflection`: replacing the placeholder root README with Nathan's project reflection (overview, tech stack, dev-process retrospective). Pulled supporting assets from the Obsidian vault into `docs/`: `docs/images/hero.jpeg`, `docs/images/low-fidelity-prototypes.png`, `docs/prototype.pdf`, and `docs/pr-7-review.md` (the pr-to-obsidian-generated review note for PR #7, linked from the README as a worked example of the review workflow).