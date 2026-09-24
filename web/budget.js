import { labels, keys, blankDocument, fillMissingBaseline, validateDocument, forecast } from './budget-model.js';
const $ = id => document.getElementById(id);
const currency = new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'});
const money = value => currency.format(value);
const storageKey = 'finance-budget-v1';
let doc = blankDocument(), current = 0;
try {
  const saved = JSON.parse(localStorage.getItem(storageKey));
  if (saved?.version === 1 && saved.months?.length === 12 && saved.months.every(m => m && typeof m === 'object')) doc = fillMissingBaseline(saved);
} catch { $('draft-status').textContent = 'Could not restore draft. Downloads still work.'; }
function save() {
  try { localStorage.setItem(storageKey,JSON.stringify(doc)); $('draft-status').textContent='Draft saved in this browser'; }
  catch { $('draft-status').textContent='Browser storage unavailable. Download to save.'; }
}
function message(text) { $('document-status').textContent = text; }
function element(tag,text,parent) { const el=document.createElement(tag); el.textContent=text; parent.append(el); return el; }
for (let i=0;i<12;i++) {
  const button=element('button',String(i+1),$('month-nav'));
  button.type='button'; button.setAttribute('aria-label','Edit month '+(i+1));
  button.onclick=()=>{current=i; render();};
}
for (const key of keys) {
  const label=element('label',labels[key],$('budget-fields'));
  const input=document.createElement('input'); input.id='field-'+key; input.type='number'; input.min='0'; input.step='.01';
  input.max=key==='fun'?'400':key==='investment'?'500':'100000';
  label.append(input);
  input.oninput=()=>{doc.months[current][key]=input.value===''?null:input.valueAsNumber; save(); review();};
}
$('student-name').value=doc.name; $('budget-title').value=doc.title;
$('student-name').oninput=e=>{doc.name=e.target.value;save();};
$('budget-title').oninput=e=>{doc.title=e.target.value;save();};
$('month-notes').oninput=e=>{doc.months[current].notes=e.target.value;save();};
function render() {
  $('month-heading').textContent='Month '+(current+1);
  [...$('month-nav').children].forEach((b,i)=>{b.removeAttribute('aria-current');if(i===current)b.setAttribute('aria-current','step');});
  keys.forEach(k=>$('field-'+k).value=doc.months[current][k]??'');
  $('month-notes').value=doc.months[current].notes??'';
  $('previous-month').disabled=current===0; $('copy-previous').disabled=current===0; $('next-month').disabled=current===11;
  review();
}
function review() {
  const rows=forecast(doc); const row=rows[current]; const month=doc.months[current];
  let summary=row.complete?'Unassigned income: '+money(row.unassigned)+'. Projected ending cash: '+money(row.cash)+'.':'Complete every category to review this month. Blank fields are treated as zero in this provisional forecast.';
  if(row.unassigned<0)summary+=' You are allocating more than your income; revise your budget or explain the savings withdrawal.';
  if(row.cash<0)summary+=' Your cash runs out under this plan.';
  if(month.rent!==null && month.rent<1000)summary+=' Rent is underfunded versus the $1,000 case study.';
  const essentials=['food','utilities','transport','personal'];
  if(essentials.every(k=>month[k]!==null) && essentials.reduce((sum,k)=>sum+month[k],0)<400)summary+=' Essentials total less than the $400 case-study requirement.';
  $('month-summary').textContent=summary;
  $('budget-review').replaceChildren();
  rows.forEach((r,i)=>{
    const tr=document.createElement('tr'); $('budget-review').append(tr);
    [String(i+1)+(r.complete?'':' (draft)'),money(doc.months[i].income??0),money(r.expenses),money(doc.months[i].investment??0),money(doc.months[i].savings??0),money(r.unassigned),money(r.cash)].forEach(v=>element('td',v,tr));
  });
}
$('previous-month').onclick=()=>{current--;render();};
$('next-month').onclick=()=>{current++;render();};
$('copy-previous').onclick=()=>{doc.months[current]={...doc.months[current-1]};save();render();};
function checked(action) { try {validateDocument(doc);action();} catch(e) {message(e.message);} }
$('download-document').onclick=()=>checked(()=>{
  const url=URL.createObjectURL(new Blob([JSON.stringify(doc,null,2)],{type:'application/json'}));
  const a=document.createElement('a');a.href=url;a.download='monthly-budget.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  message('Document downloaded. This does not submit it to your instructor.');
});
$('import-document').onchange=async e=>{
  try {
    const file=e.target.files[0];if(!file)return;
    if(file.size>65536)throw Error('Document is too large (64 KB maximum).');
    const imported=validateDocument(JSON.parse(await file.text()));
    if(!confirm('Replace your current draft with this document?'))return;
    doc=imported;current=0;save();$('student-name').value=doc.name;$('budget-title').value=doc.title;render();message('Document opened. Review before submitting.');
  }catch(error){message('Could not open document: '+error.message);}finally{e.target.value='';}
};
$('print-document').onclick=()=>checked(()=>{
  const root=$('print-budget');root.replaceChildren();
  element('p','Budget document v1',root);
  element('h1',doc.title,root);element('p','Student: '+doc.name+' · 12-month budget forecast · Starting cash: $3,000',root);
  const rows=forecast(doc);
  doc.months.forEach((m,i)=>{
    const section=element('article','',root);element('h2','Month '+(i+1),section);
    const table=element('table','',section);
    keys.forEach(k=>{const tr=element('tr','',table);element('td',labels[k],tr);element('td',money(m[k]),tr);});
    element('p','Unassigned: '+money(rows[i].unassigned)+' · Ending cash: '+money(rows[i].cash),section);
    element('p',m.notes,section);
  });window.print();
});
$('submit-document').onclick=async()=>{
  const button=$('submit-document');
  try {
    validateDocument(doc);button.disabled=true;message('Submitting…');
    const response=await fetch('/api/documents',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(doc)});
    if(response.status===501 || response.status===404)throw Error('Submissions need the classroom server. Download your document or ask your instructor for the submission URL.');
    const result=await response.json();if(!response.ok)throw Error(result.error||'Submission failed.');
    if(!result.receipt)throw Error('The server did not return a receipt.');
    message('Submitted successfully. Receipt: '+result.receipt+' · '+result.submittedAt);
  } catch(error){message('Not submitted: '+error.message);} finally{button.disabled=false;}
};
render();
