# UX Parity

Compare Jinja (base.html + dashboard.html etc.) vs React (AppShell + pages).

## Technique

Preserve `frontend/src/styles/legacy.css` verbatim from `dashboard/static/css/styles.css` (1217 lines) plus `variables.css` tokens. Tailwind handles layout only (spacing/flex/grid); palette/fonts/components remain from legacy.css. Migrate component-by-component; keep legacy.css until visual regression signed off.

## Tokens Preserved

- CSS variables: --red, --red-dark, --bg, --surface, --border, --text, --sub, --muted, --navy, --purple, --green, --amber, --gridline (light + dark)
- Fonts: Titillium Web, IBM Plex Mono, Inter
- Spacing/border-radius/shadows, nav dimensions (sticky f1-nav), button/card/chart/table sizes, dark-mode `[data-theme]` toggle

## Screens to Compare (pixel)

- home, dashboard initial/loaded/prediction-complete/ai sidebar, standings, H2H, constructors, analytics, dark mode, mobile/tablet/desktop, grid editor
- Navigation active state: Jinja `request.blueprint` → React Router `NavLink isActive`
- Charts: Chart.js preserved (react-chartjs-2 wrapper)
- AI sidebar: fixed 400px, slide-in, tabs Settings/Chat, sliders, persistence (localStorage mode/model/weight/temperature, key NOT persisted)

## Checklist

- [ ] Screenshot Jinja vs React at 375, 768, 1100px
- [ ] Layout/spacing/font size/positions/colors/card dimensions/charts/navigation/interactive states
