// Uses Playwright from NODE_PATH (the bundled Codex runtime), no project JS build.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:1000}});
  const marker=Date.now().toString();
  const logText='Browser acceptance '+marker+': my jab felt sharper but my shin is sore.';
  const replyText='Browser coach reply '+marker+': thanks for the update. Let us talk before class.';
  const errors=[];
  page.on('pageerror', e=>errors.push(e.message));
  // This acceptance script intentionally resets the fictional local demo.
  await page.request.post('http://127.0.0.1:8765/api/reset');
  await page.goto('http://127.0.0.1:8765');
  await page.getByRole('heading',{name:'A little feedback. A lot of progress.'}).waitFor();
  await page.getByRole('button',{name:'Before class',exact:true}).click();
  await page.getByRole('heading',{name:'Walk in knowing your people.'}).waitFor();
  assert(await page.locator('.roster-row').count()>0,'seeded brief must contain booked people');
  const screenshots=path.join(__dirname,'screenshots');
  fs.mkdirSync(screenshots,{recursive:true});
  await page.screenshot({path:path.join(screenshots,'desktop-brief.png'),fullPage:true});
  await page.getByRole('button',{name:'Demo tools',exact:true}).click();
  await page.locator('#sms-body').fill(logText);
  await page.getByRole('button',{name:'Send into demo',exact:true}).click();
  await page.locator('#conversation').getByText(logText,{exact:false}).first().waitFor();
  await page.getByRole('button',{name:'Coach inbox',exact:true}).click();
  const card=page.locator('article.log').filter({hasText:logText}).first();
  await card.locator('textarea').fill(replyText);
  await card.getByRole('button',{name:'Send simulated SMS',exact:true}).click();
  await page.getByRole('button',{name:'Demo tools',exact:true}).click();
  await page.locator('#conversation').getByText(replyText,{exact:false}).waitFor();
  await page.getByRole('button',{name:'After class',exact:true}).click();
  assert((await page.locator('#job-time').inputValue()).includes('T20:45:00'));
  await page.getByRole('button',{name:'Run due jobs',exact:true}).click();
  await page.locator('#job-result').filter({hasText:'sent'}).waitFor();
  const firstJobs=JSON.parse(await page.locator('#job-result').innerText());
  assert(firstJobs.sent>0,'preset must cause due nudges');
  await page.getByRole('button',{name:'Sunday recap',exact:true}).click();
  assert((await page.locator('#job-time').inputValue()).includes('T18:00:00'));

  await page.getByRole('button',{name:'Owner overview',exact:true}).click();
  await page.getByRole('heading',{name:'See where a conversation could help.'}).waitFor();
  assert.equal(await page.locator('.metric').count(),4);
  await page.screenshot({path:path.join(screenshots,'desktop-owner.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});
  for (const label of ['Coach inbox','Before class','Owner overview','Demo tools','Message & event log']) {
    await page.getByRole('button',{name:label,exact:true}).click();
    await page.waitForTimeout(150);
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),'mobile overflow: '+label);
  }
  await page.getByRole('button',{name:'Before class',exact:true}).click();
  await page.getByRole('heading',{name:'Walk in knowing your people.'}).waitFor();
  await page.screenshot({path:path.join(screenshots,'mobile-brief.png'),fullPage:true});
  assert.deepEqual(errors,[]);
  await browser.close();
  console.log('PASS: browser coaching loop, seeded brief, owner metrics, five mobile views, no page errors.');
})().catch(error=>{console.error(error);process.exit(1)});


