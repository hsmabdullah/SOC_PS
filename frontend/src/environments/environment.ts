/**
 * Runtime environment configuration.
 *
 * `apiBaseUrl` targets the FastAPI layer (`api/main.py` at the repo
 * root — run `uvicorn api.main:app --reload --port 8000`). In
 * development the dev-server proxy (proxy.conf.json) forwards `/api`
 * to that process on :8000.
 *
 * `useMockApi` — when true, an HttpInterceptor answers every `/api/v1/*`
 * request in the browser with mock payloads instead of calling the
 * backend. Leave false to use the real FastAPI + SQL Server data; set to
 * true only for UI work without any backend running.
 */
export const environment = {
  production: false,
  apiBaseUrl: '/api/v1',
  useMockApi: false,
};
