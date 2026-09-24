import random

import pytest

from finance_game import FortuneConfig, GameConfig, fun_happiness, rank_simulations, run_simulation


def no_fortune_config(**overrides):
    fortune = FortuneConfig(gift_chance=0, bad_fortune_chance=0)
    return GameConfig(fortune=fortune, **overrides)


def test_simulation_uses_25_to_35_hours_and_433_weeks():
    result = run_simulation([200] * 12, config=no_fortune_config(), rng=random.Random(7))

    assert len(result.months) == 12
    assert all(25 <= month.hours_per_week <= 35 for month in result.months)
    assert all(month.income == month.hours_per_week * 15 * 4.33 for month in result.months)


def test_shared_seed_makes_repeated_plans_identical():
    first = run_simulation([200] * 12, 150)
    second = run_simulation([200] * 12, 150)

    assert first == second


def test_fun_happiness_has_diminishing_returns():
    assert fun_happiness(0) == pytest.approx(0)
    assert fun_happiness(100) == pytest.approx(195, abs=1)
    assert fun_happiness(200) == pytest.approx(294, abs=1)
    assert fun_happiness(400) == pytest.approx(372, abs=1)
    assert fun_happiness(400) - fun_happiness(300) < fun_happiness(100)


def test_investing_happens_after_bills_and_grows_monthly():
    result = run_simulation([0] * 12, 500, config=no_fortune_config())
    first = result.months[0]

    assert first.rent_paid == 1000
    assert first.other_expenses_paid == 400
    assert first.investment_amount == 500
    assert first.investment_balance == pytest.approx(504)
    assert result.investment_balance > 6_000


def test_investment_is_capped_when_cash_is_not_available():
    config = no_fortune_config(starting_savings=0, hourly_wage=0)
    result = run_simulation([400] * 12, 500, config=config, rng=random.Random(1))

    assert result.investment_balance == 0
    assert all(month.savings_end >= 0 for month in result.months)


def test_missed_expenses_are_not_double_penalized():
    config = no_fortune_config(starting_savings=0, hourly_wage=0)
    result = run_simulation([400] * 12, config=config, rng=random.Random(1))

    assert result.months[0].missed_rent and result.months[0].missed_other_expenses
    assert result.months[0].happiness_change == -800


def test_no_fun_penalty_uses_requested_budget():
    config = no_fortune_config(starting_savings=0, hourly_wage=0)
    no_budget = run_simulation([0] * 12, config=config, rng=random.Random(1))
    budgeted_but_unaffordable = run_simulation([400] * 12, config=config, rng=random.Random(1))

    assert no_budget.months[0].fun_spending == 0
    assert budgeted_but_unaffordable.months[0].fun_spending == 0
    assert no_budget.months[0].happiness_change - budgeted_but_unaffordable.months[0].happiness_change == -50


def test_bad_fortune_is_capped_and_job_loss_last_one_month():
    fortune = FortuneConfig(
        gift_chance=0, bad_fortune_chance=1, max_bad_fortunes=2,
        job_loss_chance=1, bad_fortune_money_loss=0, bad_fortune_happiness_loss=0,
    )
    result = run_simulation([200] * 12, config=GameConfig(fortune=fortune), rng=random.Random(3))

    assert sum(month.bad_fortune is not None for month in result.months) == 2
    job_loss_months = [month for month in result.months if month.job_lost]
    assert len(job_loss_months) == 1
    assert result.months[job_loss_months[0].month].income > 0


def test_combined_score_can_reward_quality_of_life():
    config = no_fortune_config()
    high_cash = run_simulation([0] * 12, config=config, rng=random.Random(1))
    high_quality = run_simulation([400] * 12, config=GameConfig(fortune=config.fortune, starting_savings=3_000), rng=random.Random(1))

    assert high_quality.score > high_cash.score
    assert rank_simulations([high_cash, high_quality])[0] is high_quality


def test_fun_allocations_and_investment_require_valid_inputs():
    with pytest.raises(ValueError):
        run_simulation([200] * 11)
    with pytest.raises(ValueError):
        run_simulation([401] * 12)
    with pytest.raises(ValueError):
        run_simulation([200] * 12, 501)
