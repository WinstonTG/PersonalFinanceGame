const $=id=>document.getElementById(id);
const money=value=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(value);
const labels={income:'Income',rent:'Rent',food:'Food',utilities:'Utilities',transport:'Gas',personal:'Personal',fun:'Fun',investment:'Investment',savings:'Savings target'};
let selected=null, snapshot=null, sourceUrl=null;
function add(tag,text,parent){const e=document.createElement(tag);e.textContent=text;parent.append(e);return e;}
function row(values,parent){const tr=add('tr','',parent);values.forEach(v=>add('td',v,tr));}
async function api(path,body){
  const response=await fetch(path,body===undefined?{}:{method:'POST',headers:{'X-Grader-Request':'1'},body:body instanceof File?body:JSON.stringify(body)});
  const data=await response.json();if(!response.ok)throw Error(data.error||'Request failed.');return data;
}
async function list(){
  const students=await api('/api/sessions');$('students').replaceChildren();
  students.sort((a,b)=>(b.score??-Infinity)-(a.score??-Infinity));
  for(const student of students){
    const button=add('button',student.name+' · '+(student.outdated?'Old rules — reimport PDF':student.score===null?student.completedMonths+'/12 months':student.score.toFixed(2)+' pts'),$('students'));
    button.onclick=async()=>{try{selected=student.id;render(await api('/api/session?id='+selected));$('source-link').replaceChildren();}catch(e){$('status').textContent=e.message;}};
  }
  if(!students.length)add('p','No PDFs imported yet.',$('students'));
}
function render(data){
  snapshot=data;$('workspace').hidden=false;$('student-title').textContent=data.document.name+' — '+data.document.title;
  const outdated=data.rulesVersion!=='fixed-rent-v3';
  const plannedIncome=plan=>data.document.version===2?'$1,500–$2,100':money(plan.income)+' (old estimate)';
  $('progress').textContent=data.completedMonths+' OF 12 MONTHS REVEALED';
  $('next-month').disabled=data.completedMonths===12 || outdated;
  $('next-month').textContent=data.completedMonths===0?'Confirm plan & simulate Month 1':data.completedMonths===12?'Year complete':'Simulate Month '+(data.completedMonths+1);
  $('plan-head').replaceChildren();const head=add('tr','',$('plan-head'));['Month',...Object.values(labels)].forEach(v=>add('th',v,head));
  $('plan-body').replaceChildren();data.document.months.forEach((m,i)=>row([i+1,...Object.keys(labels).map(k=>k==='income'?plannedIncome(m):money(m[k]))],$('plan-body')));
  $('plan-details').open=data.completedMonths===0;
  $('history').replaceChildren();data.months.forEach(m=>row([m.month,money(m.income),money(m.gifts),money(m.bad_fortune_cost),money(m.rent_paid+m.other_expenses_paid),money(m.investment_amount),money(m.fun_spending),money(m.savings_end),m.happiness_change.toFixed(2)+' pts'],$('history')));
  const m=data.months.at(-1);$('month-panel').hidden=!m;
  if(m){
    const plan=data.document.months[m.month-1];$('month-title').textContent='Month '+m.month+' · '+m.hours_per_week+' hours/week';
    $('events').replaceChildren();const events=[];
    if(m.gifts)events.push('Gift received: +'+money(m.gifts));
    if(m.bad_fortune)events.push('Bad fortune: −'+money(m.bad_fortune_cost)+' cash and −35 happiness.'+(m.bad_fortune==='job_loss_next_month'?' Job lost: no wages next month.':''));
    if(m.job_lost)events.push('Unemployment month: $0 wages. Employment resumes next month.');
    if(m.missed_rent)events.push('Rent not fully paid: −500 happiness.');
    if(m.missed_other_expenses)events.push('Other essentials not fully paid: −300 happiness.');
    if(!m.requested_fun)events.push('No fun budget: −50 happiness.');
    if(!events.length)events.push('No fortune event this month.');
    events.forEach(text=>add('div',text,$('events')).className='event');
    $('cards').replaceChildren();[['Cash',money(m.savings_end)],['Investments',money(m.investment_balance)],['Happiness this month',m.happiness_change.toFixed(2)+' pts'],['Happiness so far',m.happiness_end.toFixed(2)+' pts']].forEach(([label,value])=>{const card=add('div',label,$('cards'));card.className='card';add('strong',value,card);});
    $('comparison').replaceChildren();
    const prior=data.months.length>1?data.months.at(-2).savings_end:3000;
    [['Income',plannedIncome(plan),m.income],['Rent',plan.rent,m.rent_paid],['Other essentials',plan.food+plan.utilities+plan.transport+plan.personal,m.other_expenses_paid],['Investment',plan.investment,m.investment_amount],['Fun',plan.fun,m.fun_spending],['Net cash saved',plan.savings,m.savings_end-prior]].forEach(([label,p,a])=>row([label,typeof p==='string'?p:money(p),money(a)],$('comparison')));
  }
  $('final-panel').hidden=!data.final || outdated;
  if(outdated)$('status').textContent='This session used older rules. Reimport the student PDF to grade under the current fixed-rent rules.';
  if(data.final){const f=data.final;$('final-score').textContent=f.score.toFixed(2)+' points';$('final-breakdown').textContent=money(f.ending_savings)+' cash + '+money(f.investment_balance)+' investments + '+f.total_happiness.toFixed(2)+' happiness points. Average monthly happiness: '+f.average_happiness.toFixed(2)+'.';}
}
$('pdf-file').onchange=async e=>{
  const file=e.target.files[0];if(!file)return;
  $('status').textContent='Reading PDF…';e.target.disabled=true;
  try{
    if(file.size>5*1024*1024)throw Error('Choose a PDF under 5 MB.');
    const data=await api('/api/import',file);selected=data.id;render(data);await list();
    if(sourceUrl)URL.revokeObjectURL(sourceUrl);sourceUrl=URL.createObjectURL(file);
    $('source-link').replaceChildren();const a=add('a','Open original PDF for verification',$('source-link'));a.href=sourceUrl;a.target='_blank';a.rel='noopener';
    $('status').textContent='PDF imported. Review all 12 budgets, then confirm to simulate Month 1.';
  }catch(error){$('status').textContent='Import failed: '+error.message;}finally{e.target.disabled=false;e.target.value='';}
};
$('next-month').onclick=async()=>{
  $('next-month').disabled=true;
  try{render(await api('/api/next',{id:selected,expectedMonth:snapshot.completedMonths}));await list();$('status').textContent='Progress saved.';}
  catch(error){$('status').textContent=error.message;$('next-month').disabled=snapshot?.completedMonths===12;}
};
$('download-report').onclick=async()=>{
  try{const data=await api('/api/report?id='+selected);const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='graded-budget.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(e){$('status').textContent=e.message;}
};
$('print-report').onclick=()=>window.print();
list().catch(e=>$('status').textContent=e.message);
