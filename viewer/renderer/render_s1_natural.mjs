#!/usr/bin/env node
/**
 * Strategy 1 (natural-size render) — render JSX or HTML at the widget's
 * natural CSS layout dimensions and screenshot the widget bounding box.
 *
 * Output:  <source-basename>-s1.png  next to each .jsx / .html source file.
 *
 * Usage:
 *   node render_s1_natural.mjs <run-dir> [-j N] [--out-suffix s1]
 *
 * For each *.jsx / *.html file under run-dir, writes the natural render to
 *   <dirname>/<basename>-<suffix>.png  (default suffix = "s1").
 * Skips samples whose output already exists (idempotent, safe to re-run).
 */
import fs from 'node:fs';
import fsp from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { EventEmitter } from 'node:events';
import esbuild from 'esbuild';
import { chromium } from 'playwright';

EventEmitter.defaultMaxListeners = 64;

const VIEWER_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

function log(...a) { console.log('[s1-natural]', ...a); }
function pngSize(p) { const b = fs.readFileSync(p); return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) }; }

function normalizeJsx(srcPath, dstPath) {
  const src = fs.readFileSync(srcPath, 'utf8');
  const replaced = src.replace(/<style>(?!\s*\{)([\s\S]*?)<\/style>/g, (_, css) => {
    return `<style>{\`${css.replace(/`/g, '\\`')}\`}</style>`;
  });
  fs.writeFileSync(dstPath, replaced, 'utf8');
  return dstPath;
}
async function bundleJsx(input, out, wd) {
  const entry = out.replace(/\.js$/, '.entry.js');
  fs.writeFileSync(entry,
    `import React from 'react';\nimport { createRoot } from 'react-dom/client';\nimport Widget from ${JSON.stringify(input)};\n` +
    `createRoot(document.getElementById('root')).render(React.createElement(Widget));`, 'utf8');
  await esbuild.build({
    entryPoints: [entry], outfile: out, bundle: true, platform: 'browser',
    format: 'iife', target: ['es2020'], jsx: 'automatic', jsxImportSource: 'react',
    sourcemap: false, logLevel: 'silent', absWorkingDir: wd,
    nodePaths: [VIEWER_ROOT, path.join(VIEWER_ROOT, 'node_modules')],
    define: { 'process.env.NODE_ENV': '"production"' },
  });
}

const HTML_SHELL = `<!doctype html><html><head><meta charset="utf-8"/><style>
html,body,#root{margin:0;padding:0;background:transparent}body{overflow:hidden}.widget{display:inline-block}
</style>
<script>window.tailwind=window.tailwind||{};window.tailwind.config={corePlugins:{preflight:false}};</script>
<script src="https://cdn.tailwindcss.com"></script>
</head><body><div id="root"></div></body></html>`;

async function* walkSources(dir) {
  for (const e of await fsp.readdir(dir, { withFileTypes: true })) {
    if (e.name.startsWith('.')) continue;  // skip .analysis-*, .git, etc.
    const full = path.join(dir, e.name);
    if (e.isDirectory()) yield* walkSources(full);
    else if (e.isFile() && /\.(jsx|html)$/i.test(e.name)) yield full;
  }
}

async function renderJsx(context, jsxPath, outPng) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 's1-'));
  const norm = normalizeJsx(jsxPath, path.join(tmp, 'w.jsx'));
  const bundle = path.join(tmp, 'b.js');
  await bundleJsx(norm, bundle, path.dirname(jsxPath));
  const page = await context.newPage();
  let pageError = null;
  page.on('pageerror', (e) => { if (!pageError) pageError = e; });
  try {
    await page.setContent(HTML_SHELL, { waitUntil: 'load' });
    await page.addScriptTag({ content: fs.readFileSync(bundle, 'utf8') });
    const sel = page.waitForSelector('.widget', { state: 'attached', timeout: 10000 });
    sel.catch(() => {});
    await new Promise((res, rej) => {
      let fin = false;
      const finish = (fn) => (v) => { if (fin) return; fin = true; clearInterval(t); fn(v); };
      const t = setInterval(() => { if (pageError) finish(rej)(pageError); }, 50);
      sel.then(finish(res), finish(rej));
    });
    await page.waitForTimeout(80);
    const widget = await page.$('.widget');
    if (!widget) throw new Error('no .widget');
    let box = await page.evaluate(el => { const r = el.getBoundingClientRect(); return { x:r.x, y:r.y, w:r.width, h:r.height }; }, widget);
    const start = Date.now();
    while ((box.w === 0 || box.h === 0) && Date.now() - start < 3000) {
      await page.waitForTimeout(50);
      box = await page.evaluate(el => { const r = el.getBoundingClientRect(); return { x:r.x, y:r.y, w:r.width, h:r.height }; }, widget);
    }
    if (box.w === 0 || box.h === 0) throw new Error(`widget 0x0`);
    const vw = Math.max(400, Math.ceil(box.x + box.w + 20));
    const vh = Math.max(400, Math.ceil(box.y + box.h + 20));
    await page.setViewportSize({ width: vw, height: vh });
    await widget.screenshot({ path: outPng, omitBackground: true });
  } finally {
    await page.close().catch(() => {});
    fs.rmSync(tmp, { recursive: true, force: true });
  }
}

async function renderHtml(context, htmlPath, outPng) {
  const page = await context.newPage();
  try {
    await page.goto('file://' + htmlPath, { waitUntil: 'load' });
    await page.waitForTimeout(120);
    const widget = await page.$('.widget');
    if (widget) {
      const box = await page.evaluate(el => { const r = el.getBoundingClientRect(); return { x:r.x, y:r.y, w:r.width, h:r.height }; }, widget);
      if (box.w === 0 || box.h === 0) throw new Error(`widget 0x0`);
      const vw = Math.max(400, Math.ceil(box.x + box.w + 20));
      const vh = Math.max(400, Math.ceil(box.y + box.h + 20));
      await page.setViewportSize({ width: vw, height: vh });
      await widget.screenshot({ path: outPng, omitBackground: true });
    } else {
      // fall back to body screenshot
      await page.screenshot({ path: outPng, fullPage: false, omitBackground: true });
    }
  } finally {
    await page.close().catch(() => {});
  }
}

async function main() {
  const argv = process.argv.slice(2);
  let runDir = '', jobs = 8, suffix = 's1';
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '-j' || argv[i] === '--jobs') jobs = Number(argv[++i]);
    else if (argv[i] === '--out-suffix') suffix = argv[++i];
    else if (!runDir) runDir = argv[i];
  }
  if (!runDir) { console.error('Usage: render_s1_natural.mjs <run-dir> [-j N] [--out-suffix s1]'); process.exit(1); }
  runDir = path.resolve(runDir);

  const files = [];
  for await (const f of walkSources(runDir)) {
    const out = f.replace(/\.(jsx|html)$/i, `-${suffix}.png`);
    if (!fs.existsSync(out)) files.push(f);
  }
  log(`runDir=${runDir} pending=${files.length} concurrency=${jobs} suffix=-${suffix}`);
  if (!files.length) { log('nothing to do'); return; }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1200, height: 1000 } });
  let idx = 0, ok = 0, fail = 0;
  async function worker() {
    while (true) {
      const i = idx++; if (i >= files.length) break;
      const f = files[i];
      const out = f.replace(/\.(jsx|html)$/i, `-${suffix}.png`);
      try {
        if (/\.jsx$/i.test(f)) await renderJsx(context, f, out);
        else await renderHtml(context, f, out);
        ok++;
        if ((ok + fail) % 50 === 0 || (ok + fail) === files.length) {
          log(`[${ok + fail}/${files.length}] ok=${ok} fail=${fail}`);
        }
      } catch (e) {
        fail++; console.log(`FAIL ${f}: ${e.message}`);
      }
    }
  }
  await Promise.all(Array.from({ length: jobs }, () => worker()));
  await browser.close();
  log(`Done: ok=${ok} fail=${fail}`);
}
main().catch(e => { console.error(e); process.exit(1); });
