# Personal Finance Game

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
