import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { ChartConfiguration } from 'chart.js';

import { SeverityCount } from '../../../../core/models/soc.models';
import { ChartComponent } from '../../../../shared/chart/chart';
import {
  CHART_COLORS,
  SEVERITY_COLORS,
  barValueLabelsPlugin,
} from '../../../../shared/chart/chart-theme';

/**
 * Severity breakdown as horizontal bars wearing the reserved status
 * colors. Severity is named on the axis and counted at the bar tip, so
 * color never carries the meaning alone.
 */
@Component({
  selector: 'soc-severity-chart',
  imports: [ChartComponent],
  template: `
    <div class="card card--hover">
      <div class="card__head">
        <div>
          <h3 class="card__title">By severity</h3>
          <p class="card__subtitle">Alerts in window</p>
        </div>
      </div>
      <div class="card__body chart-area">
        <soc-chart [config]="config()" ariaLabel="Bar chart of alerts by severity" />
      </div>
    </div>
  `,
  styles: ['.chart-area { height: 300px; }'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SeverityChartComponent {
  readonly severities = input.required<SeverityCount[]>();

  protected readonly config = computed<ChartConfiguration>(() => {
    const rows = this.severities();
    return {
      type: 'bar',
      data: {
        labels: rows.map((r) => r.severity.charAt(0).toUpperCase() + r.severity.slice(1)),
        datasets: [
          {
            data: rows.map((r) => r.count),
            backgroundColor: rows.map((r) => SEVERITY_COLORS[r.severity]),
            borderRadius: 4,
            borderSkipped: 'start',
            maxBarThickness: 22,
          },
        ],
      },
      options: {
        indexAxis: 'y',
        layout: { padding: { right: 44 } },
        plugins: { legend: { display: false } },
        scales: {
          x: {
            beginAtZero: true,
            grid: { color: CHART_COLORS.grid },
            border: { display: false },
            ticks: { maxTicksLimit: 5, precision: 0 },
          },
          y: {
            grid: { display: false },
            border: { display: false },
            ticks: { color: CHART_COLORS.inkSecondary, font: { size: 12, weight: 600 } },
          },
        },
      },
      plugins: [barValueLabelsPlugin],
    };
  });
}
