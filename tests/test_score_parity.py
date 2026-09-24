import json
import subprocess
from pathlib import Path

import pytest

from finance_game import run_simulation


def test_browser_and_python_agree_for_valid_plans():
    plans = [
        {'fun': [0] * 12, 'invest': 0},
        {'fun': [150] * 12, 'invest': 150},
        {'fun': [400] * 12, 'invest': 500},
        {'fun': list(range(0, 360, 30)), 'invest': 317.25},
    ]
    output = subprocess.check_output(
        ['node', '--input-type=module', '-e',
         'import {runPlan} from "./web/simulation.js";'
         'const plans=JSON.parse(process.argv[1]);'
         'console.log(JSON.stringify(plans.map(p=>runPlan(p.fun,p.invest))));',
         json.dumps(plans)],
        cwd=Path(__file__).resolve().parents[1], text=True,
    )
    for plan, browser in zip(plans, json.loads(output)):
        result = run_simulation(plan['fun'], plan['invest'])
        assert result.score == pytest.approx(browser['score'])
        assert result.ending_savings == pytest.approx(browser['endingSavings'])
        assert result.investment_balance == pytest.approx(browser['investmentBalance'])
        for month, js_month in zip(result.months, browser['months']):
            assert month.income == pytest.approx(js_month['income'])
            assert month.happiness_change == pytest.approx(js_month['happinessChange'])
            assert month.investment_amount == pytest.approx(js_month['investmentAmount'])
            assert month.missed_rent == js_month['missedRent']


def test_cli_scores_valid_rows_around_a_truncated_row(tmp_path):
    path = tmp_path / 'submissions.csv'
    valid = 'First,150,"' + ','.join(['150'] * 12) + '"\n'
    path.write_text('name,invest,fun\n' + valid + 'Broken,150\n' + valid.replace('First', 'Last'))
    result = subprocess.run(
        ['python', '-m', 'finance_game.score', str(path)],
        capture_output=True, text=True, check=True,
        cwd=Path(__file__).resolve().parents[1],
    )
    assert 'First' in result.stdout and 'Last' in result.stdout
    assert 'COULD NOT SCORE (1)' in result.stdout
    assert 'Broken: row 3' in result.stdout
