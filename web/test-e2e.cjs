// End-to-end smoke test for Big Bolão web app
// Verifies: login flow, all 4 nav tabs, palpite modal, resultado detail
// Usage: node test-e2e.cjs (requires puppeteer installed)

const puppeteer = require('puppeteer');

const BASE = 'http://localhost:5173';
const TIMEOUT = 10000;

async function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

async function clickNavTab(page, label) {
  const btn = await page.evaluateHandle((lbl) => {
    for (const b of document.querySelectorAll('.nav-btn')) {
      if (b.textContent.includes(lbl)) return b;
    }
    return null;
  }, label);
  if (!btn) throw new Error(`Nav button "${label}" not found`);
  await btn.click();
  await delay(1200);
}

async function main() {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();
  page.on('pageerror', err => { throw new Error('PAGE ERROR: ' + err.message); });
  page.on('console', msg => { if (msg.type() === 'error') console.warn('  [console error]', msg.text()); });

  let passed = 0;
  let failed = 0;

  function check(name, condition) {
    if (condition) { passed++; console.log(`  ✅ ${name}`); }
    else { failed++; console.log(`  ❌ ${name}`); }
  }

  try {
    // === 1. Initial load ===
    console.log('1. Initial load');
    await page.goto(BASE + '/', { waitUntil: 'networkidle0', timeout: TIMEOUT });
    await page.waitForSelector('#app', { timeout: TIMEOUT });
    await delay(1500);
    check('Page loads', true);

    // === 2. Login ===
    console.log('2. Login');
    await page.click('.login-btn');
    await delay(1500);
    const greeting = await page.evaluate(() => document.querySelector('.home-greeting')?.textContent);
    check('Home greeting shows name', greeting === 'Oi, Mari Gallo! 👋');
    check('BottomNav visible', !!(await page.$('.bottom-nav')));
    check('Stats card visible', !!(await page.$('.stats-card')));

    // === 3. Navigate to all tabs ===
    const tabs = [
      { label: 'Jogos', check: () => !!document.querySelector('.filter-bar') },
      { label: 'Ranking', check: () => !!document.querySelector('.podium') },
      { label: 'Meus', check: () => !!document.querySelector('.page-title') },
      { label: 'Início', check: () => !!document.querySelector('.home-greeting') },
    ];

    for (const tab of tabs) {
      console.log('3. Navigate to ' + tab.label);
      await clickNavTab(page, tab.label);
      const hash = await page.evaluate(() => window.location.hash);
      check('Hash updated for ' + tab.label, hash.length > 1);
      const found = await page.evaluate(tab.check);
      check('Content renders for ' + tab.label, found);
    }

    // === 4. Palpite modal ===
    console.log('4. Palpite modal');
    await clickNavTab(page, 'Início');
    // Click any "Palpitar" button
    await page.evaluate(() => {
      for (const b of document.querySelectorAll('button')) {
        if (b.textContent.includes('Palpitar')) { b.click(); break; }
      }
    });
    await delay(800);
    const modalTitle = await page.evaluate(() => document.querySelector('.modal-title')?.textContent);
    check('Modal opens', modalTitle === 'Fazer palpite');
    check('Save button exists', !!(await page.$('.btn-save')));

    // === 5. Resultado detail ===
    console.log('5. Resultado detail');
    await page.evaluate(() => {
      // Close modal
      const close = document.querySelector('.btn-close');
      if (close) close.click();
    });
    await delay(500);
    await clickNavTab(page, 'Jogos');
    // Switch to Finalizados filter
    await page.evaluate(() => {
      for (const b of document.querySelectorAll('.filter-btn')) {
        if (b.textContent.includes('Finalizados')) { b.click(); break; }
      }
    });
    await delay(800);
    // Click first "Ver detalhes" button
    await page.evaluate(() => {
      for (const b of document.querySelectorAll('button')) {
        if (b.textContent.includes('Ver detalhes')) { b.click(); break; }
      }
    });
    await delay(800);
    const score = await page.evaluate(() => document.querySelector('.result-bigscore-value')?.textContent);
    check('Resultado detail shows score', score?.includes('×'));

    // === Summary ===
    console.log(`\n${'='.repeat(40)}`);
    console.log(`Passed: ${passed}  Failed: ${failed}`);
    console.log(`${'='.repeat(40)}`);

  } finally {
    await browser.close();
  }

  if (failed > 0) process.exit(1);
}

main().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
