import { Injectable, computed, inject, signal } from '@angular/core';
import { Subscription, forkJoin } from 'rxjs';

import { SocApiService } from '../api/soc-api.service';
import {
  AlertCategory,
  DashboardFilters,
  DashboardSummary,
  DateRange,
  Severity,
  SocAlert,
} from '../models/soc.models';

const DEFAULT_FILTERS: DashboardFilters = {
  range: '7d',
  severities: [],
  categories: [],
};

/**
 * Signal-based store for the dashboard view.
 *
 * Filters are the single source of truth; every mutation triggers one
 * refetch, and every widget derives from the same `summary` /  `alerts`
 * signals so the numbers on screen always agree.
 */
@Injectable({ providedIn: 'root' })
export class DashboardStore {
  private readonly api = inject(SocApiService);

  private readonly _filters = signal<DashboardFilters>(DEFAULT_FILTERS);
  private readonly _summary = signal<DashboardSummary | null>(null);
  private readonly _alerts = signal<SocAlert[]>([]);
  private readonly _loading = signal(false);
  private readonly _error = signal<string | null>(null);
  private inflight: Subscription | null = null;

  readonly filters = this._filters.asReadonly();
  readonly summary = this._summary.asReadonly();
  readonly alerts = this._alerts.asReadonly();
  readonly loading = this._loading.asReadonly();
  readonly error = this._error.asReadonly();

  /** True while refetching with data already on screen (dim, don't blank). */
  readonly refreshing = computed(() => this._loading() && this._summary() !== null);

  readonly activeFilterCount = computed(() => {
    const f = this._filters();
    return (f.range !== DEFAULT_FILTERS.range ? 1 : 0) + f.severities.length + f.categories.length;
  });

  constructor() {
    this.refetch();
  }

  setRange(range: DateRange): void {
    if (this._filters().range === range) return;
    this._filters.update((f) => ({ ...f, range }));
    this.refetch();
  }

  toggleSeverity(severity: Severity): void {
    this._filters.update((f) => ({
      ...f,
      severities: f.severities.includes(severity)
        ? f.severities.filter((s) => s !== severity)
        : [...f.severities, severity],
    }));
    this.refetch();
  }

  toggleCategory(category: AlertCategory): void {
    this._filters.update((f) => ({
      ...f,
      categories: f.categories.includes(category)
        ? f.categories.filter((c) => c !== category)
        : [...f.categories, category],
    }));
    this.refetch();
  }

  clearFilters(): void {
    this._filters.set(DEFAULT_FILTERS);
    this.refetch();
  }

  refetch(): void {
    const filters = this._filters();
    this.inflight?.unsubscribe();
    this._loading.set(true);
    this._error.set(null);

    this.inflight = forkJoin({
      summary: this.api.getDashboardSummary(filters),
      alerts: this.api.getAlerts(filters, 8),
    }).subscribe({
      next: ({ summary, alerts }) => {
        this._summary.set(summary);
        this._alerts.set(alerts.items);
        this._loading.set(false);
      },
      error: () => {
        this._error.set('Could not reach the SOC API. Check the FastAPI service and retry.');
        this._loading.set(false);
      },
    });
  }
}
