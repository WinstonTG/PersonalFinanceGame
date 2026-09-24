export const labels = {
  income: 'Expected income', rent: 'Rent', food: 'Food & groceries',
  utilities: 'Utilities & phone', transport: 'Transportation', personal: 'Personal essentials',
  fun: 'Fun & activities', investment: 'Investment', savings: 'Cash savings',
};
export const keys = Object.keys(labels);
export function blankDocument() {
  return { version: 1, name: '', title: '', months: Array.from({length:12}, () =>
    Object.fromEntries([...keys.map(key => [key, null]), ['notes', '']])) };
}
export function validateDocument(doc) {
  if (!doc || doc.version !== 1 || !Array.isArray(doc.months) || doc.months.length !== 12) throw Error('Use a version 1 budget document with 12 months.');
  for (const key of ['name','title']) if (typeof doc[key] !== 'string' || !doc[key].trim() || doc[key].length > 100) throw Error('Enter your name and plan title (up to 100 characters).');
  doc.months.forEach((month, i) => {
    for (const key of keys) {
      const value = month?.[key];
      const max = key === 'fun' ? 400 : key === 'investment' ? 500 : 100000;
      if (typeof value !== 'number' || !Number.isFinite(value) || value < 0 || value > max || Math.abs(value*100-Math.round(value*100)) > .00001)
        throw Error('Month '+(i+1)+': enter '+labels[key]+' from 0 to '+max+', with at most two decimal places.');
    }
    if (typeof month.notes !== 'string' || month.notes.length > 2000) throw Error('Month '+(i+1)+': notes must be text under 2000 characters.');
  });
  return doc;
}
export function forecast(doc) {
  let cash = 3000;
  return doc.months.map(month => {
    const complete = keys.every(k => typeof month[k] === 'number' && Number.isFinite(month[k]) && month[k] >= 0);
    const amount = key => Number.isFinite(month[key]) ? month[key] : 0;
    const expenses = ['rent','food','utilities','transport','personal','fun'].reduce((sum,k)=>sum+amount(k),0);
    const net = amount('income')-expenses-amount('investment');
    cash += net;
    return { complete, expenses, cash, unassigned: net-amount('savings') };
  });
}
