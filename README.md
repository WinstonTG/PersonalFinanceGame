# Personal Finance Game

This repository contains the first version of the game's month-by-month
simulation engine.

## Rules implemented

- 12 monthly turns, starting with $3,000 in savings.
- Randomly selected 20–30 work hours per week every month.
- Income uses 4.33 weeks per month at $15/hour.
- $1,000 rent and $400 of other required expenses.
- A player supplies one fun-spending allocation per month from $0–$400.
- Fun happiness is `fun spending - $200`: $200 is neutral and $400 is the
  maximum positive monthly contribution.
- Gifts have a 50% monthly chance and add $50.
- Bad fortune has a 10% monthly chance and can occur at most twice.
- Bad fortune reduces money and happiness and may cause one month of job loss.
- Required expenses are paid in order without allowing savings to go below $0.
  Unpaid expenses cause substantial happiness penalties.
- Players rank by ending savings, with average happiness as the tie-breaker.

## Run tests

```bash
python -m pytest
```

Randomness can be replayed by passing a seeded `random.Random` instance to
`run_simulation`.
