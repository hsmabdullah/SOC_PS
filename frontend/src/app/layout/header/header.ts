import { ChangeDetectionStrategy, Component, signal } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';

import { LogoComponent } from '../../shared/brand/logo';

@Component({
  selector: 'soc-header',
  imports: [RouterLink, RouterLinkActive, LogoComponent],
  templateUrl: './header.html',
  styleUrl: './header.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HeaderComponent {
  protected readonly nav = [
    { label: 'Dashboard', path: '/', enabled: true },
    { label: 'Alerts', path: '/alerts', enabled: false },
    { label: 'Intelligence', path: '/intel', enabled: false },
    { label: 'Reports', path: '/reports', enabled: false },
  ];

  protected readonly clock = signal(this.now());

  constructor() {
    setInterval(() => this.clock.set(this.now()), 30_000);
  }

  private now(): string {
    return new Intl.DateTimeFormat('en', {
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'UTC',
      hour12: false,
    }).format(new Date());
  }
}
