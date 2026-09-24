# Personal Finance Game

## Hosting the classroom game on Vercel

Use the repository root as Vercel's **Root Directory** (not `web`). The committed
`vercel.json` selects **Other**, builds with `npm run build`, and publishes only
`dist`. No environment variables, Python service or database are required.
Make sure the deployed branch includes these changes (`fix/meeting-scorer`).
Redeploy after changing the settings or use the deployment created by the Git push.
The configuration follows [Vercel's static configuration reference](https://vercel.com/docs/project-configuration/vercel-json).

- `/` opens the practice game; `/budget.html` opens the student workbook.
- Students save a PDF and send it using your normal class hand-in method.
  Online direct submission is deliberately unavailable; the site is not a hosted inbox.
- Drafts live in the current browser/site only. A different device, private browsing,
  clearing storage, or a different preview URL will not carry them over. Download
  the completed JSON plan as a backup; it can be reopened in the workbook.
- The private grader stays on your computer. Grader code, databases, tests and
  repository files are excluded from the public build. No grading secrets are needed online.
- Keep using fictional game data. No login or sensitive financial information is needed.

Quick check before class: open the public URL in an incognito window, visit
`/budget.html`, fill all 12 months, save a PDF and import it into your local grader.
If Vercel asks students to log in, review your deployment's access settings before
sharing the link. Share the public app URL, not the `vercel.com` dashboard URL.

Local production-output check:

```sh
npm run build
python -m http.server 8003 --bind 127.0.0.1 --directory dist
```

The build copies only explicitly allowed student assets. Response headers in
`vercel.json` prevent framing/content sniffing and require revalidation of assets
so updated rules are not held in a long-lived browser cache. Local static preview
does not emulate Vercel's headers; verify those on the deployed URL.

## Private instructor PDF grader

Students send you the PDF exported by their workbook. Start the separate,
authenticated, local-only grader with:

```sh
python -m pip install pypdf==6.19.0
python -m finance_game.grader
```

Import a PDF, verify its figures, and simulate one month per click. Grades and
progress persist locally; the final graded PDF includes the score. See
[the grader guide](docs/private-grader.md) for access, supported PDFs, detailed
budget rules and exactly how misfortunes are calculated.

## Student budget documents

Start the submission-capable app from the repository root:

```sh
python -m finance_game.server
```

Open http://127.0.0.1:8001/budget.html. Students enter their name and title,
then complete each of 12 months: rent, food, utilities,
transport, personal essentials, fun, investment, and cash savings. Every field
starts with shared expense defaults where applicable: fixed $1,000 rent, $25 each for food, utilities and gas,
and $50 for personal essentials. Fun, investment and cash savings remain
blank for the student to choose; explicit zero is accepted. Existing draft values
are preserved except rent, which is always reset to $1,000. Missing baseline fields
are filled on restore. Use “Apply starting expenses to all months” to update an
existing draft's expense defaults without changing its other allocations or notes. Old income estimates
are replaced by the shared $1,500–$2,100 monthly range ($15 × 25–35 hours × 4 weeks).
Actual hours are generated in the grader. Notes explain the student's choices.
Copy previous month is optional. Drafts auto-save in that browser.

The worksheet shows ranges for unassigned income and projected cash carried forward from
$3,000. Savings stays in cash rather than being deducted twice. Underfunded
essentials and deficits are flagged for reflection; students may submit an
imperfect plan for instructor feedback. These forecasts are not scored game
results. The existing simulator and CSV competition scorer remain separate;
arbitrary student expenses do not alter official competition scores.

Download budget document creates a JSON file that can be reopened using Open
budget document. Print / Save PDF produces a readable full document containing
all categories and notes for every month. PDF files are for reading; import
uses the JSON format. Submission validates all months and stores the document
in submissions.sqlite3 on the host, returning a receipt. That database is ignored
by Git. A static HTTP server supports editing/export but cannot accept submissions.

Instructors export received plans using:

```sh
python -m finance_game.server --export
```

The command prints JSON containing receipt, timestamp and complete document for
every submission. Downloaded JSON files can be opened in the worksheet to review
or print them. No student documents are exposed by the static file server.
Back up submissions.sqlite3 to retain receipts and plans. Each submit creates a
new receipt; revisions are retained as separate submissions.

By default only this computer can connect. For a trusted classroom network,
run `python -m finance_game.server --bind 0.0.0.0` and give students this
computer's LAN address on port 8001. This is a local classroom tool without user
accounts, not a public hosted submission service. Do not collect account numbers
or real financial credentials.

This repository contains the first version of the game's month-by-month
simulation engine.

## Rules implemented

- 12 monthly turns, starting with $3,000 in savings.
- Randomly selected 25–35 work hours per week every month.
- Income uses 4 weeks per month at $15/hour.
- $1,000 fixed rent and $125 of other required expenses.
- A player supplies one monthly auto-invest amount from $0–$500 and twelve
  fun-spending allocations from $0–$400.
- Investments happen after required bills, cannot be withdrawn during the year,
  and grow by 0.8% monthly.
- Fun happiness uses a $0 baseline and a $400 maximum budget, with
  diminishing-return happiness points:
  `400 * (1 - exp(-fun / 150))`.
- Gifts have a 50% monthly chance and add $50.
- Bad fortune has a 10% monthly chance and can occur at most twice.
- Bad fortune reduces money and happiness and may cause one month of job loss.
- Required expenses are paid before investment and fun without allowing savings
  to go below $0. Unpaid rent costs 500 happiness points and unpaid other
  expenses cost 300 points.
- The final score is `ending savings + investment balance + total happiness`.
- All plans use the same hidden shared seed, so players face the same year.

## Run tests

```bash
python -m pytest
npm run test:ui
npm run test:e2e
```

Randomness can be replayed by passing a seeded `random.Random` instance to
`run_simulation`.

## Try the UI

Start the browser app from the repository root:

```bash
python -m http.server 8000 --directory web
```

Then open `http://localhost:8000`. Players can name a plan, set monthly
auto-investing and fun spending, and run the year to see ending savings,
investment growth, combined score, quality of life, events, and month-by-month
details.

## Score a submissions CSV

The scorer expects a header with `name`, `invest`, and `fun` columns. The `fun`
field must be quoted CSV text containing twelve comma-separated values:

```csv
name,invest,fun
Balanced,150,"150,150,150,150,150,150,150,150,150,150,150,150"
```

Run it with:

```bash
python -m finance_game.score submissions.csv
```

Dollar signs and spaces in the numbers are tolerated. Every well-formed row is
scored; malformed rows are listed under `COULD NOT SCORE` at the bottom with the
name and the reason, so a typo can be fixed in the CSV and the scorer rerun
without losing the rest of the leaderboard.

## Running it at a meeting

Participants do not get the simulator. They get a one-page case study with a
copy-paste prompt that makes their AI end its answer with two lines:

```
INVEST: <one number, 0 to 500>
FUN: <twelve numbers, 0 to 400, comma separated>
```

They enter those in a Google Form with these exact question titles, which the
scorer matches on:

| Question | Type |
| --- | --- |
| `Name` | Short answer |
| `Monthly auto-invest` | Short answer, number 0 to 500 |
| `Fun by month` | Short answer, twelve comma-separated numbers |
| `Your plan` | Paragraph, the pasted AI answer (ignored by the scorer) |

Download the responses as CSV from the form's Responses tab and run the scorer
on it. Everyone is scored against the same hidden shared year.
