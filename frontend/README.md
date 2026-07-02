# Pak Suzuki SOC — Frontend

Angular frontend for the Security Operations Center dashboard. Modern,
minimal, data-dense UI in the Pak Suzuki brand palette — Primary Red
`#E20A17`, Primary Blue `#003399` — on white/neutral surfaces, set in Inter.

## Stack

- **Angular 21** — standalone components, signals, zoneless change detection,
  lazy routes with view transitions
- **Chart.js 4** — via a thin `soc-chart` wrapper component and a central
  theme (`shared/chart/chart-theme.ts`)
- **SCSS design tokens** — all colors/spacing/motion in `src/styles.scss`

## Run

```bash
npm install
npm start          # http://localhost:4200
```

By default the app runs against a **mock API** (`environment.useMockApi =
true`): an `HttpInterceptor` answers every `/api/v1/*` request with
deterministic, filter-aware payloads shaped exactly like the FastAPI
responses. All data on screen is aggregated from one seeded alert
population, so every widget agrees.

## Connecting the FastAPI backend

1. Implement the endpoints in the FastAPI layer:
   - `GET /api/v1/dashboard/summary?range=&severities=&categories=`
     → `DashboardSummary` (see `src/app/core/models/soc.models.ts`)
   - `GET /api/v1/alerts?range=&severities=&categories=&limit=`
     → `AlertPage`
2. Set `useMockApi: false` in `src/environments/environment.ts`.
3. `npm start` proxies `/api` to `http://localhost:8000`
   (see `proxy.conf.json`).

## Branding

Drop the official `Suzuki_logo_2025_(vertical).png` into
`public/branding/` — the splash screen picks it up automatically. Until
then a built-in SVG rendition of the S mark is shown.

## Structure

```
src/app/
├── core/
│   ├── models/soc.models.ts        # API contracts (mirror FastAPI models)
│   ├── api/soc-api.service.ts      # HttpClient gateway
│   ├── api/mock-api.interceptor.ts # mock FastAPI (dev)
│   ├── api/mock-data.ts            # seeded alert population + aggregation
│   └── state/dashboard.store.ts    # signal store: filters → refetch → data
├── layout/header/                  # sticky brand header + nav
├── features/
│   ├── splash/                     # animated brand splash overlay
│   └── dashboard/                  # dashboard page
│       └── components/             # kpi-card, filter-bar, charts, table…
└── shared/
    ├── brand/logo…                 # logo lockup (PNG w/ SVG fallback)
    └── chart/                      # Chart.js wrapper + validated theme
```

## Chart color system

Categorical series use a fixed, validated 6-slot palette (CVD-safe adjacent
pairs, ≥3:1 contrast on white). Suzuki red is **reserved** for
severity/status and brand accents — it is never used as a series color, so
red always means risk.
