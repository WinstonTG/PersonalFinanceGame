import test from 'node:test';
import assert from 'node:assert/strict';
import {blankDocument,keys,forecast,validateDocument} from './budget-model.js';
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
