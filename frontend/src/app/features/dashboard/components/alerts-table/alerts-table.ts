import { ChangeDetectionStrategy, Component, input } from '@angular/core';

import { AlertStatus, SocAlert } from '../../../../core/models/soc.models';

/**
 * Latest alerts — the table view that keeps every value reachable
 * without hovering a chart.
 */
@Component({
  selector: 'soc-alerts-table',
  templateUrl: './alerts-table.html',
  styleUrl: './alerts-table.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AlertsTableComponent {
  readonly alerts = input.required<SocAlert[]>();

  protected statusLabel(status: AlertStatus): string {
    return {
      open: 'Open',
      investigating: 'Investigating',
      contained: 'Contained',
      resolved: 'Resolved',
    }[status];
  }

  protected timeAgo(iso: string): string {
    const diffMin = Math.max(0, Math.round((Date.now() - Date.parse(iso)) / 60_000));
    if (diffMin < 60) return `${diffMin}m ago`;
    const h = Math.round(diffMin / 60);
    if (h < 48) return `${h}h ago`;
    return `${Math.round(h / 24)}d ago`;
  }
}
