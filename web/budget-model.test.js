import test from 'node:test';
import assert from 'node:assert/strict';
import {blankDocument,keys,forecast,validateDocument,baseline,fillMissingBaseline} from './budget-model.js';
test('every month starts with shared assumptions but no discretionary choices',()=>{
  const d=blankDocument();
  for(const month of d.months){
    for(const [key,value] of Object.entries(baseline))assert.equal(month[key],value);
    assert.equal(month.food+month.utilities+month.transport+month.personal,400);
    for(const key of ['fun','investment','savings'])assert.equal(month[key],null);
  }
  d.months[0].rent=1200;
  assert.equal(d.months[1].rent,1000);
});
test('restoring older drafts fills missing defaults without replacing student choices',()=>{
  const d=blankDocument();Object.assign(d.months[0],{income:2100,food:0,rent:null,fun:80});
  const restored=fillMissingBaseline(d);
  assert.equal(restored.months[0].income,2100);
  assert.equal(restored.months[0].food,0);
  assert.equal(restored.months[0].rent,1000);
  assert.equal(restored.months[0].fun,80);
});
test('savings allocation stays in cash and income carries forward',()=>{
  const d=blankDocument();d.name='A';d.title='Plan';
  d.months.forEach(m=>{keys.forEach(k=>m[k]=0);Object.assign(m,{income:2000,rent:1000,food:400,fun:100,investment:200,savings:300});});
  validateDocument(d);
  const rows=forecast(d);
  assert.equal(rows[0].unassigned,0);
  assert.equal(rows[0].cash,3300);
  assert.equal(rows[11].cash,6600);
});
test('incomplete documents cannot be submitted',()=>{
  const d=blankDocument();d.name='A';d.title='Plan';
  assert.throws(()=>validateDocument(d),/Month 1/);
});
