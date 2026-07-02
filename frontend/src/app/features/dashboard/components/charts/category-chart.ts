import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { ChartConfiguration } from 'chart.js';

import { CategoryCount } from '../../../../core/models/soc.models';
import { ChartComponent } from '../../../../shared/chart/chart';
import { categoryColor, doughnutCenterPlugin } from '../../../../shared/chart/chart-theme';

/**
 * Threat-category mix. Each category keeps its fixed slot color (color
 * follows the entity — filters never repaint survivors); 2px surface
 * gaps separate the segments; the legend carries identity.
 */
@Component({
  selector: 'soc-category-chart',
  imports: [ChartComponent],
  template: `
    <div class="card card--hover">
      <div class="card__head">
        <div>
          <h3 class="card__title">Threat categories</h3>
          <p class="card__subtitle">Share of alerts in window</p>
        </div>
      </div>
      <div class="card__body chart-area">
        <soc-chart [config]="config()" ariaLabel="Doughnut chart of alerts by threat category" />
      </div>
    </div>
  `,
  styles: ['.chart-area { height: 280px; }'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CategoryChartComponent {
  readonly categories = input.required<CategoryCount[]>();

  protected readonly config = computed<ChartConfiguration>(() => {
    const rows = this.categories();
    return {
      type: 'doughnut',
      data: {
        labels: rows.map((r) => r.category),
        datasets: [
          {
            data: rows.map((r) => r.count),
            backgroundColor: rows.map((r, i) => categoryColor(r.category, i)),
            borderColor: '#ffffff',
            borderWidth: 2,
            hoverOffset: 6,
          },
        ],
      },
      options: {
        cutout: '68%',
        layout: { padding: 8 },
        plugins: {
          legend: {
            position: 'right',
            labels: { pointStyle: 'circle', padding: 12 },
          },
        },
      },
      plugins: [doughnutCenterPlugin('alerts')],
    };
  });
}
