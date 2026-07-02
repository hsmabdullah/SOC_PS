import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { AlertPage, DashboardFilters, DashboardSummary } from '../models/soc.models';

/**
 * Thin HTTP gateway to the FastAPI layer.
 *
 * Endpoints (FastAPI):
 *   GET {apiBaseUrl}/dashboard/summary?range=&severities=&categories=
 *   GET {apiBaseUrl}/alerts?range=&severities=&categories=&limit=
 *
 * While `environment.useMockApi` is true these requests are answered by
 * `mockApiInterceptor` with identical response shapes.
 */
@Injectable({ providedIn: 'root' })
export class SocApiService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiBaseUrl;

  getDashboardSummary(filters: DashboardFilters): Observable<DashboardSummary> {
    return this.http.get<DashboardSummary>(`${this.base}/dashboard/summary`, {
      params: this.toParams(filters),
    });
  }

  getAlerts(filters: DashboardFilters, limit = 8): Observable<AlertPage> {
    return this.http.get<AlertPage>(`${this.base}/alerts`, {
      params: this.toParams(filters).set('limit', limit),
    });
  }

  private toParams(filters: DashboardFilters): HttpParams {
    let params = new HttpParams().set('range', filters.range);
    if (filters.severities.length) {
      params = params.set('severities', filters.severities.join(','));
    }
    if (filters.categories.length) {
      params = params.set('categories', filters.categories.join(','));
    }
    return params;
  }
}
