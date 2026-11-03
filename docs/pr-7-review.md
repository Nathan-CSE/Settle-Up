---
type: pr-review
repo: Nathan-CSE/Settle-Up
pr: 7
url: https://github.com/Nathan-CSE/Settle-Up/pull/7
pr_author: Nathan-CSE
branch: "`feat/mobile-expo-scaffold` -> `main`"
status: closed
created: 2026-08-07T12:05
updated: 2026-11-03T14:50
---
# Review Summaries
---
**Commented** -- @Nathan-CSE -- [view on GitHub](https://github.com/Nathan-CSE/Settle-Up/pull/7#pullrequestreview-4872271254)
> good initial changes, some tweaks to UI required (e.g. make dark more more visible, make text output consistent, add more transparency through dialogues)
> 
> need to clarify negative final balances, include status codes for errors to make them more informative

# Inline Comments
---
## `backend/app/main.py`
**Line 13** -- @Nathan-CSE -- [view on GitHub](https://github.com/Nathan-CSE/Settle-Up/pull/7#discussion_r3712784145)
> We have to run `uv run flask --app app.main run --debug --host=0.0.0.0` to run our flask server because:
> - `uv run`: We are using `uv` for dependancy management, so `uv run <cmd>` executes the command inside the project's `.venv` without us needing to `source .venv/bin/activate` first
> - `flask…run --debug` is normal Flask CLI
> - `--app app.main`: We need this because we use `main.py` instead of `app.py` which is what Flask's auto-discovery tries to look for. We have it set up like `main.py`, as we're using the app-factory pattern (i.e. `create_app`)
> - `--host=0.0.0.0`: Flask's dev server defaults to binding only `127.0.0.1`, but Expo connects over LAN IP which is different, so we need this flag so that Flask listens on all interfaces
> 
> This is expo go's listening IP address:
> › Scan the QR code above to open in Expo Go.
> › Metro: exp://192.168.1.35:8081
> › Web: http://localhost:8081
> 
> This is flask listening on all interfaces - normally it would only be running on `127.0.0.1`:
> › Serving Flask app 'app.main'
> › Debug mode: off
> WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
> › Running on all addresses (0.0.0.0)
> › Running on http://127.0.0.1:5000
> › Running on http://192.168.1.35:5000

**Line 15** -- @Nathan-CSE -- [view on GitHub](https://github.com/Nathan-CSE/Settle-Up/pull/7#discussion_r3712588631)
> Blueprints are a feature of Flask that allows us to split API routes across multiple files/modules without needing a shared `app` instance. Without blueprints, we would be cramming every `@app.route` into one file and if we were splitting it across multiple files, we would need to pass `app` around into other modules and call `.route()` which is poor coding practice.

**Line 15** -- @Nathan-CSE -- [view on GitHub](https://github.com/Nathan-CSE/Settle-Up/pull/7#discussion_r3712602589)
> If we check inside `settlement.py`, we can see the modular route that we've defined

## `mobile/src/api/settlement.js`
**Line 1** -- @Nathan-CSE -- [view on GitHub](https://github.com/Nathan-CSE/Settle-Up/pull/7#discussion_r3726605479)
> in summary: because network errors are unpredictable across platforms/browsers, we attempt to wrap them in our own error class. not bad, but some further context (such as status codes) would be helpful

**Line 9** -- @Nathan-CSE -- [view on GitHub](https://github.com/Nathan-CSE/Settle-Up/pull/7#discussion_r3726527563)
> we extend the error class and add name and body to the object field, so we can show users the specific api error instead of a generic python error

**Line 20** -- @Nathan-CSE -- [view on GitHub](https://github.com/Nathan-CSE/Settle-Up/pull/7#discussion_r3726528889)
> fetch API is a replacement for XML/HTTP requests and will create a promise for us, however it itself will throw on network-level failures (e.g. network-level failures, no connection, DNS failure), so we wrap it in a try/catch

**Line 32** -- @Nathan-CSE -- [view on GitHub](https://github.com/Nathan-CSE/Settle-Up/pull/7#discussion_r3726541180)
> this converts a raw network exception into a friendly SettlementApiError for the user

**Line 40** -- @Nathan-CSE -- [view on GitHub](https://github.com/Nathan-CSE/Settle-Up/pull/7#discussion_r3726569085)
> we call response.json() regardless of status code. in this case, the fetch succeeded and we got an HTTP response, but its body isn't valid JSON (e.g. the server crashed and returned an HTML error page, or truncated output - basically something external network related that we can't exactly know for sure). If we get an error like that then we catch it and turn it into a SettlementApiError

**Line 48** -- @Nathan-CSE -- [view on GitHub](https://github.com/Nathan-CSE/Settle-Up/pull/7#discussion_r3726578469)
> we throw an error if we get a status that wasn't 200, 400, 422

## `mobile/src/screens/PlayersScreen.js`
**Line 60** -- @Nathan-CSE -- [view on GitHub](https://github.com/Nathan-CSE/Settle-Up/pull/7#discussion_r3726629718)
> not the biggest fan of this currently - you can only add/remove players once, so if you make a tiny mistake/typo, you need to remove and add the player back. feedback would be to make the userfield/balances editable after being added, so they can be changed and only when we select 'settle-up' are the edits finalised until we get a response from the server

**Line 60** -- @Nathan-CSE -- [view on GitHub](https://github.com/Nathan-CSE/Settle-Up/pull/7#discussion_r3726748663)
> it could potentially be an interface where if you select a user/player it brings up an edit dialogue

**Line 117** -- @Nathan-CSE -- [view on GitHub](https://github.com/Nathan-CSE/Settle-Up/pull/7#discussion_r3726782162)
> should we allow users to have a negative final balance? does it make sense to just increase their initial buy in amount? not sure how to clarify this case

**Line 128** -- @Nathan-CSE -- [view on GitHub](https://github.com/Nathan-CSE/Settle-Up/pull/7#discussion_r3726756482)
> I quite like the idea of an edit 'dialogue', where you can edit their initial/final buy in, and also choose to delete - the two step process for deletion would also be good

**Line 128** -- @Nathan-CSE -- [view on GitHub](https://github.com/Nathan-CSE/Settle-Up/pull/7#discussion_r3726961640)
> this section also doesn't scroll so the app doesn't work when you have a lot of players at once

## `mobile/src/screens/ResultsScreen.js`
**Line 49** -- @Nathan-CSE -- [view on GitHub](https://github.com/Nathan-CSE/Settle-Up/pull/7#discussion_r3726850918)
> could potentially put a button that opens a dialogue box to explain how the auto-resolve algorithm works

**Line 86** -- @Nathan-CSE -- [view on GitHub](https://github.com/Nathan-CSE/Settle-Up/pull/7#discussion_r3726862029)
> need to tweak `body.breakdown`, so that it uses proper arrows, just tweak the backend

## `mobile/src/storage/gameStorage.js`
**Line 1** -- @Nathan-CSE -- [view on GitHub](https://github.com/Nathan-CSE/Settle-Up/pull/7#discussion_r3726830277)
> local async works well

## `mobile/src/theme.js`
**Line 18** -- @Nathan-CSE -- [view on GitHub](https://github.com/Nathan-CSE/Settle-Up/pull/7#discussion_r3726818784)
> border element is not very clear, hard to see in dark mode, change colour

**Line 27** -- @Nathan-CSE -- [view on GitHub](https://github.com/Nathan-CSE/Settle-Up/pull/7#discussion_r3726805901)
> this is not properly exposed, changes automatically depending on device theme - should be 3 options, light, dark and match system

# My Notes
---
# Minor Tweaks
*These I can add myself*
- Dark mode theme colour change for visibility
- Backend text output more consistent with frontend mobile UI

# Open Questions
- Need to clarify if users are allowed to have negative final balances

# Agent Feedback
- Modify UI to use dialogue menus for editing players, auto-resolve screen, settings
- Scrolling behaviour for players
- Explanation screens for ‘auto-resolve’ and ‘settlement explanation’

> [!NOTE] How does settlement work?
> Each player's net is calculated as final balance minus buy-in. A positive net means they're owed money; a negative net means they owe money.
> 
> Players are split into two groups: **debtors** (negative net) and **creditors** (positive net), each sorted from largest to smallest.
> 
> The algorithm matches the largest debtor with the largest creditor, and transfers the smaller of the two amounts between them. Whoever's fully settled drops out, and the process repeats with whoever's left, until everyone's net is zero.
> 
> This algorithm matching produces the fewest possible transactions needed to settle everyone up.
> 
> Every step of the matching is recorded, so you can see exactly who paid whom and why in the calculation breakdown.

> [!NOTE] How does auto-resolve work?
> When buy-ins and final balances don't quite match, the leftover amount (the delta) gets split evenly across every player's final balance.
> 
> Positive delta (balances too high): a small amount is deducted from each player's payout.
> 
> Negative delta (balances too low): a small bonus is added to each player's payout.
> 
> If splitting the delta would push someone's balance negative, they're excluded and their share moves to the rest — which can cascade if others are close to zero too. If it cascades until no one's left to absorb it, auto-resolve isn't offered and you'll need to fix the entry manually.
> 
> The split is always even across players, not weighted by buy-in size, and every resolution is shown in the calculation breakdown so nothing happens silently.

![[(2) Personal Projects/Settle-Up/prototype.pdf]]