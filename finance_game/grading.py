"""Incremental grading of detailed student budgets."""
from dataclasses import asdict
from .documents import validate_document
from .engine import SHARED_SEED, iterate_simulation, summarize_months
RULES_VERSION = 'four-week-v2'


class GradingSession:
    def __init__(self, document, seed=SHARED_SEED):
        self.document = validate_document(document)
        self.months = []
        self.iterator = iterate_simulation(
            [m['fun'] for m in self.document['months']], seed=seed,
            monthly_budgets=self.document['months'],
        )

    def advance(self, expected_month):
        # Optimistic step check prevents double clicks/retries advancing twice.
        if expected_month != len(self.months):
            raise ValueError('Month changed. Reload the session before advancing.')
        if len(self.months) >= 12:
            raise ValueError('All 12 months have already been graded.')
        self.months.append(next(self.iterator))
        return self.snapshot()

    def snapshot(self):
        final = asdict(summarize_months(self.months)) if len(self.months) == 12 else None
        if final:
            del final['months']
        return {
            'rulesVersion': RULES_VERSION,
            'document': self.document, 'completedMonths': len(self.months),
            'months': [asdict(month) for month in self.months], 'final': final,
        }
