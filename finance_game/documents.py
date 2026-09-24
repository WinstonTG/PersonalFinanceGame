"""Validation and durable intake for student budget documents."""
import json
import math
import sqlite3
import uuid
from datetime import datetime, timezone

CATEGORIES = ('income', 'rent', 'food', 'utilities', 'transport', 'personal', 'fun', 'investment', 'savings')


def validate_document(document):
    if not isinstance(document, dict) or document.get('version') not in (1, 2):
        raise ValueError('Unsupported budget document; expected version 1 or 2.')
    ranged = document['version'] == 2
    if ranged and document.get('incomeRange') != {'min': 1500, 'max': 2100}:
        raise ValueError('Expected income range is 1500–2100 per month.')
    for field in ('name', 'title'):
        value = document.get(field)
        if not isinstance(value, str) or not value.strip() or len(value) > 100:
            raise ValueError(f'{field} is required (maximum 100 characters).')
    months = document.get('months')
    if not isinstance(months, list) or len(months) != 12:
        raise ValueError('Complete all 12 monthly budgets.')
    clean = {'version': document['version'], 'name': document['name'].strip(), 'title': document['title'].strip(), 'months': []}
    if ranged:
        clean['incomeRange'] = {'min': 1500, 'max': 2100}
    for index, month in enumerate(months, 1):
        if not isinstance(month, dict):
            raise ValueError(f'Month {index}: invalid budget.')
        row = {}
        for field in CATEGORIES:
            if ranged and field == 'income':
                continue
            value = month.get(field)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 100000:
                raise ValueError(f'Month {index}: enter {field} between 0 and 100000.')
            if abs(value * 100 - round(value * 100)) > 0.00001:
                raise ValueError(f'Month {index}: {field} needs at most two decimal places.')
            if field in ('fun', 'investment') and value > (400 if field == 'fun' else 500):
                raise ValueError(f'Month {index}: {field} exceeds the game limit.')
            row[field] = value
        notes = month.get('notes', '')
        if not isinstance(notes, str) or len(notes) > 2000:
            raise ValueError(f'Month {index}: notes must be text under 2000 characters.')
        row['notes'] = notes
        clean['months'].append(row)
    return clean


def save_document(database, document):
    clean = validate_document(document)
    receipt = str(uuid.uuid4())
    created = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(database) as connection:
        connection.execute('CREATE TABLE IF NOT EXISTS documents (receipt TEXT PRIMARY KEY, created TEXT NOT NULL, document TEXT NOT NULL)')
        connection.execute('INSERT INTO documents VALUES (?, ?, ?)', (receipt, created, json.dumps(clean)))
    return {'receipt': receipt, 'submittedAt': created}
