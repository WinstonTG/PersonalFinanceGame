import io

import pytest

from finance_game import SubmissionFormatError, read_submissions_csv, score_submissions
from finance_game.submissions import read_submissions_csv_lenient


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


def test_dollar_signs_and_spaces_are_tolerated():
    csv_text = 'name,invest,fun\nSpacey,$150,"150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150"\n'
    submissions = read_submissions_csv(io.StringIO(csv_text))

    assert submissions[0].investment_amount == 150
    assert submissions[0].fun_allocations == (150,) * 12


def test_google_forms_export_headers_and_extra_columns_are_accepted():
    csv_text = (
        "Timestamp,Name,Monthly auto-invest,Fun by month,Your plan\n"
        '9/24/2026 17:12:10,Balanced,150,"150,150,150,150,150,150,150,150,150,150,150,150","Emergency buffer: ..."\n'
    )
    submissions = read_submissions_csv(io.StringIO(csv_text))

    assert submissions[0].name == "Balanced"


def test_lenient_read_scores_good_rows_and_reports_bad_ones():
    csv_text = (
        "name,invest,fun\n"
        'Fine,100,"100,100,100,100,100,100,100,100,100,100,100,100"\n'
        'Eleven,100,"100,100,100,100,100,100,100,100,100,100,100"\n'
        'Typo,abc,"100,100,100,100,100,100,100,100,100,100,100,100"\n'
    )
    good, bad = read_submissions_csv_lenient(io.StringIO(csv_text))

    assert [item.name for item in good] == ["Fine"]
    assert len(bad) == 2
    assert bad[0].startswith("Eleven:") and "exactly 12" in bad[0]
    assert bad[1].startswith("Typo:") and "must be a number" in bad[1]
