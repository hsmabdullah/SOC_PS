import { Chart, Plugin, registerables } from 'chart.js';

/**
 * Central Chart.js theme for the SOC dashboard.
 *
 * Categorical slots are a validated palette (CVD-safe adjacent pairs,
 * ≥3:1 contrast on white) in a FIXED order — assign in sequence, never
 * cycle, never reorder. Suzuki red is reserved for severity/status and
 * is never used as a series color.
 */

export const CHART_COLORS = {
  slots: ['#2952cc', '#d97706', '#0e8a72', '#6d28d9', '#c2367e', '#0891b2'],
  ink: '#0f172a',
  inkSecondary: '#475569',
  inkMuted: '#8a94a6',
  grid: '#eceff3',
  surface: '#ffffff',
} as const;

export const SEVERITY_COLORS: Record<string, string> = {
  critical: '#e20a17',
  high: '#ea580c',
  medium: '#d97706',
  low: '#64748b',
};

/** Fixed color per category — color follows the entity, never its rank. */
export const CATEGORY_COLORS: Record<string, string> = {
  Malware: CHART_COLORS.slots[0],
  Phishing: CHART_COLORS.slots[1],
  'Intrusion Attempt': CHART_COLORS.slots[2],
  'Data Exfiltration': CHART_COLORS.slots[3],
  'Policy Violation': CHART_COLORS.slots[4],
  DDoS: CHART_COLORS.slots[5],
};

export function withAlpha(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

let themed = false;

export function applyChartTheme(): void {
  if (themed) return;
  themed = true;

  Chart.register(...registerables);

  Chart.defaults.font.family = "'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif";
  Chart.defaults.font.size = 11;
  Chart.defaults.color = CHART_COLORS.inkMuted;
  // Mutate (don't replace) the animation defaults: the options resolver
  // expects the original key set to stay intact.
  const animation = Chart.defaults.animation as { duration?: number; easing?: string };
  if (animation && typeof animation === 'object') {
    animation.duration = 650;
    animation.easing = 'easeOutQuart';
  }
  Chart.defaults.maintainAspectRatio = false;
  Chart.defaults.responsive = true;

  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.plugins.legend.labels.boxWidth = 14;
  Chart.defaults.plugins.legend.labels.boxHeight = 8;
  Chart.defaults.plugins.legend.labels.color = CHART_COLORS.inkSecondary;
  Chart.defaults.plugins.legend.labels.font = { size: 12 };

  const tooltip = Chart.defaults.plugins.tooltip;
  tooltip.backgroundColor = '#0f172a';
  tooltip.titleColor = '#cbd5e1';
  tooltip.titleFont = { size: 11, weight: 'normal' };
  tooltip.bodyColor = '#ffffff';
  tooltip.bodyFont = { size: 12, weight: 600 };
  tooltip.padding = { top: 10, bottom: 10, left: 12, right: 12 };
  tooltip.cornerRadius = 10;
  tooltip.boxWidth = 8;
  tooltip.boxHeight = 8;
  tooltip.boxPadding = 4;
  tooltip.usePointStyle = true;
  tooltip.caretSize = 5;
}

/**
 * Crosshair for line charts: a vertical hairline snapped to the hovered X,
 * so the reader aims at a date, not at a 2px line.
 */
export const crosshairPlugin: Plugin = {
  id: 'socCrosshair',
  afterDraw(chart) {
    const actives = chart.tooltip?.getActiveElements();
    if (!actives?.length) return;
    const { ctx, chartArea } = chart;
    const x = actives[0].element.x;
    ctx.save();
    ctx.strokeStyle = 'rgba(15, 23, 42, 0.18)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(x, chartArea.top);
    ctx.lineTo(x, chartArea.bottom);
    ctx.stroke();
    ctx.restore();
  },
};

/**
 * Value labels at the tips of horizontal bars — the selective direct-label
 * channel (and the relief channel for status-colored fills).
 */
export const barValueLabelsPlugin: Plugin = {
  id: 'socBarValues',
  afterDatasetsDraw(chart) {
    const { ctx } = chart;
    ctx.save();
    ctx.font = "600 11px 'Inter', system-ui, sans-serif";
    ctx.fillStyle = CHART_COLORS.inkSecondary;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    chart.data.datasets.forEach((dataset, di) => {
      const meta = chart.getDatasetMeta(di);
      if (meta.hidden) return;
      meta.data.forEach((bar, i) => {
        const raw = dataset.data[i];
        if (raw == null) return;
        ctx.fillText(Number(raw).toLocaleString(), bar.x + 8, bar.y);
      });
    });
    ctx.restore();
  },
};

/** Total figure in the center of a doughnut. */
export function doughnutCenterPlugin(label: string): Plugin {
  return {
    id: 'socDoughnutCenter',
    afterDraw(chart) {
      const meta = chart.getDatasetMeta(0);
      if (!meta.data.length) return;
      const { x, y } = meta.data[0];
      const total = (chart.data.datasets[0].data as number[]).reduce((s, v) => s + (v ?? 0), 0);
      const { ctx } = chart;
      ctx.save();
      ctx.textAlign = 'center';
      ctx.font = "700 22px 'Inter', system-ui, sans-serif";
      ctx.fillStyle = CHART_COLORS.ink;
      ctx.fillText(total.toLocaleString(), x, y - 4);
      ctx.font = "500 11px 'Inter', system-ui, sans-serif";
      ctx.fillStyle = CHART_COLORS.inkMuted;
      ctx.fillText(label, x, y + 14);
      ctx.restore();
    },
  };
}
