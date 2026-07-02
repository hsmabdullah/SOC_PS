import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { ChartConfiguration } from 'chart.js';

import { TrendSeries } from '../../../../core/models/soc.models';
import { ChartComponent } from '../../../../shared/chart/chart';
import { CHART_COLORS, crosshairPlugin, withAlpha } from '../../../../shared/chart/chart-theme';

/**
 * Alert volume over time. 2px lines, 10% area wash, crosshair + single
 * tooltip listing every series at the hovered X.
 */
@Component({
  selector: 'soc-trend-chart',
  imports: [ChartComponent],
  template: `
    <div class="card card--hover">
      <div class="card__head">
        <div>
          <h3 class="card__title">Alert volume</h3>
          <p class="card__subtitle">New vs resolved alerts across the selected window</p>
        </div>
      </div>
      <div class="card__body chart-area">
        <soc-chart [config]="config()" ariaLabel="Line chart of new and resolved alerts over time" />
      </div>
    </div>
  `,
  styles: ['.chart-area { height: 300px; }'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TrendChartComponent {
  readonly trend = input.required<TrendSeries>();

  protected readonly config = computed<ChartConfiguration>(() => {
    const trend = this.trend();
    const colors = [CHART_COLORS.slots[0], CHART_COLORS.slots[2]]; // blue, teal

    return {
      type: 'line',
      data: {
        labels: trend.labels,
        datasets: trend.series.map((s, i) => ({
          label: s.label,
          data: s.points,
          borderColor: colors[i],
          backgroundColor: withAlpha(colors[i], 0.08),
          fill: true,
          borderWidth: 2,
          tension: 0.35,
          pointRadius: 0,
          pointHitRadius: 24,
          pointHoverRadius: 5,
          pointHoverBackgroundColor: colors[i],
          pointHoverBorderColor: CHART_COLORS.surface,
          pointHoverBorderWidth: 2,
        })),
      },
      options: {
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            position: 'top',
            align: 'end',
            labels: { pointStyle: 'line', usePointStyle: true },
          },
        },
        scales: {
          x: {
            grid: { display: false },
            border: { color: CHART_COLORS.grid },
            ticks: { maxTicksLimit: 8, maxRotation: 0 },
          },
          y: {
            beginAtZero: true,
            grid: { color: CHART_COLORS.grid },
            border: { display: false },
            ticks: { maxTicksLimit: 5, precision: 0 },
          },
        },
      },
      plugins: [crosshairPlugin],
    };
  });
}
