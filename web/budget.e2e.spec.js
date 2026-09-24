import {test,expect} from 'playwright/test';

test('student builds twelve budgets, downloads, reopens and submits',async({page})=>{
  await page.goto('http://127.0.0.1:8000/budget.html');
  await expect(page.locator('#income-range')).toContainText('$1,500–$2,100');
  await expect(page.locator('#field-income')).toHaveCount(0);
  await expect(page.locator('#field-rent')).toHaveValue('1000');
  await expect(page.locator('#field-food')).toHaveValue('250');
  await expect(page.locator('#field-fun')).toHaveValue('');
  await page.locator('#student-name').fill('Test Student');
  await page.locator('#budget-title').fill('Buffer plan');
  await page.locator('#submit-document').click();
  await expect(page.locator('#document-status')).toContainText('Month 1');
  const values={rent:1000,food:250,utilities:50,transport:50,personal:50,fun:100,investment:200,savings:300};
  for(const [key,value] of Object.entries(values))await page.locator('#field-'+key).fill(String(value));
  await page.locator('#month-notes').fill('Save for emergencies.');
  await expect(page.locator('#month-summary')).toContainText('$2,800.00 – $3,400.00');
  for(let i=2;i<=12;i++){await page.locator('#next-month').click();await page.locator('#copy-previous').click();}
  await page.reload();
  await expect(page.locator('#student-name')).toHaveValue('Test Student');
  const downloadEvent=page.waitForEvent('download');
  await page.locator('#download-document').click();const download=await downloadEvent;
  page.once('dialog',dialog=>dialog.accept());
  await page.locator('#import-document').setInputFiles(await download.path());
  await expect(page.locator('#document-status')).toContainText('Document opened');
  await page.evaluate(()=>window.print=()=>{});
  await page.locator('#print-document').click();
  await page.emulateMedia({media:'print'});
  await expect(page.locator('#print-budget')).toBeVisible();
  await expect(page.locator('#print-budget article')).toHaveCount(12);
  await page.emulateMedia({media:'screen'});
  await page.locator('#submit-document').click();
  await expect(page.locator('#document-status')).toContainText('Submitted successfully. Receipt:');
  await page.setViewportSize({width:390,height:844});
  await expect(page.locator('#income-range')).toBeVisible();
  await page.screenshot({path:'test-results/budget-mobile.png',fullPage:true});
});

test('submission service rejects incomplete documents',async({request})=>{
  const response=await request.post('http://127.0.0.1:8000/api/documents',{data:{version:1,name:'Test',title:'Incomplete',months:[]}});
  expect(response.status()).toBe(400);
  expect(await response.json()).toEqual({error:'Complete all 12 monthly budgets.'});
});
