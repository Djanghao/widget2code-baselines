# TODO

## Fix html-concise rendering in S1 + S3 `renderHtml`

`viewer/renderer/render_s1_natural.mjs::renderHtml` (L108-128) and `viewer/renderer/render_s3_css_scale.mjs::renderHtml` (L124-135) both call `page.goto(file://...)` then screenshot, without injecting a transparent body background or waiting for `.widget` to attach. html-concise files set `body { background-color: #000 }`, which bleeds at rounded corners under `omitBackground:true`. Result: html-concise s1/s2/s3 outputs differ from the original baseline `1-minimal.png` (MEAN drift ~-3.48).

**Fix** — after `page.goto(...)` in both files, insert (matches original commit `47a9840` `bin/render-html.mjs:35-45`):

```js
await page.evaluate(() => {
  document.documentElement.style.background = 'transparent';
  document.body && (document.body.style.background = 'transparent');
  if (document.body) document.body.style.overflow = 'hidden';
});
await page.waitForSelector('.widget', { state: 'attached', timeout: 10000 });
```

**Scope**
- S1 `renderHtml`: apply fix.
- S3 `renderHtml`: apply fix.
- S2 (`render_s2_pil_resize.py`): no change — it resizes S1 output, so fixing S1 fixes S2.
- JSX paths (`renderJsx` in both): no change — `HTML_SHELL` already sets `background:transparent` and uses `waitForSelector('.widget')`.

**Validation** — re-run html-concise s1/s2/s3 evaluations and confirm parity with original baseline.
