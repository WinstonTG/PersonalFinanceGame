"""Command-line scorer for Google Forms CSV exports."""

from __future__ import annotations

import argparse
import sys

from .submissions import SubmissionFormatError, read_submissions_csv, score_submissions


def main() -> int:
    parser = argparse.ArgumentParser(description="Score Personal Finance Game submissions.")
    parser.add_argument("csv_file", help="CSV export with name, invest, and fun columns")
    args = parser.parse_args()
    try:
        scored = score_submissions(read_submissions_csv(args.csv_file))
    except (OSError, SubmissionFormatError) as error:
        print(f"Submission error: {error}", file=sys.stderr)
        return 2

    print("RANK | NAME | SCORE | SAVINGS | INVESTMENTS | AVG HAPPINESS")
    for rank, item in enumerate(scored, start=1):
        result = item.result
        print(
            f"{rank:>4} | {item.submission.name} | {result.score:>7.0f} | "
            f"${result.ending_savings:>7.0f} | ${result.investment_balance:>11.0f} | "
            f"{result.average_happiness:>13.1f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

