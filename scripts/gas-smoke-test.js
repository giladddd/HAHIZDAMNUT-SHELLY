#!/usr/bin/env node
/** Smoke test: GAS GET + browser form submit (no CORS errors on POST) */
const { chromium } = require('playwright');

const GAS =
  'https://script.google.com/macros/s/AKfycbx9oEJH0wO9wezg43EvBsX4unRFd8ELDRvcjL7alaXdyJpeA3pw1VirZUuw4VAMsKD39Q/exec';
const BASE = process.env.BASE || 'http://127.0.0.1:8888';

async function gasGet(params) {
  const url = GAS + '?' + new URLSearchParams(params).toString();
  const r = await fetch(url);
  const text = await r.text();
  let json = null;
  try {
    json = JSON.parse(text);
  } catch (_) {}
  return { ok: r.ok, status: r.status, json, text: text.slice(0, 120) };
}

(async () => {
  const results = [];

  results.push({
    test: 'gas_submit_get',
    ...(await gasGet({
      name: 'בדיקת_אוטומציה',
      phone: '0509999999',
      form_type: 'lead',
      timestamp: new Date().toLocaleString('he-IL'),
    })),
  });

  results.push({
    test: 'gas_lookup_get',
    ...(await gasGet({ action: 'lookup', name: 'בדיקה', phone: '50000001' })),
  });

  const browser = await chromium.launch();
  const page = await browser.newPage();

  const consoleErrors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });

  await page.goto(`${BASE}/discharge-guide.html`, { waitUntil: 'load', timeout: 20000 });
  await page.evaluate(() => {
    localStorage.removeItem('hahizd_rl');
  });

  await page.evaluate(async () => {
    window.__gasResult = await Hahizd.submit({
      name: 'בדיקת דפדפן',
      phone: '0508888888',
      notes: 'automated test',
      timestamp: new Date().toLocaleString('he-IL'),
      form_type: 'lead',
    });
  });

  const browserSubmit = await page.evaluate(() => window.__gasResult);
  const corsErrors = consoleErrors.filter((e) => /CORS|blocked/i.test(e));

  await browser.close();

  results.push({
    test: 'browser_hahizd_submit',
    ok: !!browserSubmit && browserSubmit.ok !== false,
    result: browserSubmit,
    corsErrors: corsErrors.length,
  });

  console.log(JSON.stringify(results, null, 2));

  const failed = results.filter((r) => !r.ok && r.test !== 'gas_lookup_get');
  if (failed.length || corsErrors.length) {
    console.error('FAILED');
    process.exit(1);
  }
  console.log('ALL PASS');
})();
