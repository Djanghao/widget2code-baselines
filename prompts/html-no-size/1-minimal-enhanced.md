Given a phone widget screenshot, output EXACTLY one single self-contained HTML file that visually reproduces the widget.

Strict rules:

* Output ONLY HTML code.
* No markdown fences.
* No explanations.
* Stop after `</html>`.
* Must start with: `<html lang="en">`
* Must end with: `</html>`
* `<body>` must contain ONLY one top-level element:
  `<div class="widget"> ... </div>`
* No external assets: no CDN, no external fonts, no external images.
* All CSS must be inside one `<style>` in `<head>`.
* JS only if necessary, and must be inside the `.widget` div.
* The file must render correctly when opened locally.

Design rules:

* Match layout, spacing, colors, font sizes, corners, shadows as closely as possible.
* Use system fonts only.
* Use Flexbox/Grid for layout.
* Recreate icons using CSS or inline SVG (no image links).
* Avoid placeholders unless they appear in the screenshot.

Output the final HTML only.
