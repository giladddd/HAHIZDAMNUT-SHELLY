#!/usr/bin/env node
/** Mobile smoke test — exit 1 if any check fails */
const { chromium } = require('playwright');

const PAGES = [
  'hahazdamnut.html',
  'employment.html',
  'finance.html',
  'about.html',
  'pre-meeting.html',
  'personal.html',
];

(async () => {
  const browser = await chromium.launch();
  const results = [];

  for (const file of PAGES) {
    const page = await browser.newPage({
      viewport: { width: 390, height: 844, deviceScaleFactor: 1 },
      isMobile: true,
      hasTouch: true,
    });
    const url = `http://127.0.0.1:8888/${file}`;
    try {
      await page.goto(url, { waitUntil: 'load', timeout: 20000 });
      await page.waitForTimeout(700);
      const m = await page.evaluate(() => {
        const x0 = window.scrollX;
        window.scrollBy(250, 0);
        const x1 = window.scrollX;
        window.scrollTo(0, window.scrollY);
        return {
          scrollX: x0,
          canScrollX: x1 !== x0,
          iw: window.innerWidth,
          bodyW: document.body.getBoundingClientRect().width,
        };
      });
      const ok = Math.abs(m.scrollX) <= 2 && !m.canScrollX && m.bodyW <= m.iw + 4;
      results.push({ file, ok, ...m });
    } catch (e) {
      results.push({ file, ok: false, err: e.message.split('\n')[0] });
    }
    await page.close();
  }

  // hahazdamnut extra checks
  const page = await browser.newPage({
    viewport: { width: 390, height: 844, deviceScaleFactor: 1 },
    isMobile: true,
    hasTouch: true,
  });
  await page.goto('http://127.0.0.1:8888/hahazdamnut.html', { waitUntil: 'load' });
  await page.waitForTimeout(800);
  const hero = await page.evaluate(() => ({
    title: document.querySelector('h1')?.textContent?.trim().slice(0, 40),
    hamLeft: document.getElementById('navHamburger')?.getBoundingClientRect().left,
    gallerySlideW: document.querySelector('.gallery-slide')?.getBoundingClientRect().width ?? 0,
    iw: window.innerWidth,
    hasOpp: !!document.getElementById('oppCards'),
  }));
  await page.tap('#navHamburger');
  await page.waitForTimeout(300);
  const drawer = await page.evaluate(() =>
    document.getElementById('navDrawer')?.classList.contains('open')
  );
  const galleryOk = hero.gallerySlideW > 0 && hero.gallerySlideW < hero.iw * 0.95;
  results.push({
    file: 'hahazdamnut.html (hero+menu+gallery)',
    ok: !!hero.title && hero.hamLeft >= 0 && drawer && hero.hasOpp && galleryOk,
    hero,
    drawer,
    galleryOk,
  });
  await browser.close();

  const failed = results.filter((r) => !r.ok);
  console.log(JSON.stringify(results, null, 2));
  if (failed.length) {
    console.error('FAILED:', failed.length);
    process.exit(1);
  }
  console.log('ALL PASS');
})();
