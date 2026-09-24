import {test,expect} from 'playwright/test';
import {spawn} from 'node:child_process';
import {mkdtemp,readFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';

test('real student PDF imports privately and grades one month at a time',async({page,request,browser})=>{
  test.setTimeout(60000);
  const directory=await mkdtemp(join(tmpdir(),'finance-grader-test-'));
  const server=spawn('python',['-m','finance_game.grader','--port','8012','--data-dir',directory,'--no-open']);
  server.stdout.resume();server.stderr.resume();
  try{
    await expect.poll(async()=>{try{return (await request.get('http://127.0.0.1:8012/')).status();}catch{return 0;}}).toBe(401);
    // Produce an actual PDF through the student workbook's print layout.
    await page.goto('http://127.0.0.1:8000/budget.html');
    const document={version:1,name:'PDF Student',title:'Test budget',months:Array.from({length:12},(_,i)=>({income:2000,rent:1000,food:250,utilities:50,transport:50,personal:50,fun:100+i,investment:150+i,savings:300,notes:'Emergency reserve.'}))};
    await page.evaluate(d=>localStorage.setItem('finance-budget-v1',JSON.stringify(d)),document);
    await page.reload();await page.evaluate(()=>window.print=()=>{});await page.locator('#print-document').click();
    const pdf=await page.pdf({format:'A4',printBackground:true});
    const settings=JSON.parse(await readFile(join(directory,'settings.json'),'utf8'));
    await page.goto('http://127.0.0.1:8012/login?key='+settings.key);
    await page.locator('#pdf-file').setInputFiles({name:'student.pdf',mimeType:'application/pdf',buffer:pdf});
    await expect(page.locator('#status')).toContainText('PDF imported');
    await expect(page.locator('#plan-body tr')).toHaveCount(12);
    await expect(page.locator('#plan-body tr').last()).toContainText('$111.00');
    await expect(page.locator('#final-panel')).toBeHidden();
    for(let i=1;i<=12;i++){
      await page.locator('#next-month').click();
      await expect(page.locator('#history tr')).toHaveCount(i);
      if(i<12)await expect(page.locator('#final-panel')).toBeHidden();
    }
    await expect(page.locator('#final-panel')).toBeVisible();
    await expect(page.locator('#next-month')).toBeDisabled();
    const score=await page.locator('#final-score').textContent();
    await page.reload();await page.locator('#students button').first().click();
    await expect(page.locator('#final-score')).toHaveText(score);
    const download=page.waitForEvent('download');await page.locator('#download-report').click();
    const report=JSON.parse(await readFile(await (await download).path(),'utf8'));
    expect(report.completedMonths).toBe(12);expect(report.document.months[11].investment).toBe(161);
    await page.screenshot({path:'test-results/grader-final.png',fullPage:true});
    await page.emulateMedia({media:'print'});await expect(page.locator('#final-score')).toBeVisible();
    const outsider=await browser.newContext();const other=await outsider.request.get('http://127.0.0.1:8012/api/sessions');expect(other.status()).toBe(401);await outsider.close();
  }finally{server.kill();}
});
