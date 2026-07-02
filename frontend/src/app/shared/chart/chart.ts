import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  OnDestroy,
  effect,
  input,
  viewChild,
} from '@angular/core';
import { Chart, ChartConfiguration } from 'chart.js';

import { applyChartTheme } from './chart-theme';

/**
 * Thin, reusable Chart.js host. The parent supplies a full
 * ChartConfiguration via signal input; updates re-render in place with
 * Chart.js's built-in transition so filter changes animate smoothly.
 * The host element must be given a height by its parent.
 */
@Component({
  selector: 'soc-chart',
  template: '<canvas #canvas role="img" [attr.aria-label]="ariaLabel()"></canvas>',
  styles: [
    ':host { display: block; position: relative; height: 100%; min-height: 200px; }',
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ChartComponent implements OnDestroy {
  readonly config = input.required<ChartConfiguration>();
  readonly ariaLabel = input('chart');

  private readonly canvas = viewChild<ElementRef<HTMLCanvasElement>>('canvas');
  private chart: Chart | null = null;

  constructor() {
    applyChartTheme();
    effect(() => {
      const canvas = this.canvas()?.nativeElement;
      const config = this.config();
      if (!canvas) return;
      if (!this.chart) {
        this.chart = new Chart(canvas, config);
      } else {
        this.chart.data = config.data;
        if (config.options) {
          this.chart.options = config.options;
        }
        this.chart.update();
      }
    });
  }

  ngOnDestroy(): void {
    this.chart?.destroy();
    this.chart = null;
  }
}
