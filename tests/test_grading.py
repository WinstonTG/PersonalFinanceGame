import pytest
from finance_game.documents import CATEGORIES
from finance_game.engine import run_simulation, summarize_months, FortuneConfig, GameConfig, iterate_simulation
from finance_game.grading import GradingSession
from finance_game.pdf_budget import parse_budget_text, LABELS, read_budget_pdf


def plan():
    row = dict.fromkeys(CATEGORIES, 0) | {'income': 2000, 'rent': 1000, 'food': 400, 'fun': 150, 'investment': 150, 'notes': ''}
    return {'version': 1, 'name': 'Student', 'title': 'Plan', 'months': [dict(row) for _ in range(12)]}


def test_incremental_budget_matches_classic_when_allocations_match():
    session = GradingSession(plan())
    assert session.snapshot()['months'] == []
    assert session.snapshot()['final'] is None
    for month in range(12):
        view = session.advance(month)
        assert len(view['months']) == month+1
        assert bool(view['final']) == (month == 11)
    assert view['final']['score'] == pytest.approx(run_simulation([150]*12,150).score)
    with pytest.raises(ValueError): session.advance(12)


def test_duplicate_advance_does_not_skip_a_month():
    session = GradingSession(plan());session.advance(0)
    with pytest.raises(ValueError):session.advance(0)
    assert len(session.months) == 1


def test_budget_values_cannot_invent_income_or_remove_required_bills():
    document = plan()
    for m in document['months']:
        m.update(income=99999,rent=0,food=0,investment=0,savings=99999)
    session = GradingSession(document)
    month = session.advance(0)['months'][0]
    assert month['income'] <= 2100
    assert month['rent_paid'] == 1000
    assert month['other_expenses_paid'] == 400
    assert month['savings_end'] >= 0


def test_monthly_investments_and_higher_expenses_are_used():
    document=plan();document['months'][0].update(investment=500,rent=1200,food=450)
    document['months'][1]['investment']=0
    session=GradingSession(document)
    first=session.advance(0)['months'][0]
    second=session.advance(1)['months'][1]
    assert first['investment_amount'] == 500
    assert first['rent_paid'] == 1200
    assert first['other_expenses_paid'] == 450
    assert second['investment_amount'] == 0


def test_pdf_text_requires_each_month_and_category_once():
    doc=plan()
    text='Budget document v1\nPlan\nStudent: Student · 12-month budget forecast · Starting cash: $3,000\n'
    for i,m in enumerate(doc['months'],1):
        text+=f'Month {i}\n'+''.join(f'{label} ${m[k]:,.2f}\n' for k,label in LABELS.items())+'Unassigned: $0.00 · Ending cash: $3000.00\n'
    assert parse_budget_text(text)==doc
    with pytest.raises(ValueError):parse_budget_text(text.replace('Month 12','Month 11'))
    with pytest.raises(ValueError):parse_budget_text(text.replace('Food & groceries $400.00','Food & groceries ???',1))
    with pytest.raises(ValueError):read_budget_pdf(b'not a PDF')


def test_forced_bad_fortunes_are_capped_and_unemployment_recovers():
    cfg=GameConfig(fortune=FortuneConfig(gift_chance=1,bad_fortune_chance=1,job_loss_chance=1))
    months=list(iterate_simulation([150]*12,config=cfg))
    assert sum(m.bad_fortune is not None for m in months)==2
    assert months[0].bad_fortune_cost==200
    assert months[1].income==0
    assert months[2].income>0
    assert months[1].gifts==50


def test_private_year_and_progress_survive_store_restart(tmp_path):
    from finance_game.grader import Store
    store=Store(tmp_path)
    session=GradingSession(plan(), store.seed)
    session.advance(0)
    store.save('student',session.snapshot())
    reopened=Store(tmp_path)
    assert reopened.seed==store.seed
    assert reopened.key==store.key
    assert reopened.load('student')==session.snapshot()
    other=GradingSession(plan(), reopened.seed)
    assert other.advance(0)==session.snapshot()


def test_older_rule_scores_are_excluded_from_current_leaderboard(tmp_path):
    from finance_game.grader import Store
    store=Store(tmp_path)
    session=GradingSession(plan(),store.seed)
    for i in range(12):session.advance(i)
    old=session.snapshot();del old['rulesVersion']
    store.save('older',old)
    entry=store.listing()[0]
    assert entry['outdated'] is True
    assert entry['score'] is None
