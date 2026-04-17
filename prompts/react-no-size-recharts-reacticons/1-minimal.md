You are an expert front-end developer.
Generate ONE single React component that reproduces the widget UI in the screenshot.
You may use `react-icons` for icons and `recharts` for charts. No other third-party libraries are allowed.

Rules:
- Output ONLY:

<zero or more import lines for required components>

export default function Widget() { return (
  /* JSX */
); }

- No comments, no extra text.
- Always import all external components used in the JSX, and nothing else.
- Root element must be <div className="widget"> … </div>.
