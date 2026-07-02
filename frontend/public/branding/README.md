# Brand assets

Place the official brand files here:

- `Suzuki_logo_2025_(vertical).png` — used by the splash screen and any
  vertical lockup (`<soc-logo variant="vertical" />`).

Until the PNG is present, the app renders a built-in SVG placeholder of the
Suzuki "S" mark (brand red `#E20A17`) with a "Pak Suzuki" wordmark in brand
blue `#003399`, so nothing breaks. Drop the real PNG in this folder and the
components pick it up automatically — no code change needed.
