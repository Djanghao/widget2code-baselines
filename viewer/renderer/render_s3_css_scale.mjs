#!/usr/bin/env node
/**
 * Strategy 3 (CSS transform scale) — render JSX or HTML at natural size in
 * headless Chromium, then apply CSS `transform: scale(sx, sy)` so the widget
 * fills the GT dimensions exactly. Browser re-rasterizes vector content
 * (text glyphs, inline SVG) at scale, so they stay sharp.
 *
 * For each *.jsx / *.html under <run-dir>, finds the matching gt_NNNN.png in
 * <gt-dir>, computes (sx, sy) = (gtW/naturalW, gtH/naturalH), applies the
 * transform with `top left` origin, then screenshots clip=(0,0,gtW,gtH).
 *
 * Output:  <source-basename>-s3.png  next to each source.
 *
 * Usage:
 *   node render_s3_css_scale.mjs <run-dir> --gt-dir <gt-dir>
 *                                [-j N] [--out-suffix s3]
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
const IMAGE_ID_RE = /(?:image_|gt_)(\d{4,})/;

function log(...a) { console.log('[s3-css-scale]', ...a); }
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
html,body,#root{margin:0;padding:0;background:transparent}body{overflow:hidden}.widget{display:inline-block;transform-origin:top left}
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

function sampleIdFor(file) {
  const m = file.match(IMAGE_ID_RE);
  return m ? m[1] : null;
}

async function applyScaleAndShoot(page, gtW, gtH, outPng) {
  const nat = await page.evaluate(() => {
    const w = document.querySelector('.widget');
    if (!w) return null;
    const r = w.getBoundingClientRect();
    return { w: r.width, h: r.height };
  });
  if (!nat || !nat.w || !nat.h) throw new Error('natural size 0');
  const sx = gtW / nat.w, sy = gtH / nat.h;
  await page.evaluate(([sx, sy]) => {
    const w = document.querySelector('.widget');
    w.style.transformOrigin = 'top left';
    w.style.transform = `scale(${sx}, ${sy})`;
  }, [sx, sy]);
  await page.setViewportSize({ width: gtW + 20, height: gtH + 20 });
  await page.waitForTimeout(40);
  await page.screenshot({ path: outPng, clip: { x: 0, y: 0, width: gtW, height: gtH }, omitBackground: true });
}

async function renderJsx(context, jsxPath, gtSize, outPng) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 's3-'));
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
    await applyScaleAndShoot(page, gtSize.w, gtSize.h, outPng);
  } finally {
    await page.close().catch(() => {});
    fs.rmSync(tmp, { recursive: true, force: true });
  }
}

async function renderHtml(context, htmlPath, gtSize, outPng) {
  const page = await context.newPage();
  try {
    await page.goto('file://' + htmlPath, { waitUntil: 'load' });
    await page.waitForTimeout(120);
    const has = await page.$('.widget');
    if (!has) throw new Error('no .widget in html');
    await applyScaleAndShoot(page, gtSize.w, gtSize.h, outPng);
  } finally {
    await page.close().catch(() => {});
  }
}

async function main() {
  const argv = process.argv.slice(2);
  let runDir = '', gtDir = '', jobs = 8, suffix = 's3';
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '-j' || a === '--jobs') jobs = Number(argv[++i]);
    else if (a === '--gt-dir') gtDir = argv[++i];
    else if (a === '--out-suffix') suffix = argv[++i];
    else if (!runDir) runDir = a;
  }
  if (!runDir || !gtDir) {
    console.error('Usage: render_s3_css_scale.mjs <run-dir> --gt-dir <gt-dir> [-j N] [--out-suffix s3]');
    process.exit(1);
  }
  runDir = path.resolve(runDir);
  gtDir  = path.resolve(gtDir);

  const tasks = [];
  for await (const f of walkSources(runDir)) {
    const id = sampleIdFor(f);
    if (!id) continue;
    const gt = path.join(gtDir, `gt_${id}.png`);
    if (!fs.existsSync(gt)) continue;
    const out = f.replace(/\.(jsx|html)$/i, `-${suffix}.png`);
    if (fs.existsSync(out)) continue;
    tasks.push({ src: f, gt, out });
  }
  log(`runDir=${runDir} pending=${tasks.length} concurrency=${jobs} suffix=-${suffix}`);
  if (!tasks.length) { log('nothing to do'); return; }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1600, height: 1600 } });
  let idx = 0, ok = 0, fail = 0;
  async function worker() {
    while (true) {
      const i = idx++; if (i >= tasks.length) break;
      const { src, gt, out } = tasks[i];
      try {
        const gtSize = pngSize(gt);
        if (/\.jsx$/i.test(src)) await renderJsx(context, src, gtSize, out);
        else                     await renderHtml(context, src, gtSize, out);
        ok++;
        if ((ok + fail) % 50 === 0 || (ok + fail) === tasks.length) {
          log(`[${ok + fail}/${tasks.length}] ok=${ok} fail=${fail}`);
        }
      } catch (e) {
        fail++; console.log(`FAIL ${src}: ${e.message}`);
      }
    }
  }
  await Promise.all(Array.from({ length: jobs }, () => worker()));
  await browser.close();
  log(`Done: ok=${ok} fail=${fail}`);
}
main().catch(e => { console.error(e); process.exit(1); });
