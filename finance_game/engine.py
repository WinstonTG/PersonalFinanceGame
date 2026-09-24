"""Balanced, reproducible rules for the Personal Finance Game."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
import random
from typing import Sequence


MONTHS_IN_YEAR = 12
WEEKS_PER_MONTH = 4.33
SHARED_SEED = 20260924


class _SharedRandom:
    """Small cross-language PRNG matching the browser implementation."""

    def __init__(self, seed: int):
        self.value = abs(int(seed) or SHARED_SEED) % 2_147_483_647

    def random(self) -> float:
        self.value = (self.value * 16_807) % 2_147_483_647
        return (self.value - 1) / 2_147_483_646

    def randint(self, minimum: int, maximum: int) -> int:
        return int(self.random() * (maximum - minimum + 1)) + minimum


@dataclass(frozen=True)
class FortuneConfig:
    gift_amount: float = 50.0
    gift_chance: float = 0.50
    bad_fortune_chance: float = 0.10
    max_bad_fortunes: int = 2
    bad_fortune_money_loss: float = 200.0
    bad_fortune_happiness_loss: float = 35.0
    job_loss_chance: float = 0.50


@dataclass(frozen=True)
class GameConfig:
    starting_savings: float = 3_000.0
    hourly_wage: float = 15.0
    min_hours_per_week: int = 25
    max_hours_per_week: int = 35
    rent: float = 1_000.0
    other_expenses: float = 400.0
    min_fun: float = 0.0
    max_fun: float = 400.0
    max_investment: float = 500.0
    investment_monthly_return: float = 0.008
    fun_happiness_scale: float = 400.0
    fun_happiness_decay: float = 150.0
    no_fun_happiness_loss: float = 50.0
    missed_rent_happiness_loss: float = 500.0
    missed_other_expenses_happiness_loss: float = 300.0
    fortune: FortuneConfig = field(default_factory=FortuneConfig)


@dataclass
class SimulationState:
    savings: float
    investment_balance: float = 0.0
    happiness: float = 0.0
    bad_fortunes_seen: int = 0
    job_lost_this_month: bool = False


@dataclass(frozen=True)
class MonthResult:
    month: int
    hours_per_week: int
    income: float
    rent_paid: float
    other_expenses_paid: float
    requested_investment: float
    investment_amount: float
    investment_balance: float
    requested_fun: float
    fun_spending: float
    gifts: float
    bad_fortune: str | None
    job_lost: bool
    savings_end: float
    happiness_change: float
    happiness_end: float
    missed_rent: bool
    missed_other_expenses: bool
    food_shortage: bool


@dataclass(frozen=True)
class SimulationResult:
    months: tuple[MonthResult, ...]
    ending_savings: float
    investment_balance: float
    average_happiness: float
    total_happiness: float
    score: float


def fun_happiness(fun_spending: float, config: GameConfig | None = None) -> float:
    """Return diminishing-return happiness points for actual fun spending."""

    config = config or GameConfig()
    return config.fun_happiness_scale * (1 - math.exp(-fun_spending / config.fun_happiness_decay))


def _validate_config(config: GameConfig) -> None:
    if config.min_hours_per_week > config.max_hours_per_week:
        raise ValueError("min_hours_per_week cannot exceed max_hours_per_week")
    if config.min_fun < 0 or config.max_fun < config.min_fun:
        raise ValueError("fun range is invalid")
    if config.max_investment < 0:
        raise ValueError("max_investment cannot be negative")
    if config.fun_happiness_decay <= 0:
        raise ValueError("fun_happiness_decay must be positive")


def run_simulation(
    fun_allocations: Sequence[float],
    investment_amount: float = 0.0,
    *,
    config: GameConfig | None = None,
    rng: random.Random | None = None,
    seed: int = SHARED_SEED,
) -> SimulationResult:
    """Run one player's 12-month plan against one reproducible shared year.

    Bills are paid before investing, investing is capped by available cash, and
    the investment balance is locked until the final score.
    """

    config = config or GameConfig()
    rng = rng or _SharedRandom(seed)
    _validate_config(config)
    if len(fun_allocations) != MONTHS_IN_YEAR:
        raise ValueError("fun_allocations must contain exactly 12 monthly values")
    if any(not math.isfinite(value) or value < config.min_fun or value > config.max_fun for value in fun_allocations):
        raise ValueError(f"each fun allocation must be between {config.min_fun:g} and {config.max_fun:g}")
    if not math.isfinite(investment_amount) or investment_amount < 0 or investment_amount > config.max_investment:
        raise ValueError(f"investment_amount must be between 0 and {config.max_investment:g}")

    state = SimulationState(savings=config.starting_savings)
    results: list[MonthResult] = []

    for month, requested_fun in enumerate(fun_allocations, start=1):
        hours = rng.randint(config.min_hours_per_week, config.max_hours_per_week)
        job_lost = state.job_lost_this_month
        income = 0.0 if job_lost else config.hourly_wage * hours * WEEKS_PER_MONTH
        state.job_lost_this_month = False
        state.savings += income

        gifts = config.fortune.gift_amount if rng.random() < config.fortune.gift_chance else 0.0
        state.savings += gifts

        bad_fortune: str | None = None
        if (
            state.bad_fortunes_seen < config.fortune.max_bad_fortunes
            and rng.random() < config.fortune.bad_fortune_chance
        ):
            state.bad_fortunes_seen += 1
            state.savings = max(0.0, state.savings - config.fortune.bad_fortune_money_loss)
            bad_fortune = "bad_fortune"
            if not job_lost and rng.random() < config.fortune.job_loss_chance:
                state.job_lost_this_month = True
                bad_fortune = "job_loss_next_month"

        rent_paid = min(state.savings, config.rent)
        state.savings -= rent_paid
        other_expenses_paid = min(state.savings, config.other_expenses)
        state.savings -= other_expenses_paid
        missed_rent = rent_paid < config.rent
        missed_other_expenses = other_expenses_paid < config.other_expenses

        investment_amount_for_month = min(state.savings, investment_amount)
        state.savings -= investment_amount_for_month
        state.investment_balance += investment_amount_for_month

        fun_spending = min(state.savings, requested_fun)
        state.savings -= fun_spending
        state.investment_balance *= 1 + config.investment_monthly_return

        happiness_change = fun_happiness(fun_spending, config)
        if requested_fun == 0:
            happiness_change -= config.no_fun_happiness_loss
        if missed_rent:
            happiness_change -= config.missed_rent_happiness_loss
        if missed_other_expenses:
            happiness_change -= config.missed_other_expenses_happiness_loss
        if bad_fortune:
            happiness_change -= config.fortune.bad_fortune_happiness_loss
        state.happiness += happiness_change

        results.append(
            MonthResult(
                month=month,
                hours_per_week=hours,
                income=income,
                rent_paid=rent_paid,
                other_expenses_paid=other_expenses_paid,
                requested_investment=investment_amount,
                investment_amount=investment_amount_for_month,
                investment_balance=state.investment_balance,
                requested_fun=requested_fun,
                fun_spending=fun_spending,
                gifts=gifts,
                bad_fortune=bad_fortune,
                job_lost=job_lost,
                savings_end=state.savings,
                happiness_change=happiness_change,
                happiness_end=state.happiness,
                missed_rent=missed_rent,
                missed_other_expenses=missed_other_expenses,
                food_shortage=missed_other_expenses,
            )
        )

    total_happiness = sum(month.happiness_change for month in results)
    return SimulationResult(
        months=tuple(results),
        ending_savings=state.savings,
        investment_balance=state.investment_balance,
        average_happiness=total_happiness / MONTHS_IN_YEAR,
        total_happiness=total_happiness,
        score=state.savings + state.investment_balance + total_happiness,
    )


def rank_simulations(results: Sequence[SimulationResult]) -> list[SimulationResult]:
    """Rank players by the shared combined score."""

    return sorted(
        results,
        key=lambda result: (result.score, result.ending_savings, result.average_happiness),
        reverse=True,
    )
