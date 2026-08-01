Push the current branch (if it has unpushed commits) and open a GitHub PR against `main` via `gh pr create`.

- Run `git log main..HEAD --oneline` to see every commit this PR would include, and `git diff main..HEAD --stat` for the full file-level shape of the change — the summary must cover all of it, not just the most recent commit.
- Run the project's test suite (see CLAUDE.md's Common Commands) and report actual pass/fail counts and coverage in the test plan — never claim a check passed without having run it this turn.
- Match the style of prior PRs in this repo (`gh pr list --state all`): a `## Summary` section (bullet per component/area touched) and a `## Test plan` checklist, ending with the `🤖 Generated with [Claude Code](https://claude.com/claude-code)` footer.
- If an open PR already exists for this branch, update it (`gh pr edit`) instead of creating a duplicate.
- Confirm the target branch and summary with me before running `gh pr create` if anything about scope is ambiguous (e.g. commits that look unrelated to the stated task).
