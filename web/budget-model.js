export const labels = {
  rent: 'Rent', food: 'Food & groceries',
  utilities: 'Utilities & phone', transport: 'Gas', personal: 'Personal essentials',
  fun: 'Fun & activities', investment: 'Investment', savings: 'Cash savings',
};
export const keys = Object.keys(labels);
export const incomeRange = Object.freeze({min:1500,max:2100});
export const baseline = Object.freeze({
  rent: 1000, food: 25, utilities: 25, transport: 25, personal: 50,
});
export function fillMissingBaseline(document) {
  return {...document, version:2, incomeRange:{...incomeRange}, months: document.months.map(month => {
    const filled = {...month};
    delete filled.income; // Old drafts used an estimate; income is now a shared range.
    filled.rent = baseline.rent; // Rent is fixed, including restored/imported plans.
    for (const [key,value] of Object.entries(baseline)) {
      if (filled[key] == null) filled[key] = value;
    }
    return filled;
  })};
}
export function blankDocument() {
  return fillMissingBaseline({ version: 2, name: '', title: '', months: Array.from({length:12}, () =>
    Object.fromEntries([...keys.map(key => [key, null]), ['notes', '']])) });
}
export function validateDocument(doc) {
  if (!doc || ![1,2].includes(doc.version) || !Array.isArray(doc.months) || doc.months.length !== 12) throw Error('Use a budget document with 12 months.');
  if (doc.version===2 && (doc.incomeRange?.min!==1500 || doc.incomeRange?.max!==2100)) throw Error('Expected income range is $1,500–$2,100.');
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
  let cashMin = 3000, cashMax = 3000;
  return doc.months.map(month => {
    const complete = keys.every(k => typeof month[k] === 'number' && Number.isFinite(month[k]) && month[k] >= 0);
    const amount = key => Number.isFinite(month[key]) ? month[key] : 0;
    const expenses = ['rent','food','utilities','transport','personal','fun'].reduce((sum,k)=>sum+amount(k),0);
    const netMin = incomeRange.min-expenses-amount('investment');
    const netMax = incomeRange.max-expenses-amount('investment');
    cashMin += netMin; cashMax += netMax;
    return { complete, expenses, cashMin, cashMax,
      unassignedMin: netMin-amount('savings'), unassignedMax: netMax-amount('savings') };
  });
}
