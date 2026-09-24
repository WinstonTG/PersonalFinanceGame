# Private PDF grader

The student workbook and instructor grader are separate programs. Students
complete the workbook, use Print / Save PDF, and send that PDF to the instructor
by their usual submission channel. They do not need access to the grader.

## Start on the grader's computer

From this repository, install the PDF dependency once and launch:

```sh
python -m pip install pypdf==6.19.0
python -m finance_game.grader
```

This opens an authenticated browser window at port 8002. The grader only listens
on 127.0.0.1; it cannot be bound to a classroom/public interface. Every page and
grading API requires its access key. The student server never serves the grader
files or database. A student on another laptop cannot connect.

The instructor's access link, private year seed and grades are stored under
`~/.personal-finance-grader/` with restricted filesystem permissions. If the
browser does not open, open `access.html` in that directory and click its link.
Do not share this link. Anyone with access to your OS account or authenticated
browser can use the grader. Use your computer's screen lock when away.

`--no-open` starts without opening a browser; `--port` changes the local port.
`--data-dir` selects a separate gradebook. A new directory creates a new random
year; reuse the same directory for all students in one competition. Back up the
entire directory, including settings.json and grades.sqlite3, to keep progress
and the same year. Never publish these files to the repository.

## Grading workflow

1. Choose one student's PDF. The importer reads the visible category tables,
   validates 12 complete months, and displays all extracted values.
2. Verify the student's identity and values against the original PDF link.
3. Click Confirm plan & simulate Month 1, then advance one month at a time.
   Future events and results are not sent to the browser before advancement.
4. Watch fortune events, planned-versus-actual spending, cash, investment balance,
   and happiness. Every advancement is saved locally. Reopen a saved student to
   resume; repeated/stale advancement requests cannot skip a month.
5. After Month 12, read the final score and its components. Print / Save graded
   PDF includes the results and score; Download full grading report exports JSON
   with the plan, all monthly results, and final score. Saved students are sorted
   by completed score. Each import is a distinct submission; duplicate uploads
   are not automatically merged or treated as new winners.

PDFs must be text-based exports from the workbook, including all 12 months.
Current exports and earlier workbook exports without the version heading are
supported. Prefer standard A4/Letter printing with browser headers/footers off.
Scans, photos, encrypted PDFs, altered layouts, files over 5 MB, and PDFs over
30 pages are rejected. Ambiguous/missing amounts produce an error instead of a
guessed grade. Original notes remain in the student's PDF and are not scored.
PDF extraction uses pypdf's text extraction:
https://pypdf.readthedocs.io/en/stable/user/extract-text.html

## Detailed-budget rules

These rules extend the classic fixed-investment game for monthly worksheets:

- Starting cash: $3,000. Actual wages use $15/hour, a random integer from 25–35
  hours/week, and 4.33 weeks/month. The student's income is an estimate, not a
  source of additional money.
- Rent due is the greater of $1,000 and planned rent. Other essentials due are
  the greater of $400 and the sum of food, utilities, transport and personal
  expenses. Individual essential categories are pooled because the case study
  only sets a combined $400 requirement. Zeroing a budget cannot erase bills.
- Bills are paid from cash before that month's planned investment (0–500), then
  fun (0–400). Transfers and spending are capped by available cash. Investment
  balance grows by 0.8% at month end and cannot pay bills.
- The cash savings entry is a target. Compare it with actual net cash saved;
  it is never deducted twice or awarded an extra bonus.
- Fun happiness: `400 * (1 - exp(-actual_fun / 150))`. Requested fun of zero
  costs another 50 points. Unpaid rent costs 500 points; unpaid other essentials
  costs 300 points, once. Bills do not create a separate debt ledger.
- Final score: ending cash + ending investments + total annual happiness.
  Average happiness is also displayed. Final scores require all 12 months.

## Fortune calculation

Each month rolls hours first, then a 50% chance of a $50 gift. A separate 10%
roll can trigger bad fortune until two events have occurred. Each bad event
takes up to $200 of cash and subtracts 35 happiness points. If employed, a
separate 50% roll also schedules job loss for the next month. This is a 5%
unconditional monthly job-loss-event chance only while employed and below the
two-event cap (10% × 50%). The cash hit still applies to a job-loss event.

Unemployment lasts one month; another event during unemployment does not extend
it. Gifts still occur during unemployment. If job loss is rolled in Month 12,
the wage loss is beyond the game's horizon; the immediate event penalty applies.
Gifts currently give cash only, with no direct happiness bonus.

One privately generated seed is retained in the instructor's settings. Every
student experiences exactly the same hours, gifts and events, independently of
their plan. It is distinct from the public practice simulator's seed. No market
volatility or extra random grading bonuses are introduced.

## Verification

`python -m pytest -q`, `npm run test:ui`, and `npm run test:e2e` cover legacy
score parity, detailed expenses, varying investments, required-bill floors,
job-loss recovery, durable progress, invalid PDFs, authentication and the actual
workbook PDF → import → 12 separate advances → final report workflow.
