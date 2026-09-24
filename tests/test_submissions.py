import io

import pytest

from finance_game import SubmissionFormatError, read_submissions_csv, score_submissions


def test_csv_submission_requires_three_fields_but_accepts_twelve_fun_values():
    csv_text = "name,invest,fun\nBalanced,150,200,200,200,200,200,200,200,200,200,200,200\n"
    # The commas in the fun plan must be quoted in a real CSV export.
    csv_text = 'name,invest,fun\nBalanced,150,"200,200,200,200,200,200,200,200,200,200,200,200"\n'
    submissions = read_submissions_csv(io.StringIO(csv_text))

    assert submissions[0].name == "Balanced"
    assert submissions[0].investment_amount == 150
    assert len(submissions[0].fun_allocations) == 12


@pytest.mark.parametrize(
    "csv_text, message",
    [
        ('name,invest,fun\nBad,150,"1,2,3"\n', "exactly 12"),
        ('name,invest,fun\nBad,501,"0,0,0,0,0,0,0,0,0,0,0,0"\n', "between 0 and 500"),
        ('name,invest,fun\nBad,150,"0,0,0,0,0,0,0,0,0,0,0,401"\n', "between 0 and 400"),
    ],
)
def test_malformed_rows_are_reported(csv_text, message):
    with pytest.raises(SubmissionFormatError, match=message):
        read_submissions_csv(io.StringIO(csv_text))


def test_scored_submissions_are_ranked_by_combined_score():
    csv_text = 'name,invest,fun\nSaver,500,"0,0,0,0,0,0,0,0,0,0,0,0"\n' \
        'Quality,0,"400,400,400,400,400,400,400,400,400,400,400,400"\n'
    scored = score_submissions(read_submissions_csv(io.StringIO(csv_text)))

    assert scored[0].result.score >= scored[1].result.score
    assert all(item.result.investment_balance >= 0 for item in scored)
