"""Read the visible tables in PDFs exported by the student workbook."""
import io
import re
from pypdf import PdfReader
from pypdf.errors import PyPdfError
from .documents import validate_document

LABELS = {
    'income': 'Expected income', 'rent': 'Rent', 'food': 'Food & groceries',
    'utilities': 'Utilities & phone', 'transport': 'Transportation',
    'personal': 'Personal essentials', 'fun': 'Fun & activities',
    'investment': 'Investment', 'savings': 'Cash savings',
}


def parse_budget_text(text):
    text = text.replace('\u00a0', ' ')
    identity = re.search(r'Student:\s*(.*?)\s*·\s*12-month budget forecast', text, re.S)
    if not identity:
        raise ValueError('Student name not found. Use Print / Save PDF in the student workbook.')
    name = re.sub(r'\s+', ' ', identity[1]).strip()
    before = text[:identity.start()]
    if 'Budget document v1' in before:
        title = before.split('Budget document v1')[-1].strip()
    else:
        title = before.strip().splitlines()[-1] if before.strip() else 'Imported budget'
    title = re.sub(r'\s+', ' ', title).strip()
    headings = list(re.finditer(r'(?m)^\s*Month\s+(\d{1,2})\s*$', text))
    if [int(m[1]) for m in headings] != list(range(1, 13)):
        raise ValueError('Expected months 1–12 exactly once, in order. Export the complete workbook PDF again.')
    months = []
    for index, heading in enumerate(headings):
        block = text[heading.end():headings[index+1].start() if index < 11 else len(text)]
        # Only table content precedes Unassigned. Notes are never read as amounts.
        table, separator, tail = block.partition('Unassigned:')
        if not separator:
            raise ValueError(f'Month {index+1}: missing budget summary.')
        row = {}
        for key, label in LABELS.items():
            pattern = r'\s*'.join(re.escape(word) for word in label.split())
            values = re.findall(pattern + r'\s*\$\s*([0-9]+(?:,[0-9]{3})*\.[0-9]{2})', table)
            if len(values) != 1:
                raise ValueError(f'Month {index+1}: could not read {label} uniquely. Export again; do not use a scanned PDF.')
            row[key] = float(values[0].replace(',', ''))
        # Notes remain available in the source PDF; they do not affect scoring.
        row['notes'] = ''
        months.append(row)
    return validate_document({'version': 1, 'name': name, 'title': title, 'months': months})


def read_budget_pdf(data):
    if not data.startswith(b'%PDF-') or len(data) > 5 * 1024 * 1024:
        raise ValueError('Choose a PDF under 5 MB exported from the student workbook.')
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise ValueError('Password-protected PDFs are not supported. Export an unlocked PDF.')
        if not 1 <= len(reader.pages) <= 30:
            raise ValueError('PDF must contain 1–30 pages.')
        text = '\n'.join(page.extract_text() or '' for page in reader.pages)
    except (PyPdfError, OSError, KeyError, TypeError) as error:
        raise ValueError('Could not read this PDF. Export it again from the workbook.') from error
    if not text.strip():
        raise ValueError('This PDF has no readable text. Scans/photos need to be re-exported from the workbook.')
    return parse_budget_text(text)
