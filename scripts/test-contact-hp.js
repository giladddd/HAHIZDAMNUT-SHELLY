#!/usr/bin/env node
const { chromium } = require('playwright');
const BASE = 'http://127.0.0.1:8888';

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(`${BASE}/hahazdamnut.html#contact`, { waitUntil: 'load' });
  await page.evaluate(() => localStorage.removeItem('hahizd_rl'));

  // Simulate autofill filling honeypot (common bug)
  await page.evaluate(() => {
    const hp = document.querySelector('#contactForm [name="_hp"]');
    if (hp) hp.value = 'spam@bot.com';
  });

  await page.fill('#fName', 'בדיקה ידנית');
  await page.fill('#fPhone', '0523960215');

  const reqs = [];
  page.on('request', (r) => {
    if (r.url().includes('script.google.com')) reqs.push(r.url());
  });

  await page.click('#cfBtn');
  await page.waitForTimeout(3000);

  const hp = await page.evaluate(() => document.querySelector('#contactForm [name="_hp"]')?.value);
  const success = await page.evaluate(() => document.getElementById('cfSuccess')?.classList.contains('show'));
  const errPhone = await page.evaluate(() => document.getElementById('errPhone')?.classList.contains('show'));

  console.log(JSON.stringify({ hp, success, errPhone, gasRequests: reqs.length, gasUrl: reqs[0]?.slice(0, 80) }, null, 2));
  await browser.close();
})();
