"""CSV intake and leaderboard scoring for player plans."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, TextIO

from .engine import MONTHS_IN_YEAR, SimulationResult, run_simulation


@dataclass(frozen=True)
class PlanSubmission:
    name: str
    investment_amount: float
    fun_allocations: tuple[float, ...]


@dataclass(frozen=True)
class ScoredSubmission:
    submission: PlanSubmission
    result: SimulationResult


class SubmissionFormatError(ValueError):
    """Raised when a CSV row is malformed instead of silently dropping it."""


def _number(value: str, field: str, row_number: int) -> float:
    try:
        return float(value.strip().replace("$", "").replace(" ", ""))
    except (AttributeError, ValueError) as error:
        raise SubmissionFormatError(f"row {row_number}: {field} must be a number") from error


def _field(row: dict[str, str], names: tuple[str, ...], row_number: int) -> str:
    for name in names:
        if name in row:
            return row[name]
    raise SubmissionFormatError(f"row {row_number}: missing {names[0]} column")


def _parse_row(row: dict[str, str], row_number: int) -> PlanSubmission:
    name = _field(row, ("name", "Name"), row_number).strip()
    if not name:
        raise SubmissionFormatError(f"row {row_number}: name is required")

    investment = _number(
        _field(row, ("invest", "investment", "Monthly auto-invest"), row_number),
        "investment",
        row_number,
    )
    fun_text = _field(row, ("fun", "Fun by month"), row_number)
    fun_parts = [part.strip() for part in fun_text.split(",")]
    if len(fun_parts) != MONTHS_IN_YEAR:
        raise SubmissionFormatError(f"row {row_number}: fun must contain exactly 12 comma-separated values")
    fun = tuple(_number(value, "fun", row_number) for value in fun_parts)

    if not 0 <= investment <= 500:
        raise SubmissionFormatError(f"row {row_number}: investment must be between 0 and 500")
    if any(value < 0 or value > 400 for value in fun):
        raise SubmissionFormatError(f"row {row_number}: every fun value must be between 0 and 400")
    return PlanSubmission(name, investment, fun)


def parse_submission_rows(rows: Iterable[dict[str, str]]) -> list[PlanSubmission]:
    """Strict parse: the first malformed row raises."""

    return [_parse_row(row, row_number) for row_number, row in enumerate(rows, start=2)]


def parse_submission_rows_lenient(rows: Iterable[dict[str, str]]) -> tuple[list[PlanSubmission], list[str]]:
    """Room mode: score every good row, collect the bad ones by name and reason."""

    good: list[PlanSubmission] = []
    bad: list[str] = []
    for row_number, row in enumerate(rows, start=2):
        try:
            good.append(_parse_row(row, row_number))
        except SubmissionFormatError as error:
            who = (row.get("name") or row.get("Name") or "").strip() or "(no name)"
            bad.append(f"{who}: {error}")
    return good, bad


def read_submissions_csv(source: str | Path | TextIO) -> list[PlanSubmission]:
    if hasattr(source, "read"):
        return parse_submission_rows(csv.DictReader(source))
    with Path(source).open(newline="", encoding="utf-8-sig") as file:
        return parse_submission_rows(csv.DictReader(file))


def read_submissions_csv_lenient(source: str | Path | TextIO) -> tuple[list[PlanSubmission], list[str]]:
    if hasattr(source, "read"):
        return parse_submission_rows_lenient(csv.DictReader(source))
    with Path(source).open(newline="", encoding="utf-8-sig") as file:
        return parse_submission_rows_lenient(csv.DictReader(file))


def score_submissions(submissions: Iterable[PlanSubmission]) -> list[ScoredSubmission]:
    scored = [
        ScoredSubmission(submission, run_simulation(submission.fun_allocations, submission.investment_amount))
        for submission in submissions
    ]
    return sorted(scored, key=lambda item: (item.result.score, item.result.ending_savings), reverse=True)
