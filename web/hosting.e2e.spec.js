import {test,expect} from 'playwright/test';
import {readFile,readdir} from 'node:fs/promises';

const origin='http://127.0.0.1:8003';

test('production output contains only public student assets',async({request})=>{
  const names=await readdir('dist');
  expect(names.sort()).toEqual(['index.html','styles.css','app.js','simulation.js','budget.html','budget.css','budget.js','budget-model.js','deployment.json'].sort());
  const config=JSON.parse(await readFile('vercel.json','utf8'));
  expect(config.outputDirectory).toBe('dist');
  expect(config.buildCommand).toBe('npm run build');
  expect(config.headers[0].headers).toContainEqual({key:'X-Content-Type-Options',value:'nosniff'});
  for(const path of ['/grader_web/index.html','/finance_game/grader.py','/submissions.sqlite3','/.env','/web/grader.e2e.spec.js']){
    expect((await request.get(origin+path)).status()).toBe(404);
  }
  expect(await (await request.get(origin+'/deployment.json')).json()).toEqual({submissions:false});
});

test('hosted workbook saves, exports and prints without a submission backend',async({page})=>{
  const errors=[];const submissions=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('request',request=>{if(request.method()==='POST')submissions.push(request.url());});
  await page.goto(origin+'/budget.html');
  await expect(page.locator('#submit-document')).toBeHidden();
  await expect(page.locator('#submission-help')).toContainText('send that file to your instructor');
  await page.locator('#student-name').fill('Hosted Student');
  await page.locator('#budget-title').fill('Online classroom plan');
  for(const key of ['fun','investment','savings'])await page.locator('#field-'+key).fill('100');
  for(let i=2;i<=12;i++){
    await page.locator('#next-month').click();await page.locator('#copy-previous').click();
  }
  await page.reload();
  await expect(page.locator('#student-name')).toHaveValue('Hosted Student');
  await expect(page.locator('#field-fun')).toHaveValue('100');
  const downloading=page.waitForEvent('download');
  await page.locator('#download-document').click();
  const file=await (await downloading).path();
  const document=JSON.parse(await readFile(file,'utf8'));
  expect(document.months).toHaveLength(12);
  page.once('dialog',dialog=>dialog.accept());
  await page.locator('#import-document').setInputFiles(file);
  await expect(page.locator('#document-status')).toContainText('Document opened');
  await page.evaluate(()=>window.print=()=>{});
  await page.locator('#print-document').click();
  await expect(page.locator('#print-budget article')).toHaveCount(12);
  const pdf=await page.pdf({format:'A4'});
  expect(pdf.subarray(0,5).toString()).toBe('%PDF-');
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:'test-results/hosted-budget-mobile.png',fullPage:true});
  expect(errors).toEqual([]);expect(submissions).toEqual([]);
});

test('static simulator works and unavailable browser storage has an honest warning',async({page})=>{
  await page.goto(origin);
  await page.locator('#plan-form').evaluate(form=>form.requestSubmit());
  await expect(page.locator('#results')).toBeVisible();
  await page.addInitScript(()=>{
    Storage.prototype.setItem=()=>{throw new DOMException('Storage disabled','SecurityError');};
  });
  await page.goto(origin+'/budget.html');
  await page.locator('#student-name').fill('Student');
  await expect(page.locator('#draft-status')).toContainText('Browser storage unavailable');
  await expect(page.locator('#submit-document')).toBeHidden();
});
