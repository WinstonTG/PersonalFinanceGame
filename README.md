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

Malformed rows produce an explicit error instead of being silently skipped.
