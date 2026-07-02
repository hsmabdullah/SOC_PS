import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { DecimalPipe } from '@angular/common';

import { SystemHealth } from '../../../../core/models/soc.models';

/**
 * Health of the security stack. State is icon + label (never color
 * alone); the uptime meter's unfilled track is a lighter step of the
 * fill's own ramp so state reads across the whole bar.
 */
@Component({
  selector: 'soc-system-status',
  imports: [DecimalPipe],
  templateUrl: './system-status.html',
  styleUrl: './system-status.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SystemStatusComponent {
  readonly systems = input.required<SystemHealth[]>();

  protected stateLabel(state: SystemHealth['state']): string {
    return { operational: 'Operational', degraded: 'Degraded', down: 'Offline' }[state];
  }
}
