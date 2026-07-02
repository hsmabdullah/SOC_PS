import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

import { Kpi } from '../../../../core/models/soc.models';

/**
 * Stat tile: label · value (auto-compact) · signed delta vs previous
 * period (colored by direction × whether up is good) · 12-point sparkline
 * in the de-emphasis hue with the current period marked in the accent.
 */
@Component({
  selector: 'soc-kpi-card',
  templateUrl: './kpi-card.html',
  styleUrl: './kpi-card.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class KpiCardComponent {
  readonly kpi = input.required<Kpi>();

  protected readonly displayValue = computed(() => {
    const v = this.kpi().value;
    if (v >= 10_000) {
      return new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 }).format(v);
    }
    return v.toLocaleString();
  });

  protected readonly deltaClass = computed(() => {
    const k = this.kpi();
    if (k.deltaPct === null || k.deltaPct === 0) return 'kpi__delta--flat';
    const improved = k.deltaPct > 0 === (k.goodWhen === 'up');
    return improved ? 'kpi__delta--good' : 'kpi__delta--bad';
  });

  /** Sparkline geometry (viewBox 0 0 100 30). */
  protected readonly sparkPath = computed(() => this.buildPath().line);
  protected readonly sparkArea = computed(() => this.buildPath().area);
  protected readonly sparkDot = computed(() => this.buildPath().dot);

  private buildPath(): { line: string; area: string; dot: { x: number; y: number } } {
    const points = this.kpi().trend;
    const max = Math.max(...points, 1);
    const min = Math.min(...points, 0);
    const span = max - min || 1;
    const coords = points.map((v, i) => ({
      x: (i / (points.length - 1)) * 100,
      y: 27 - ((v - min) / span) * 24,
    }));
    const line = coords.map((c, i) => `${i === 0 ? 'M' : 'L'}${c.x.toFixed(1)} ${c.y.toFixed(1)}`).join(' ');
    const area = `${line} L100 30 L0 30 Z`;
    return { line, area, dot: coords[coords.length - 1] };
  }
}
