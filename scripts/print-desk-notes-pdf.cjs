#!/usr/bin/env node
/** Chromium prints the exact API HTML; never reconstructs a PDF from extracted text. */
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { createHash } = require('node:crypto');
const { chromium } = require(require.resolve('playwright', { paths: [process.env.FINNA_PDF_NODE_MODULES || process.cwd()] }));
const sha = data => createHash('sha256').update(data).digest('hex');
async function main() {
  if (process.argv.length !== 4) throw new Error('Expected fixture directory and PDF output directory');
  const fixture = path.resolve(process.argv[2]); const output = path.resolve(process.argv[3]);
  const manifest = JSON.parse(fs.readFileSync(path.join(fixture, 'manifest.json'), 'utf8'));
  if (!manifest.synthetic_only || manifest.production_access || !manifest.disposable_database_removed) throw new Error('Synthetic fixture proof required');
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true, ...(process.env.FINNA_PDF_CHROMIUM ? { executablePath: process.env.FINNA_PDF_CHROMIUM } : {}) });
  const results = [];
  try {
    for (const entry of manifest.cases) {
      if (!/^[a-z-]+$/.test(entry.name)) throw new Error('Invalid case name');
      const source = path.join(fixture, entry.name + '.html');
      if (sha(fs.readFileSync(source)) !== entry.sha256) throw new Error('Fixture changed');
      const page = await browser.newPage(); const remoteRequests = [];
      try {
        await page.route('**/*', async route => {
          if (route.request().url() === pathToFileURL(source).href) return route.continue();
          remoteRequests.push(route.request().url()); return route.abort();
        });
        await page.goto(pathToFileURL(source).href);
        await page.emulateMedia({ media: 'print' });
        const layout = await page.evaluate(async () => {
          await document.fonts.ready;
          return { scripts: document.scripts.length, images: document.images.length,
            printInstructionsHidden: getComputedStyle(document.querySelector('.instructions')).display === 'none',
            articles: document.querySelectorAll('article').length };
        });
        if (remoteRequests.length || layout.scripts || layout.images || !layout.printInstructionsHidden) throw new Error('Unexpected active content');
        const target = path.join(output, 'desk-notes-' + entry.name + '.pdf');
        await page.pdf({ path: target, preferCSSPageSize: true, printBackground: true, displayHeaderFooter: false });
        results.push({ case: entry.name, file: path.basename(target), sha256: sha(fs.readFileSync(target)), ...layout, remoteRequests: 0 });
      } finally { await page.close(); }
    }
    fs.writeFileSync(path.join(output, 'browser-print.json'), JSON.stringify({ browser: await browser.version(), engine: 'Chromium PDF printing', headersAndFooters: false, cssPageSize: true, cases: results }, null, 2) + '\n');
  } finally { await browser.close(); }
  console.log('Printed all four saved API HTML pages to actual browser PDFs.');
}
main().catch(error => { console.error(error); process.exitCode = 1; });
