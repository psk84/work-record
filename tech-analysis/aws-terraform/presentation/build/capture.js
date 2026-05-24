/**
 * Capture per-section screenshots from index.html.
 *
 * - Width fixed to 1920 (video width).
 * - Each section captured at its full natural height.
 * - Output: ./screenshots/section-NN.png + ./screenshots/meta.json
 */
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer-core');

const HTML_PATH = path.resolve(__dirname, '../index.html');
const NARRATIONS = require('./narrations.json');
const OUT_DIR = path.resolve(__dirname, 'screenshots');

const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

(async () => {
  if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });

  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: 'new',
    defaultViewport: { width: 1920, height: 1080, deviceScaleFactor: 1 },
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
  await page.goto('file://' + HTML_PATH, { waitUntil: 'networkidle0' });

  // Open all <details> so narration is visible (optional — we keep them closed
  // since narration text is conveyed via audio; this keeps slides cleaner).
  // No-op intentionally.

  // Hide the sticky TOC so each section reads centered and clean.
  await page.addStyleTag({
    content: `
      .toc { display: none !important; }
      .layout { grid-template-columns: 1fr !important; padding: 0 !important; }
      main { width: 100%; }
      details.narration { display: none !important; }
    `,
  });

  // Allow layout to settle
  await new Promise(r => setTimeout(r, 500));

  const meta = [];

  for (let i = 0; i < NARRATIONS.sections.length; i++) {
    const s = NARRATIONS.sections[i];
    const idx = String(i + 1).padStart(2, '0');
    const outPath = path.join(OUT_DIR, `section-${idx}.png`);

    const handle = await page.$(s.selector);
    if (!handle) {
      console.error(`! selector not found: ${s.selector}`);
      continue;
    }

    // Get bbox in document coords
    const box = await page.evaluate(el => {
      const r = el.getBoundingClientRect();
      return {
        x: Math.round(r.left + window.scrollX),
        y: Math.round(r.top + window.scrollY),
        width: Math.round(r.width),
        height: Math.round(r.height),
      };
    }, handle);

    // We want a 1920-wide capture. If element doesn't span 1920, expand x:0 width:1920
    const clip = {
      x: 0,
      y: box.y,
      width: 1920,
      height: box.height,
    };

    await page.screenshot({
      path: outPath,
      clip,
      type: 'png',
    });

    meta.push({
      id: s.id,
      title: s.title,
      file: path.relative(__dirname, outPath),
      width: clip.width,
      height: clip.height,
    });

    console.log(`✓ section-${idx} (${s.id}) ${clip.width}x${clip.height} → ${outPath}`);
  }

  fs.writeFileSync(
    path.join(OUT_DIR, 'meta.json'),
    JSON.stringify(meta, null, 2)
  );

  await browser.close();
  console.log('done.');
})().catch(err => {
  console.error(err);
  process.exit(1);
});
