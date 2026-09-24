# Scorer reliability verification

Based on PR #1 (meeting-ready), September 24, 2026.

- Truncated CSV rows previously raised AttributeError before any leaderboard
  appeared. Missing fields now produce named, row-numbered errors while valid
  submissions continue. Both parser and CLI regressions cover this behavior.
- NaN budgets previously passed Python range checks and received a score.
  CSV intake and the engine now reject non-finite amounts.
- Blank browser investment input now requires an explicit amount; zero remains
  valid. Happiness is displayed in points, and monthly notes identify gifts
  and partially paid essentials.
- Browser currency formatting reuses one formatter across the plan and results.
- Browser tests start and stop their own loopback HTTP server.
- Four representative valid plans are compared between Python and JavaScript,
  including monthly income, investing, happiness, and final scores.

## Performance scope

Before changes, scoring 40 players averaged 1.78, 1.75, and 1.74 milliseconds
over three batches of 100 runs locally. This did not justify engine caching or
parallelism for the meeting workload. Gameplay weights and valid-plan scores
are preserved; no new balance claim is made by these changes.

## Reproduce

Install Python test dependencies and Node.js, then run:

```sh
python -m pytest -q
npm ci
npx playwright install chromium
npm run test:ui
npm run test:e2e
```

Port 8000 must be available for browser tests. The parity regression requires
Node.js. To roll back these fixes, revert the fix commits while retaining the
meeting-ready baseline. That restores the documented validation defects.
