# Progress

- Scope: Vercel static publication, student save/export/hand-in, private grader boundary.
- Inspected: README, manifests/lockfile, ignore rules, browser entry points,
  workbook styles, local server, existing unit/browser tests. No AGENTS files,
  CI workflow, deployment config, environment template or migrations found.
- Baseline: 41 Python, 8 JavaScript and 6 Playwright tests passed.
- DEPLOY-01 implemented: static hand-in guidance, local capability opt-in,
  allowlisted build, Vercel headers/config. New static-output regression tests added.
- Final: `npm run build`, 41 Python tests, 8 JavaScript tests, 9 Playwright tests
  and `git diff --check` pass. Mobile output screenshot inspected. Public assets
  total 36,375 bytes before compression (excluding optional Google Fonts).
- All scoped local workstreams complete; DEPLOY-01 closed. No dependency changes.
- Deferred: live Vercel verification. Supplied deployment-dashboard link was not
  accessible; public Visit URL requested. No production settings changed.
