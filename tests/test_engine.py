import random

import pytest

from finance_game import FortuneConfig, GameConfig, rank_simulations, run_simulation


def no_fortune_config(**overrides):
    fortune = FortuneConfig(gift_chance=0, bad_fortune_chance=0)
    return GameConfig(fortune=fortune, **overrides)


def test_simulation_runs_twelve_months_with_random_hours_and_433_weeks():
    result = run_simulation([200] * 12, config=no_fortune_config(), rng=random.Random(7))

    assert len(result.months) == 12
    assert all(20 <= month.hours_per_week <= 30 for month in result.months)
    assert all(month.income == month.hours_per_week * 15 * 4.33 for month in result.months)
    assert result.ending_savings > 0


def test_fun_happiness_is_zero_at_200_and_maximum_at_400():
    config = no_fortune_config()
    at_baseline = run_simulation([200] * 12, config=config, rng=random.Random(1))
    at_max = run_simulation([400] * 12, config=config, rng=random.Random(1))

    assert all(month.happiness_change == 0 for month in at_baseline.months)
    assert all(month.happiness_change == 200 for month in at_max.months)


def test_unaffordable_required_expenses_do_not_make_savings_negative():
    config = no_fortune_config(starting_savings=0, hourly_wage=0)
    result = run_simulation([400] * 12, config=config, rng=random.Random(1))

    assert result.ending_savings == 0
    assert all(month.savings_end >= 0 for month in result.months)
    assert all(month.missed_rent and month.missed_other_expenses for month in result.months)
    assert result.average_happiness < 0


def test_bad_fortune_is_capped_and_job_loss_last_one_month():
    fortune = FortuneConfig(
        gift_chance=0,
        bad_fortune_chance=1,
        max_bad_fortunes=2,
        job_loss_chance=1,
        bad_fortune_money_loss=0,
        bad_fortune_happiness_loss=0,
    )
    result = run_simulation([200] * 12, config=GameConfig(fortune=fortune), rng=random.Random(3))

    assert sum(month.bad_fortune is not None for month in result.months) == 2
    job_loss_months = [month for month in result.months if month.job_lost]
    assert len(job_loss_months) == 1
    recovered_month = result.months[job_loss_months[0].month]
    assert recovered_month.income > 0


def test_rank_uses_savings_then_average_happiness():
    low_savings = run_simulation([200] * 12, config=no_fortune_config(starting_savings=1_000), rng=random.Random(1))
    high_savings = run_simulation([0] * 12, config=no_fortune_config(starting_savings=2_000), rng=random.Random(1))

    assert rank_simulations([low_savings, high_savings])[0] is high_savings


def test_fun_allocations_require_twelve_values_and_valid_amounts():
    with pytest.raises(ValueError):
        run_simulation([200] * 11)
    with pytest.raises(ValueError):
        run_simulation([401] * 12)
