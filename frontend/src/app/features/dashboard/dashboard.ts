import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, inject } from '@angular/core';

import { DashboardStore } from '../../core/state/dashboard.store';
import { AlertsTableComponent } from './components/alerts-table/alerts-table';
import { CategoryChartComponent } from './components/charts/category-chart';
import { SeverityChartComponent } from './components/charts/severity-chart';
import { SourcesChartComponent } from './components/charts/sources-chart';
import { TrendChartComponent } from './components/charts/trend-chart';
import { FilterBarComponent } from './components/filter-bar/filter-bar';
import { KpiCardComponent } from './components/kpi-card/kpi-card';
import { SystemStatusComponent } from './components/system-status/system-status';

@Component({
  selector: 'soc-dashboard',
  imports: [
    DatePipe,
    FilterBarComponent,
    KpiCardComponent,
    TrendChartComponent,
    SeverityChartComponent,
    CategoryChartComponent,
    SourcesChartComponent,
    SystemStatusComponent,
    AlertsTableComponent,
  ],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DashboardComponent {
  protected readonly store = inject(DashboardStore);
}
