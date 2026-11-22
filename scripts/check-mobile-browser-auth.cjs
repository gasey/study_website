#!/usr/bin/env node
/** Desktop Chromium rehearsal of the real login/confirmation pages, loopback only. */
const fs = require('node:fs');
const assert = require('node:assert/strict');
const { chromium } = require(require.resolve('playwright', { paths: [process.env.FINNA_BROWSER_MODULES || process.cwd()] }));
async function main() {
  const input = JSON.parse(fs.readFileSync(0, 'utf8'));
  const origin = new URL(input.origin);
  assert.equal(origin.hostname, '127.0.0.1');
  assert.equal(origin.protocol, 'https:');
  const browser = await chromium.launch({ headless: true, ...(process.env.FINNA_STAGE_CHROMIUM ? { executablePath: process.env.FINNA_STAGE_CHROMIUM } : {}) });
  const results = [];
  try {
    for (const account of input.accounts) {
      const context = await browser.newContext({ ignoreHTTPSErrors: true, serviceWorkers: 'block' });
      const external = [];
      try {
        await context.route('**/*', route => {
          if (new URL(route.request().url()).origin === origin.origin) return route.continue();
          external.push(new URL(route.request().url()).origin);
          return route.abort();
        });
        const page = await context.newPage();
        await page.goto(account.authorization_url);
        await page.getByLabel('Email address', { exact: true }).fill(account.email);
        await page.getByLabel('Password', { exact: true }).fill(input.password);
        await page.getByRole('button', { name: 'Log in', exact: true }).click();
        const connect = page.getByRole('button', { name: 'Connect this account', exact: true });
        await connect.waitFor();
        await page.getByText(account.email, { exact: true }).waitFor();
        if (input.screenshot && results.length === 0) await page.screenshot({ path: input.screenshot, fullPage: true });
        // Capture the genuine confirmation response; desktop has no native scheme handler.
        const response = page.waitForResponse(r => r.url() === origin.origin + '/api/mobile-auth/authorize' && r.request().method() === 'POST');
        await connect.click();
        const authorized = await response;
        assert.equal(authorized.status(), 200);
        const callback = new URL((await authorized.json()).redirect);
        assert.equal(callback.protocol + '//' + callback.hostname + callback.pathname, 'finna-staging://auth/callback');
        assert.equal(callback.searchParams.get('state'), account.state);
        assert.equal(callback.searchParams.get('flow'), account.flow);
        // Parent cookie travels only through the private subprocess pipe, never a report.
        const cookie = (await context.cookies()).find(c => c.name === 'ism_session');
        assert.ok(cookie?.secure && cookie.httpOnly);
        results.push({ flow: account.flow, code: callback.searchParams.get('code'), parent_cookie: cookie.value, browser_login: true, confirmation: true, external_requests_blocked: external.length });
      } finally { await context.close(); }
    }
    process.stdout.write(JSON.stringify({ browser: await browser.version(), accounts: results }));
  } finally { await browser.close(); }
}
main().catch(error => {
  // No browser cookies/callbacks/credentials are included in failure diagnostics.
  console.error(String(error.message).split('\n').slice(0, 10).join('\n').replace(/https?:\/\/\S+/g, '[local URL]').replace(/[A-Za-z0-9_-]{32,}/g, '[redacted]'));
  process.exitCode = 1;
});
