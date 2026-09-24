import json
import sqlite3
import pytest
from finance_game.documents import validate_document, save_document, CATEGORIES


def document():
    return {'version':1,'name':'Student','title':'My budget','months':[
        dict.fromkeys(CATEGORIES, 0) | {'income':2000,'rent':1000,'food':400,'notes':'Build a buffer.'} for _ in range(12)]}


def test_saved_submission_is_durable_and_has_receipt(tmp_path):
    db=tmp_path/'submissions.sqlite3'
    doc=document()
    receipt=save_document(db,doc)
    with sqlite3.connect(db) as connection:
        row=connection.execute('SELECT receipt,document FROM documents').fetchone()
    assert row[0]==receipt['receipt']
    assert json.loads(row[1])==doc


@pytest.mark.parametrize('value',[None,True,float('nan'),-1,500.01])
def test_invalid_investment_not_saved(tmp_path,value):
    doc=document();doc['months'][5]['investment']=value
    db=tmp_path/'documents.sqlite3'
    with pytest.raises(ValueError):save_document(db,doc)
    assert not db.exists()


def test_missing_month_or_identity_rejected():
    doc=document();doc['months'].pop()
    with pytest.raises(ValueError):validate_document(doc)
    doc=document();doc['name']=' '
    with pytest.raises(ValueError):validate_document(doc)
