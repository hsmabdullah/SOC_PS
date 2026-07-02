import { HttpInterceptorFn, HttpResponse } from '@angular/common/http';
import { delay, of } from 'rxjs';

import { environment } from '../../../environments/environment';
import { AlertCategory, DashboardFilters, DateRange, Severity } from '../models/soc.models';
import { buildAlertPage, buildSummary } from './mock-data';

/**
 * Answers `/api/v1/*` requests with mock payloads shaped exactly like the
 * FastAPI responses, plus a small simulated network latency so loading
 * states behave realistically. Registered only while
 * `environment.useMockApi` is true.
 */
export const mockApiInterceptor: HttpInterceptorFn = (req, next) => {
  if (!req.url.startsWith(environment.apiBaseUrl)) {
    return next(req);
  }

  const path = req.url.slice(environment.apiBaseUrl.length).split('?')[0];
  const filters = readFilters(req.params);
  const latency = 250 + Math.random() * 300;

  let body: unknown;
  switch (path) {
    case '/dashboard/summary':
      body = buildSummary(filters);
      break;
    case '/alerts':
      body = buildAlertPage(filters, Number(req.params.get('limit') ?? 8));
      break;
    default:
      return next(req);
  }

  return of(new HttpResponse({ status: 200, body })).pipe(delay(latency));
};

function readFilters(params: { get(name: string): string | null }): DashboardFilters {
  return {
    range: (params.get('range') ?? '7d') as DateRange,
    severities: (params.get('severities')?.split(',').filter(Boolean) ?? []) as Severity[],
    categories: (params.get('categories')?.split(',').filter(Boolean) ?? []) as AlertCategory[],
  };
}
