import io
import pytest

from finance_game import run_simulation
from finance_game.submissions import read_submissions_csv_lenient


@pytest.mark.parametrize('bad', ['Broken,150', 'Broken', 'Bad,150,"' + ','.join(['nan'] * 12) + '"'])
def test_bad_row_does_not_prevent_valid_players_being_scored(bad):
    valid = 'Good,150,"' + ','.join(['150'] * 12) + '"\n'
    good, errors = read_submissions_csv_lenient(io.StringIO(
        'name,invest,fun\n' + valid + bad + '\n' + valid.replace('Good', 'Last')
    ))
    assert [p.name for p in good] == ['Good', 'Last']
    assert len(errors) == 1
    assert 'row 3' in errors[0]


@pytest.mark.parametrize('value', [float('nan'), float('inf'), -float('inf')])
def test_engine_rejects_nonfinite_budgets(value):
    with pytest.raises(ValueError):
        run_simulation([value] * 12)
    with pytest.raises(ValueError):
        run_simulation([150] * 12, value)
