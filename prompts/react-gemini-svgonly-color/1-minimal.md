Reproduce the widget screenshot as ONE React component by **pixel-measuring** the source image, not by applying generic web defaults. **All icons and images must be hand-written inline SVG — no icon libraries, no image URLs.**

# Output format

**Your entire response starts directly with `import` or `export default function Widget` — no ```jsx, no ```, no prose, no explanation, no trailing commentary. The raw code is the whole response.** If you wrap the output in a code fence, the file will fail to compile.

Structure:

```
<zero or more import lines>

export default function Widget() { return (
  /* JSX */
); }
```

- Root element must be `<div className="widget"> … </div>`.
- Import every external component you use, and nothing else.
- **Allowed libraries: `recharts` ONLY** (for complex charts, and only when necessary). Do NOT import `react-icons`, `lucide-react`, `react-feather`, `framer-motion`, Tailwind, or anything else. Most widgets need zero import lines.
- No `<style>` tag, no `<style jsx>`, no className-based CSS, no CSS variables. All styles are inline `style={{}}`.
- No state, no hooks, no event handlers, no transitions, no animations, no media queries.
- Do NOT reference `React.*` anywhere (no `React.cloneElement`, `React.Fragment`, `React.Children`) — JSX alone compiles without importing React. If you need a fragment, use `<>…</>`.
- Close every JSX tag. Balance every `{` and `(`. Do not stop mid-structure — finish the full tree before ending.

# The SVG-only rule (ZERO external assets)

**This is the most important constraint for preventing compile errors and 404s:**

- **Every icon** is hand-written inline `<svg>`. Do NOT `import { FaX } from 'react-icons/fa'`. Do NOT import icons from any library.
- **Every image/photo area** is either a solid-color `<div>` placeholder OR an inline `<svg>` illustration. Do NOT use `<img src="https://images.unsplash.com/...">`, `<img src="https://i.pravatar.cc/...">`, or any other URL. There are no allowed image hosts.
- **Every logo/brand mark** (Visa, Apple, Chrome, etc.) is a hand-written simplified `<svg>`. Do NOT attempt to fetch real logos.
- If you cannot draw a specific icon in SVG, draw a simplified version: a camera becomes a rounded rectangle with a circle lens; a dinosaur becomes a rounded silhouette path; a logo becomes a letter inside a colored square.

**There is no fallback tier.** If your instinct is "I'll just import `FaXxx`", stop — write `<svg>` instead, even if it looks less polished.

# The single most important rule (pixel measurement)

**Every numeric value (fontSize, padding, borderRadius, gap, width, height, icon size) must be measured in absolute pixels from the source image.** Do NOT use generic web defaults like 16px/24px/32px. A title in a 1200px-wide widget is usually 60–120px, not 24px. A huge statistic in a 2000px widget may be 300–500px.

If the image's root widget is 1400×800 and the title looks like it occupies 1/12 of the widget width, write `fontSize: '120px'` — not whatever "feels reasonable for a website".

# Sizing philosophy (absolute, never responsive)

- Use `px` for every dimension. Never use `%`, `rem`, `em`, `vw`, `vh`, or `calc()` for sizing. (`width: '60%'` or `width: '100%'` is only allowed inside a fill-the-row progress bar.)
- Never use `min-width`, `max-width`, `aspect-ratio`, media queries, or `clamp()`.
- The root `<div className="widget">` must set explicit `width` and `height` in px matching the screenshot.
- All child dimensions are measured against the **source image**, not against the root container.
- `boxSizing: 'border-box'` on containers that have both padding and explicit width/height.

# Style object property order

Write each style object in this consistent order:

1. Sizing: `width`, `height`
2. Appearance: `backgroundColor` / `background`, `borderRadius`, `border`, `boxShadow`
3. Spacing: `padding`, `margin`, `boxSizing`
4. Layout: `display`, `flexDirection`, `justifyContent`, `alignItems`, `gap`
5. Positioning: `position`, `top`/`left`/`right`/`bottom`, `transform`, `zIndex`
6. Typography: `fontFamily`, `fontSize`, `fontWeight`, `color`, `letterSpacing`, `lineHeight`, `textAlign`
7. Misc: `overflow`, `opacity`, `filter`

# Layout decisions

Pick ONE archetype based on the source image, then stick with it:

- **List / card-stack**: root is `display: 'flex', flexDirection: 'column', gap: '…'`. Most common.
- **Row / banner**: root is `display: 'flex', flexDirection: 'row', alignItems: 'center'`.
- **Poster / sparse composition**: root is `position: 'relative'`, children use `position: 'absolute'` with corner anchors.
- **Dashboard**: flex column with 2–4 major sections, charts via recharts or hand-drawn SVG.

**One `<div>` = one role.** If roles conflict, nest; do not stuff.

# Height filling (avoid empty vertical gaps)

The root widget has an explicit `height` matching the screenshot. When it contains stacked sections (2+ cards, header+body, header+body+footer), the sum of section heights should roughly fill the widget.

**When you have 2–3 stacked sections, pick ONE of these to avoid large empty mid-widget gaps:**

1. Root `justifyContent: 'space-between'` — sections push to top and bottom naturally.
2. Give each section explicit `flex: 1` (or `flex: 1.5` / `flex: 2` for weighted), letting flex distribute the full height.
3. Set explicit `height` on each section that sums close to the widget's inner height (root height minus padding).

**Do not rely on `gap` alone to fill height** — `gap` is for small inter-element spacing, not for pushing sections apart. If you find yourself writing `gap: '200px'` or more, switch to one of the above.

Wrong (creates a huge empty middle):
```jsx
<div style={{ height:'1000px', display:'flex', flexDirection:'column', gap:'32px' }}>
  <Card1 />  {/* 300px tall */}
  <Card2 />  {/* 300px tall — leaves 368px empty at bottom */}
</div>
```

Right:
```jsx
<div style={{ height:'1000px', display:'flex', flexDirection:'column',
              justifyContent:'space-between', gap:'32px' }}>
  <Card1 />
  <Card2 />
</div>
```

# Spacing rules

- Use `gap` on parents for children spacing, not `margin` on children.
- `margin` is only for: inter-section gaps at the root level, deliberate offsets like overlapping avatars, or `margin: 0` resets on `<h1>/<h2>/<p>`.
- Use `flex: 1` or `flexGrow: 1` for "fill remaining" — never `width: '100%'` inside a flex row.
- Use `flexShrink: 0` on fixed-size icons/images placed alongside flexible content.
- Center via `display:flex + justifyContent:center + alignItems:center`, or `top:'50%', left:'50%', transform:'translate(-50%,-50%)'`.

# Absolute positioning

- Parent: `position: 'relative'` + `overflow: 'hidden'` if content could spill.
- Child: `position: 'absolute'` + corner anchors (`top/right/bottom/left` in px).
- Floating overlays go as **the last child** of the relative parent.

# Color palette (from the target image)

The hex values below are the dominant colors in the screenshot, extracted by k-means clustering and sorted by pixel coverage (most-common first). Treat this list as the **authoritative palette** for the widget:

[COLOR_PALETTE]

- Every `backgroundColor`, `color`, `stroke`, `fill`, and gradient stop should be either one of these hex values **or** a close neighbor of one (within ~10 units in each RGB channel). Do NOT invent new hues.
- The highest-percentage color is typically the widget background. The next 1–2 colors are usually primary surfaces or card backgrounds. Mid-list colors are accents / icon fills / chart colors. Low-percentage colors are small text, borders, or highlights.
- If a color on the list looks like a gradient mid-tone (e.g. two similar blues), you may use both stops in a `linear-gradient(...)`.
- Anti-aliased edge pixels sometimes produce near-duplicate hexes — collapse them to the dominant one.

# Color and gradient

- Solid colors: hex (`#1c1c1e`, `#7c4dff`).
- Semi-transparent overlays: `rgba(255,255,255,0.3)`, `rgba(0,0,0,0.08)`.
- Gradients: `linear-gradient(135deg, #a 0%, #b 100%)` or `radial-gradient(circle at 50% 30%, rgba(0,102,255,0.08) 0%, transparent 70%)`.
- Text color hierarchy 3–4 steps: primary → secondary (~`#6b7280`) → tertiary (~`#9ca3af`) → disabled (~`#e5e7eb`).

# Typography

- Default fontFamily: `'-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'`.
- Reset `<h1>`, `<h2>`, `<p>` with `margin: 0`.
- `letterSpacing` scales negatively with font size: 20–40px → 0 to `-0.5px`; 40–80px → `-0.5px` to `-1px`; 80–200px → `-2px` to `-5px`; 200px+ → `-5px` to `-15px`.
- `lineHeight` unitless: `'1'`, `'1.15'`, `'1.4'`.
- Digit displays: `fontVariantNumeric: 'tabular-nums'`.
- Emphasis inside text: `<span style={{color:'#fff', fontWeight:600}}>`, never `<b>`/`<strong>`.

# Icon wrapping rule (DO NOT over-badge)

**Only wrap an icon in a colored/filled background container when the source image clearly shows a filled colored shape behind it.**

- If the icon appears **bare** in the screenshot (just the icon strokes on the widget's background, no circle/square behind it) → render the bare `<svg>` with no wrapping div.
- If the icon appears **inside a filled circle/rounded-square** (like an iOS app icon or a colored badge) → use the circular icon badge recipe with the matching background color.
- Many widgets have mixed rows: one icon has a colored background (e.g. a "primary action" +) while siblings are bare. Do NOT uniformly wrap them all.

Wrong (over-badging):
```jsx
{/* Source shows only + in a square; mic and check are bare */}
<div style={{bg:'yellow', padding:'16px'}}><Plus/></div>
<div style={{bg:'yellow', padding:'16px'}}><Mic/></div>    {/* wrong — bare in source */}
<div style={{bg:'yellow', padding:'16px'}}><Check/></div>  {/* wrong — bare in source */}
```

Right:
```jsx
<div style={{bg:'yellow', padding:'16px'}}><Plus/></div>   {/* bg visible in source */}
<svg>...</svg>                                              {/* bare in source */}
<svg>...</svg>                                              {/* bare in source */}
```

# SVG icon cookbook

Every `<svg>` icon follows this template:

```jsx
<svg width="WIDTH" height="HEIGHT" viewBox="0 0 24 24" fill="none"
     stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
  {/* paths/shapes */}
</svg>
```

- For filled icons: use `fill="currentColor"` and `stroke="none"` on the svg.
- For outlined icons: `fill="none"` + `stroke="currentColor"` + `strokeWidth="2"`.
- `viewBox="0 0 24 24"` is the standard. Width/height in px matches your target on the widget.
- Use `currentColor` so the icon color is inherited from the parent `color` CSS.

**Reference shapes — copy these paths verbatim into `<svg>`:**

Basic controls:
- **Plus (+)**: `<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>`
- **Minus (−)**: `<line x1="5" y1="12" x2="19" y2="12"/>`
- **Check (✓)**: `<polyline points="20 6 9 17 4 12"/>`
- **Close (✕)**: `<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>`
- **Arrow right (→)**: `<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>`
- **Arrow left (←)**: `<line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>`
- **Chevron down**: `<polyline points="6 9 12 15 18 9"/>`
- **Chevron right**: `<polyline points="9 18 15 12 9 6"/>`
- **Chevron up-down**: `<polyline points="7 15 12 20 17 15"/><polyline points="7 9 12 4 17 9"/>`

Common UI:
- **Bell**: `<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>`
- **Heart**: `<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>`
- **Star**: `<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>`
- **Bookmark**: `<path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>`
- **Search**: `<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>`
- **Settings (gear)**: `<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>`
- **User**: `<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>`
- **Lock**: `<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>`
- **Eye**: `<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>`
- **Trash**: `<polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>`
- **Pencil/Edit**: `<path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>`
- **Envelope/Mail**: `<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>`
- **Phone**: `<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>`
- **Clock**: `<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>`
- **Calendar**: `<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>`
- **Home**: `<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>`
- **Location-pin**: `<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>`
- **Download**: `<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>`
- **Upload**: `<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>`
- **Info**: `<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>`
- **Menu (≡)**: `<line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/>`
- **Three-dots horizontal**: `<circle cx="12" cy="12" r="1" fill="currentColor"/><circle cx="19" cy="12" r="1" fill="currentColor"/><circle cx="5" cy="12" r="1" fill="currentColor"/>`
- **Three-dots vertical**: `<circle cx="12" cy="12" r="1" fill="currentColor"/><circle cx="12" cy="5" r="1" fill="currentColor"/><circle cx="12" cy="19" r="1" fill="currentColor"/>`

Media:
- **Play (▶)**: `<polygon points="5 3 19 12 5 21 5 3" fill="currentColor" stroke="none"/>`
- **Pause**: `<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>`
- **Skip back**: `<polygon points="19 20 9 12 19 4 19 20" fill="currentColor"/><line x1="5" y1="19" x2="5" y2="5"/>`
- **Skip forward**: `<polygon points="5 4 15 12 5 20 5 4" fill="currentColor"/><line x1="19" y1="5" x2="19" y2="19"/>`
- **Volume**: `<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" fill="currentColor"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>`
- **Mic**: `<path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/>`
- **Camera**: `<path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/>`
- **Music note**: `<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>`
- **Image/photo**: `<rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>`

Objects & places (map/home/commerce):
- **Bed**: `<path d="M2 4v16"/><path d="M2 8h18a2 2 0 0 1 2 2v10"/><path d="M2 17h20"/><path d="M6 8v9"/>`
- **Briefcase**: `<rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>`
- **Fork-knife (restaurant)**: `<path d="M3 2v7a3 3 0 0 0 3 3v10"/><path d="M6 2v10"/><path d="M9 2v7"/><path d="M18 2c-1.5 0-3 1-3 3v7h3v10"/>`
- **Gas-pump**: `<line x1="3" y1="22" x2="15" y2="22"/><line x1="4" y1="9" x2="14" y2="9"/><path d="M14 22V4a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v18"/><path d="M14 13h2a2 2 0 0 1 2 2v2a2 2 0 0 0 2 2 2 2 0 0 0 2-2V9.83a2 2 0 0 0-.59-1.42L18 5"/>`
- **Shopping cart**: `<circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>`
- **Coffee cup**: `<path d="M18 8h1a4 4 0 0 1 0 8h-1"/><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/><line x1="6" y1="2" x2="6" y2="5"/><line x1="10" y1="2" x2="10" y2="5"/><line x1="14" y1="2" x2="14" y2="5"/>`
- **Lightbulb**: `<path d="M9 18h6"/><path d="M10 22h4"/><path d="M12 2a7 7 0 0 0-7 7c0 3 2 5 3 7h8c1-2 3-4 3-7a7 7 0 0 0-7-7z"/>`
- **Puzzle piece**: `<path d="M19.439 7.85c-.049.322.059.648.289.878l1.568 1.568c.47.47.47 1.229 0 1.698l-2.902 2.903c-.231.231-.557.338-.879.29-.086-.013-.175-.022-.263-.022a1.768 1.768 0 0 0-1.694 2.28c.04.13.011.264-.083.357l-3.116 3.116c-.47.47-1.229.47-1.698 0l-2.821-2.821c-.229-.231-.337-.557-.29-.879.013-.085.022-.175.022-.262a1.768 1.768 0 0 0-2.28-1.694c-.13.04-.264.011-.356-.083l-3.116-3.116c-.47-.47-.47-1.229 0-1.698L4.86 7.246c.232-.232.558-.339.881-.29.086.013.175.022.262.022a1.768 1.768 0 0 0 1.694-2.28c-.04-.13-.011-.264.083-.356l3.116-3.116c.47-.47 1.229-.47 1.698 0l2.815 2.815c.231.23.557.338.879.29z"/>`
- **Flashlight**: `<path d="M18 6H4a2 2 0 0 0 0 4h14l4-2-4-2z"/><path d="M14 10v10"/><path d="M10 10v10"/>`

Arrows & trends:
- **Trending up**: `<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>`
- **Trending down**: `<polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/>`

**For anything not in this list** (dinosaur, bitcoin logo, apple logo, airpods, cats, specific device silhouettes, etc.) — write a simplified silhouette using 1–3 `<path>` / `<circle>` / `<rect>` elements, OR if the shape is too complex, substitute with a letter inside a rounded rectangle (e.g. "B" for bitcoin, "A" for apple). **Never invent an icon library name.**

# Image placeholders (no URLs)

For photo content in the screenshot (album art, user avatars, product photos, scenes):

- **Album art / product thumbnail**: rounded-corner `<div>` with a subtle gradient background and optional SVG mark:
  ```jsx
  <div style={{ width:'280px', height:'280px', borderRadius:'24px',
                background:'linear-gradient(135deg, #3a3a3c, #1c1c1e)' }} />
  ```
- **User avatar**: circular `<div>` with initials or a simple SVG user icon:
  ```jsx
  <div style={{ width:'80px', height:'80px', borderRadius:'50%',
                backgroundColor:'#6366f1', color:'#fff',
                display:'flex', alignItems:'center', justifyContent:'center',
                fontSize:'32px', fontWeight:600 }}>JD</div>
  ```
- **Scene photo / landscape**: rounded `<div>` with a linear gradient matching the dominant photo colors (sky blue to sand, etc.):
  ```jsx
  <div style={{ width:'600px', height:'400px', borderRadius:'32px',
                background:'linear-gradient(180deg, #87ceeb 0%, #f4e1c1 100%)' }} />
  ```
- **Stacked avatars**: multiple circular colored `<div>`s with border and negative margin for overlap — no images.

**Never write `<img src="https://...">`.** Any URL will either 404 or be an unreliable asset. Solid-color + gradient placeholders render reliably and still communicate the composition.

# Atomic recipes

**Circular icon badge** (inline SVG inside colored circle)
```jsx
<div style={{ width:'80px', height:'80px', backgroundColor:'#3b70ff', borderRadius:'50%',
              display:'flex', justifyContent:'center', alignItems:'center', color:'#fff' }}>
  <svg width="40" height="40" viewBox="0 0 24 24" fill="none"
       stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
  </svg>
</div>
```

**Pill tag**
```jsx
<div style={{ padding:'14px 32px', borderRadius:'9999px', backgroundColor:'#f0fdf4',
              color:'#22c55e', fontSize:'28px', fontWeight:500,
              display:'inline-flex', alignItems:'center', gap:'8px' }}>+54%</div>
```

**Linear progress bar**
```jsx
<div style={{ height:'12px', backgroundColor:'#4a4a4a', borderRadius:'6px', overflow:'hidden' }}>
  <div style={{ width:'67%', height:'100%', backgroundColor:'#fff' }} />
</div>
```

**Segmented bar (auto-fill remainder)**
```jsx
<div style={{ height:'20px', borderRadius:'10px', display:'flex', overflow:'hidden' }}>
  <div style={{ backgroundColor:'#00bcd4', width:'43%' }} />
  <div style={{ backgroundColor:'#673ab7', flex:1 }} />
</div>
```

**Circular progress ring**
```jsx
{(() => {
  const r = 104, C = 2 * Math.PI * r;
  return (
    <svg width="248" height="248" viewBox="0 0 248 248">
      <circle cx="124" cy="124" r={r} fill="none" stroke="#eee" strokeWidth="24" />
      <circle cx="124" cy="124" r={r} fill="none" stroke="#30d158" strokeWidth="24"
              strokeLinecap="round" strokeDasharray={C}
              strokeDashoffset={C * (1 - 0.75)} transform="rotate(-90 124 124)" />
    </svg>
  );
})()}
```

# Data-to-JSX mapping

- 1 occurrence → write JSX directly.
- 2 occurrences identical → duplicate; do not over-abstract.
- 3+ occurrences identical structure → `const items = [...]` + `.map()`.
- 3+ with variants → add `type` field, branch with ternary.
- 3+ parameterized + complex → extract sub-component.
- 10+ items → `const data = [...]` at module level.

**CRITICAL syntax for inline-mapped data.** If you inline an array in JSX, you MUST call `.map(...)` and return JSX. Never leave a bare `{[...]}` or `{[{...}]}` — that renders raw objects and crashes.

Wrong (will crash with React error #31):
```jsx
{[
  { icon: <svg>...</svg>, label: 'Hotel' },
  { icon: <svg>...</svg>, label: 'Gas' },
]}
```

Right:
```jsx
{[
  { icon: <svg>...</svg>, label: 'Hotel' },
  { icon: <svg>...</svg>, label: 'Gas' },
].map((item, i) => (
  <div key={i} style={{…}}>{item.icon}<span>{item.label}</span></div>
))}
```

Preferred for clarity — extract the array to a `const` above the `return`:
```jsx
const items = [
  { icon: <svg>...</svg>, label: 'Hotel' },
  { icon: <svg>...</svg>, label: 'Gas' },
];
return (
  <div>
    {items.map((item, i) => (<div key={i}>{item.icon}<span>{item.label}</span></div>))}
  </div>
);
```

# Charts

- Simple progress ring → hand-drawn SVG with `strokeDasharray`.
- Bar chart with colored segments inside bars → flex divs with `flex:1 / flex:1.5`, NOT recharts.
- Pie/donut/line/area with axes or >5 points → recharts with `isAnimationActive={false}`, `stroke="none"`, `dot={false}`, `margin={{top:0,right:0,left:0,bottom:0}}`.
- Gradient fills via `<defs><linearGradient id="x">…</linearGradient></defs>` + `fill="url(#x)"`.
- Donut center text → absolute-positioned `<div>` overlay.

# Size-tier discipline

- **<250px (XS)**: ≤3 elements, no padding, nesting ≤3 levels.
- **250–500px (S)**: 1–2 sections, padding 12–40.
- **500–1200px (M)**: header/body/footer, padding 48–80, `items.map()` for lists.
- **1200–2000px (L)**: multi-region, padding 60–100, may use recharts.
- **2000px+ (XL)**: `const data` at module level, custom recharts shape components when applicable.

# What NOT to do

- Do NOT `import` anything from `react-icons`, `lucide-react`, `react-feather`, or any icon library. **Ever.**
- Do NOT `<img src="https://...">` — no Unsplash, no pravatar, no CDN URLs. **Ever.**
- Do NOT use Tailwind classes (`className="w-[X]"` will not work).
- Do NOT use `className` for styling beyond the required root `"widget"`.
- Do NOT use `<b>`/`<strong>`/`<em>` — use `<span style={{…}}>`.
- Do NOT use `<ul>`/`<li>` — use `<div>` + map.
- Do NOT add `useState`, `useEffect`, `onClick` handlers, `transition`, or `animation`.
- Do NOT add `cursor: 'pointer'` unless the source clearly shows an interactive element.
- Do NOT use `React.*` namespace (no `React.Fragment`, `React.cloneElement`).
- Do NOT over-decorate small widgets with multiple layered shadows/gradients.
- Do NOT reference any icon library name even in comments.
