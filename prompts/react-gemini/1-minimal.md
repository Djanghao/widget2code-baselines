Reproduce the widget screenshot as ONE React component by **pixel-measuring** the source image, not by applying generic web defaults.

# Output format

Output ONLY:

```
<zero or more import lines>

export default function Widget() { return (
  /* JSX */
); }
```

- Root element must be `<div className="widget"> … </div>`.
- Import every external component you use, and nothing else.
- Allowed libraries: `react-icons` and `recharts`. No others (no lucide-react, no react-feather, no framer-motion, no Tailwind, no styled-components).
- No `<style>` tag, no `<style jsx>`, no className-based CSS, no CSS variables. All styles are inline `style={{}}`.
- No state, no hooks, no event handlers, no transitions, no animations, no media queries.
- Do NOT reference `React.*` anywhere (no `React.cloneElement`, `React.Fragment`, `React.Children`) — JSX alone compiles without importing React. If you need a fragment, use `<>…</>`.

# The single most important rule

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
- **Poster / sparse composition**: root is `position: 'relative'`, children use `position: 'absolute'` with corner anchors. Use only when elements are scattered with clear focal points.
- **Dashboard**: flex column with 2–4 major sections, charts use recharts or hand-drawn SVG.

**One `<div>` = one role.** If a container both defines a shape (radius/border/bg) and lays out children (flex/gap), it's fine to keep them together; but if roles conflict, nest instead of stuffing.

# Spacing rules

- Use `gap` on parents for children spacing, not `margin` on children.
- `margin` is only for: inter-section gaps at the root level, deliberate offsets like overlapping avatars (`marginLeft: '-20px'`), or `margin: 0` resets on `<h1>/<h2>/<p>`.
- Use `flex: 1` or `flexGrow: 1` for "fill remaining" — never `width: '100%'` inside a flex row.
- Use `flexShrink: 0` on fixed-size icons/images placed alongside flexible content.
- Center via `display:flex + justifyContent:center + alignItems:center`, or the absolute idiom `top:'50%', left:'50%', transform:'translate(-50%,-50%)'`.

# Absolute positioning (when you use it)

- Parent: `position: 'relative'` plus `overflow: 'hidden'` if content could spill out.
- Child: `position: 'absolute'` plus one or two corner anchors (`top/right/bottom/left` in px).
- Floating overlays (badges, glow backgrounds, corner buttons) go as **the last child** of the relative parent.

# Color and gradient

- Solid colors: hex (`#1c1c1e`, `#7c4dff`).
- Semi-transparent overlays: `rgba(255,255,255,0.3)`, `rgba(0,0,0,0.08)`.
- Gradients: `linear-gradient(135deg, #a 0%, #b 100%)` or `radial-gradient(circle at 50% 30%, rgba(0,102,255,0.08) 0%, transparent 70%)`.
- Text color hierarchy is 3–4 steps: primary (`#000` or `#fff`) → secondary (~`#6b7280`) → tertiary (~`#9ca3af`) → disabled/border (~`#e5e7eb`).

# Typography

- Default fontFamily stack: `'-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'`.
- Reset `<h1>`, `<h2>`, `<p>` with `margin: 0`.
- `letterSpacing` scales **negatively** with font size: 20–40px → 0 to `-0.5px`; 40–80px → `-0.5px` to `-1px`; 80–200px → `-2px` to `-5px`; 200px+ → `-5px` to `-15px`.
- `lineHeight` is unitless or omitted: `'1'`, `'1.15'`, `'1.4'`.
- For digit displays (time, countdown, money): `fontVariantNumeric: 'tabular-nums'`.
- Emphasis inside a paragraph: wrap with `<span style={{color:'#fff', fontWeight:600}}>`, never `<b>` or `<strong>`.

# Icons — three-tier strategy

**CRITICAL: Icon name hallucination is the #1 cause of compile failures.** When in doubt, DO NOT guess — fall back to tier 2 or 3.

1. **First choice — react-icons, from a short whitelist of known-common names.** You may mix packages: `fa`, `md`, `io5`, `bs`, `tb`, `fi`, `hi`, `hi2`, `lu`, `si`. Only use names you are 100% certain exist from this allowlist of safe, common icons:

   - `react-icons/fa`: `FaPlus`, `FaMinus`, `FaCheck`, `FaTimes`, `FaSearch`, `FaPlay`, `FaPause`, `FaBell`, `FaHeart`, `FaStar`, `FaHome`, `FaUser`, `FaCog`, `FaEnvelope`, `FaPhone`, `FaCamera`, `FaBookmark`, `FaLightbulb`, `FaLeaf`, `FaSnowflake`, `FaMusic`, `FaChrome`, `FaBolt`, `FaArrowRight`, `FaArrowLeft`, `FaChevronRight`, `FaChevronDown`, `FaChevronUp`, `FaPencilAlt`, `FaBitcoin`, `FaEthereum`, `FaApple`, `FaGoogle`, `FaUserSecret`, `FaPuzzlePiece`, `FaMicrophone`, `FaBookmark`, `FaBookReader`, `FaBasketballBall`, `FaDumbbell`
   - `react-icons/md`: `MdOutlineMic`, `MdCameraAlt`, `MdCreditCard`, `MdKeyboardArrowDown`, `MdKeyboardArrowUp`, `MdArrowForward`, `MdFormatListBulleted`, `MdDragIndicator`, `MdMoreHoriz`, `MdMoreVert`, `MdAdd`, `MdClose`, `MdSearch`, `MdNotifications`, `MdSettings`, `MdHome`, `MdFavorite`
   - `react-icons/io5`: `IoPlaySharp`, `IoPlayBackSharp`, `IoPlayForwardSharp`, `IoShuffle`, `IoRepeat`, `IoVolumeLow`, `IoVolumeHigh`, `IoList`, `IoStarOutline`, `IoClose`, `IoCheckmarkCircle`, `IoHelpCircle`, `IoLockClosed`, `IoFootsteps`
   - `react-icons/bs`: `BsThreeDots`, `BsThreeDotsVertical`, `BsMusicNoteBeamed`, `BsIncognito`, `BsArrowUpRight`
   - `react-icons/tb`: `TbCalendarEvent`, `TbPuzzle`, `TbArrowsRightLeft`
   - `react-icons/fi`: `FiPlus`, `FiMinus`, `FiSearch`, `FiVideo`, `FiShoppingCart`, `FiLink`, `FiTrendingUp`, `FiArrowDownLeft`, `FiSmartphone`, `FiArrowRight`
   - `react-icons/hi`, `hi2`: `HiInboxIn`, `HiChevronUpDown`, `HiDotsVertical`
   - `react-icons/lu`: `LuBadgeAlert`, `LuChevronsUpDown`, `LuFileQuestion`, `LuArrowRight`
   - `react-icons/si`: `SiVisa`, `SiMastercard`

2. **If the icon you need is NOT in the list above, DO NOT write `import { SomeGuess } from 'react-icons/xx'`.** Instead, immediately drop to tier 2 or 3. Typical hallucinations to avoid: `IoMdDinosaur`, `GiTyrannosaurus`, `FaAppleWatch`, `FaAirpods`, `FaEarbuds`, `FaAirpodsCase`, `FaRobot2`, `MdWaterDrop` — none of these may exist. Writing any icon name you are <90% confident in WILL break rendering.

3. **Tier 2 — inline SVG.** For any icon not clearly in the whitelist (dinosaurs, animals, brand logos, custom devices, decorative motifs), write:
   ```jsx
   <svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
     <path d="M..." />
   </svg>
   ```
   Compose from `<path>`, `<circle>`, `<rect>`, `<line>`, `<polygon>`. Use `fill="currentColor"` to inherit text color.

4. **Tier 3 — geometric div.** Shapes like pixel monsters, arrows, triangles can be built from `<div>` with `borderRadius`/`backgroundColor`/`clipPath: 'polygon(...)'`. A retro pixel-dinosaur silhouette can be an `<svg>` with a single hand-written path in pixel-grid coordinates.

**Rule of thumb**: if you would pause to check whether an icon name exists, that's a signal to skip react-icons entirely for that glyph and hand-write SVG instead.

# Atomic component recipes

Use these fixed patterns — do not reinvent.

**Circular icon badge**
```jsx
<div style={{ width:'80px', height:'80px', backgroundColor:'#3b70ff', borderRadius:'50%',
              display:'flex', justifyContent:'center', alignItems:'center' }}>
  <FaSnowflake style={{ color:'#fff', fontSize:'40px' }} />
</div>
```

**Pill button / tag**
```jsx
<div style={{ padding:'14px 32px', borderRadius:'9999px', backgroundColor:'#f0fdf4',
              color:'#22c55e', fontSize:'28px', fontWeight:500,
              display:'inline-flex', alignItems:'center', gap:'8px' }}>+54%</div>
```

**Linear progress bar**
```jsx
<div style={{ height:'12px', backgroundColor:'#4a4a4a', borderRadius:'6px',
              position:'relative', overflow:'hidden' }}>
  <div style={{ width:'67%', height:'100%', backgroundColor:'#fff', borderRadius:'6px' }} />
</div>
```

**Segmented bar (two colors, auto-fill remainder)**
```jsx
<div style={{ height:'20px', borderRadius:'10px', display:'flex', overflow:'hidden' }}>
  <div style={{ backgroundColor:'#00bcd4', width:'43%' }} />
  <div style={{ backgroundColor:'#673ab7', flex:1 }} />
</div>
```

**Circular progress ring (SVG)**
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

**Stacked avatars**
```jsx
<img src="..." style={{ width:'130px', height:'130px', borderRadius:'50%',
                        border:'8px solid #fff', objectFit:'cover' }} />
<img src="..." style={{ width:'130px', height:'130px', borderRadius:'50%',
                        border:'8px solid #fff', objectFit:'cover', marginLeft:'-45px' }} />
```

**Fading-text truncation**
```jsx
<div style={{ whiteSpace:'nowrap',
              WebkitMaskImage:'linear-gradient(to right, black 60%, transparent 100%)',
              maskImage:'linear-gradient(to right, black 60%, transparent 100%)' }}>…</div>
```

# Data-to-JSX mapping (choose by frequency)

- 1 occurrence → write JSX directly.
- 2 occurrences with identical style → duplicate (do not over-abstract).
- 3+ occurrences, identical structure → declare `const items = [...]` inside the function, map over it.
- 3+ occurrences with variants → include a `type` field in each data item, branch with ternary or switch.
- 3+ occurrences needing parameterization + complex markup → extract a sub-component `const Card = ({value, color}) => …` above the main component.
- 10+ items or chart data → declare `const data = [...]` at **module level** (outside the function).

# Charts

- Simple progress ring → hand-drawn SVG with `strokeDasharray` (see recipe above).
- Bar chart with colored segments inside each bar → **flex divs** with `flex:1 / flex:1.5` ratios, NOT recharts.
- Pie/donut/line/area needing axes, tooltips, or >5 data points → recharts, with these defaults:
  - `isAnimationActive={false}`
  - `stroke="none"` on `Pie`
  - `dot={false}` on `Line` unless dots are visible in the image
  - `margin={{top:0,right:0,left:0,bottom:0}}` unless padding is visible
- Gradient fills via `<defs><linearGradient id="x">…</linearGradient></defs>` + `fill="url(#x)"`.
- Center text inside a donut → absolute-positioned overlay `<div>`, not recharts `<Label>`.

# Images

- If photos are needed: use `https://images.unsplash.com/photo-XXXXX?w=400&h=400&fit=crop` for generic content, `https://i.pravatar.cc/150?img=N` for avatars.
- Apply filters to match the design: `filter: 'grayscale(100%)'`, `'brightness(0.9)'`, etc.
- Set `objectFit: 'cover'` and explicit px width/height.

# Shadows and effects

- `boxShadow` for rectangular containers: `'0 12px 36px -8px rgba(0,0,0,0.3)'`.
- `filter: 'drop-shadow(0 4px 10px rgba(0,0,0,0.5))'` for SVG icons (respects transparency).
- Double-ring badge without extra element: `border: '4px solid #000'` + `boxShadow: '0 0 0 3px #fff'`.
- Do NOT stack 3+ radial gradients or multiple inset shadows unless the source image visibly shows glass/metal texture.

# Size-tier discipline

Pick the complexity tier based on widget pixel size:

- **<250px (XS)**: ≤3 visible elements, no padding (use flex center), nesting ≤3 levels.
- **250–500px (S)**: one or two sections, padding 12–40, single data array max.
- **500–1200px (M)**: header/body/footer structure, padding 48–80, `items.map()` for lists.
- **1200–2000px (L)**: multi-region with dividers, padding 60–100, `colors`/`styles` helper constants allowed, may use recharts.
- **2000px+ (XL)**: move `const data = [...]` to module level (outside the function), extract custom recharts shape components (`CustomBar`, `CustomTick`, `CustomTooltip`) when applicable.

# What NOT to do

- Do NOT import from `lucide-react`, `react-feather`, `react-circular-progressbar`, `@mui/*`, or any library other than `react-icons` and `recharts`.
- Do NOT guess icon names — if unsure whether `FaAppleWatch` exists, use `FaMobileAlt` or inline SVG instead.
- Do NOT use Tailwind classes (`className="w-[1352px]"` will not work).
- Do NOT use `className` for styling beyond the required root `"widget"`.
- Do NOT wrap emphasis in `<b>`/`<strong>`/`<em>` — use `<span style={{…}}>`.
- Do NOT use `<ul>`/`<li>` — use `<div>` + map.
- Do NOT add `useState`, `useEffect`, `onClick` handlers, `transition`, or `animation`.
- Do NOT add `cursor: 'pointer'` unless the source clearly shows an interactive element.
- Do NOT use `React.Fragment` / `<>…</>` unless the return requires it.
- Do NOT over-decorate small widgets with multiple layered shadows/gradients that the screenshot does not show.
