# Classroom Vercel readiness — 2026-09-24

## DEPLOY-01 — Static host offers unavailable submission workflow

- Category: deployment/correctness. Severity: medium. Confidence: high.
- Status: validated → reproduced by static proof → fixed → regression-tested → closed.
- Locations: `web/budget.js:9` capability check and `web/budget.js:103` submit handler;
  `web/budget.html:21` actions; `finance_game/server.py:26` capability endpoint;
  `scripts/build-web.mjs:1` public output; `vercel.json:1` deployment configuration.
- Trigger: open the workbook on a static host and click Submit to instructor.
- Flow: browser POSTs `/api/documents`; only the local Python server implements
  that route and durable SQLite persistence. No Vercel function exists.
- Expected: online students have a usable, accurately described hand-in path.
- Actual: the button is offered but produces a 404/405/501 or JSON parsing error.
  Existing error handling prevents false success, but cannot accept the plan.
- Impact: classroom hand-in confusion; no evidence of silently lost submissions.
- Safeguards considered: PDF/JSON export already works locally; the README
  acknowledges static-host limitations but the UI does not detect them.
- Remediation: default to PDF hand-in; enable direct submission only when the
  local server explicitly advertises it. Add an allowlisted static build and
  Vercel configuration, keeping private grader/backend files out of public output.
- Regression checks: real static output in an isolated browser, PDF/JSON export,
  draft persistence, private-path 404s, and existing local submission tests.
- Residual risk: no online submission database; PDF delivery remains external.
- Results: build succeeds; 41 Python, 8 JavaScript and 9 browser tests pass.
  Static-host tests cover exports, restore/import, unavailable storage, no POSTs,
  simulator operation and private-path 404s; existing local hand-in/grader tests pass.
- Rollback: revert this deployment-readiness commit and redeploy the prior version;
  no database/schema or student draft migration is needed.

## Scope decisions

### DEPLOY-02 — Python builder selected for a static student app

- Severity: medium; confidence high that Python was selected (user's exact build
  error). Whether stale deployment settings/commit or auto-detection caused that
  selection is unverified without deployment logs.
- Locations: `vercel.json:4`, `pyproject.toml:5`, `web/hosting.e2e.spec.js:10`.
- Trigger/impact: Vercel invokes Python entrypoint discovery; this repository has
  a local CLI grader, not an ASGI/WSGI app; deployment fails before publication.
- Prior safeguard: framework null + output directory only; the reported remote
  failure demonstrates local static-server tests did not validate builder selection.
- Fix: explicitly build only package.json with @vercel/static-build and publish
  dist. Keep Python packaging untouched. Legacy builder override is intentional;
  Vercel documents that explicit builds include only their outputs.
- Regression: require the single static builder and its build/output settings;
  rerun build and existing static/public-boundary tests.
- Status: validated from deployment error; fixed; local verification passed:
  npm build, 8 JavaScript tests, 9 browser tests and git diff --check. Remote
  deployment confirmation remains pending; local checks do not run Vercel itself.
- Residual risk: remote deployment success must still be confirmed; an old commit
  redeploy will not include this fix. Rollback: revert this targeted config commit.

- No claim that instructor data is currently exposed on Vercel: deployed URL and
  dashboard configuration are not available. Restricting public output is preventive.
- No new accounts, database, paid services, scoring changes or dependency upgrades.
- Browser drafts are device/site-specific, not cloud backups; document this plainly.
- Performance review limited to static asset size; no measured bottleneck justifies
  an optimization project for this classroom workload.
