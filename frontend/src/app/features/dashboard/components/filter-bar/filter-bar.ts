import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  HostListener,
  inject,
  signal,
} from '@angular/core';

import { DashboardStore } from '../../../../core/state/dashboard.store';
import {
  ALERT_CATEGORIES,
  DateRange,
  SEVERITIES,
} from '../../../../core/models/soc.models';

/**
 * The single filter row above the charts. Date range first (preset rows,
 * check-marked selection), then severity toggles and a category
 * multi-select. Every control writes to the shared store, so all widgets
 * below re-render against the same slice.
 */
@Component({
  selector: 'soc-filter-bar',
  templateUrl: './filter-bar.html',
  styleUrl: './filter-bar.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FilterBarComponent {
  protected readonly store = inject(DashboardStore);
  private readonly host = inject(ElementRef<HTMLElement>);

  protected readonly severities = SEVERITIES;
  protected readonly categories = ALERT_CATEGORIES;
  protected readonly ranges: { id: DateRange; label: string }[] = [
    { id: '24h', label: 'Last 24 hours' },
    { id: '7d', label: 'Last 7 days' },
    { id: '30d', label: 'Last 30 days' },
    { id: '90d', label: 'Last 90 days' },
  ];

  protected readonly openMenu = signal<'range' | 'category' | null>(null);

  protected rangeLabel(): string {
    return this.ranges.find((r) => r.id === this.store.filters().range)!.label;
  }

  protected toggleMenu(menu: 'range' | 'category'): void {
    this.openMenu.update((m) => (m === menu ? null : menu));
  }

  protected selectRange(range: DateRange): void {
    this.store.setRange(range);
    this.openMenu.set(null);
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (!this.host.nativeElement.contains(event.target as Node)) {
      this.openMenu.set(null);
    }
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.openMenu.set(null);
  }
}
