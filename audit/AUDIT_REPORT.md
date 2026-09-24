# Lightweight classroom deployment check — 2026-09-24

## Outcome and scope

The student app now has a tested static deployment path for Vercel. This was a
bounded classroom-readiness check, not an enterprise/security certification or
a scoring/balance redesign. No new accounts, paid services or dependencies.

## Architecture and findings

Browser → static public assets → local browser draft / PDF or JSON download.
Students deliver PDFs through the class hand-in method. The authenticated Python
grader and its data remain on the instructor's laptop. The optional local Python
classroom server retains direct submission to SQLite; it is not deployed to Vercel.

DEPLOY-01 (medium, high confidence) fixed: static hosting previously offered a
submission button without a corresponding backend. The static app now explains
PDF hand-in and only exposes direct submission after a server capability check.
An explicit nine-file build excludes private software/tests/data. Vercel config
sets the build/output and basic response headers, using the official
[configuration reference](https://vercel.com/docs/project-configuration/vercel-json).
See FINDINGS.md for evidence, regression coverage and rollback.

## Method and results

Reviewed entry points, manifests, lockfile, deployment/persistence boundaries and
existing tests. Validated the backend mismatch by tracing the actual browser
POST to its local-only handler; avoided adding an unneeded hosted database.
Tested a real static server serving the exact generated output separately from
the submission-capable server. Browser tests use isolated contexts/test data.

- Baseline: 41 Python + 8 JavaScript + 6 browser tests passed.
- Final: `npm run build`; `python -m pytest -q` (41);
  `npm run test:ui` (8); `npm run test:e2e` (9); `git diff --check` passed.
- New tests: output allowlist/private 404s; static simulator; browser persistence;
  JSON export/import; PDF generation; unavailable-storage warning; no submission POST.
- Existing tests still cover local submissions and actual PDF-to-private-grader flow.
- Mobile screenshot inspected: fields, hand-in instructions and actions are readable.
- Performance: nine public files total 36,375 uncompressed bytes, excluding optional
  external fonts. No runtime backend or per-player server state; no optimization needed.

## Limits and follow-up

No evidence that private data was exposed by the user's existing deployment;
that hypothesis was not promoted to a finding. Live deployment headers, selected
branch/root directory and public access remain unverified: the supplied URL is an
inaccessible Vercel dashboard link. No credentials or production data were accessed.
Tests emulate static file serving, not Vercel's edge routing or dashboard settings.
Browser validation used Chromium, not every mobile PDF-printing implementation.

Deploy the branch containing this commit with repository root as Root Directory,
then check the public Visit URL in incognito before class. Browser drafts are not
cloud backups; students should export completed plans and submit the PDF externally.
No remaining high/critical findings established within this scope.
