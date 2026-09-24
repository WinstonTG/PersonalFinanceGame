# Personal Finance Game

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
then complete each of 12 months: estimated income, rent, food, utilities,
transport, personal essentials, fun, investment, and cash savings. Every field
starts with the shared income/expense defaults where applicable: $1,948.50
expected income (30 hours/week), $1,000 rent, $250 food and $50 each for utilities,
transportation and personal essentials. Fun, investment and cash savings remain
blank for the student to choose; explicit zero is accepted. Existing draft values
are preserved, with missing baseline fields filled on restore. Notes explain the student's choices.
Copy previous month is optional. Drafts auto-save in that browser.

The worksheet shows unassigned income and projected cash carried forward from
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
- Income uses 4.33 weeks per month at $15/hour.
- $1,000 rent and $400 of other required expenses.
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
