/**
 * Runtime environment configuration.
 *
 * `apiBaseUrl` targets the FastAPI layer in front of the Python backend.
 * In development the dev-server proxy (proxy.conf.json) forwards `/api`
 * to the FastAPI process on :8000.
 *
 * `useMockApi` — when true, an HttpInterceptor answers every `/api/v1/*`
 * request with realistic mock payloads (same shapes FastAPI will return),
 * so the UI is fully functional without the backend. Flip to false once
 * the FastAPI endpoints are live.
 */
export const environment = {
  production: false,
  apiBaseUrl: '/api/v1',
  useMockApi: true,
};
