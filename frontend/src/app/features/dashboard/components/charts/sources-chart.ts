import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { ChartConfiguration } from 'chart.js';

import { SourceCount } from '../../../../core/models/soc.models';
import { ChartComponent } from '../../../../shared/chart/chart';
import { CHART_COLORS, barValueLabelsPlugin } from '../../../../shared/chart/chart-theme';

/**
 * Top attack sources — nominal single-series bars, so every bar wears
 * slot-1 blue (bar length already encodes the value) with counts at the
 * tips. One series → no legend box; the title names it.
 */
@Component({
  selector: 'soc-sources-chart',
  imports: [ChartComponent],
  template: `
    <div class="card card--hover">
      <div class="card__head">
        <div>
          <h3 class="card__title">Top attack sources</h3>
          <p class="card__subtitle">Alerts per source IP in window</p>
        </div>
      </div>
      <div class="card__body chart-area">
        <soc-chart [config]="config()" ariaLabel="Bar chart of top attack source IP addresses" />
      </div>
    </div>
  `,
  styles: ['.chart-area { height: 280px; }'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SourcesChartComponent {
  readonly sources = input.required<SourceCount[]>();

  protected readonly config = computed<ChartConfiguration>(() => {
    const rows = this.sources();
    return {
      type: 'bar',
      data: {
        labels: rows.map((r) => r.source),
        datasets: [
          {
            data: rows.map((r) => r.count),
            backgroundColor: CHART_COLORS.slots[0],
            borderRadius: 4,
            borderSkipped: 'start',
            maxBarThickness: 16,
          },
        ],
      },
      options: {
        indexAxis: 'y',
        layout: { padding: { right: 40 } },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              afterTitle: (items) => rows[items[0].dataIndex]?.location ?? '',
            },
          },
        },
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
            ticks: {
              color: CHART_COLORS.inkSecondary,
              font: { size: 11.5 },
            },
          },
        },
      },
      plugins: [barValueLabelsPlugin],
    };
  });
}
