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

## Run (full stack)

Terminal 1 — FastAPI backend (from the **repository root**):

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

Terminal 2 — Angular frontend (from `frontend/`):

```bash
npm install
npm start          # http://localhost:4200 (proxies /api → :8000)
```

The FastAPI layer (`api/` at the repo root) reads the alerts table from
**SQL Server** through the existing `database/connector.py`. Configure
`DB_*` credentials and the `SOC_ALERTS_TABLE` / `SOC_COL_*` column
mapping in the root `.env`. When `DB_SERVER` is empty the API serves a
deterministic built-in demo dataset, so the stack runs end-to-end
without a database.

### Frontend-only mode (no backend at all)

Set `useMockApi: true` in `src/environments/environment.ts` — an
`HttpInterceptor` then answers every `/api/v1/*` request in the browser
with the same payload shapes, useful for pure UI work.

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
