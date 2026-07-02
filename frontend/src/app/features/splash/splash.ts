import {
  ChangeDetectionStrategy,
  Component,
  afterNextRender,
  output,
  signal,
} from '@angular/core';

import { LogoComponent } from '../../shared/brand/logo';

/**
 * Animated splash screen: the Pak Suzuki logo eases in over a clean white
 * canvas with a brand-gradient progress sweep, holds briefly, then the
 * whole overlay lifts and fades to reveal the dashboard already rendered
 * beneath it — a seamless transition, not a page swap.
 */
@Component({
  selector: 'soc-splash',
  imports: [LogoComponent],
  templateUrl: './splash.html',
  styleUrl: './splash.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SplashComponent {
  readonly done = output<void>();
  protected readonly leaving = signal(false);

  constructor() {
    afterNextRender(() => {
      const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
      const hold = reduced ? 400 : 1900;
      const exit = reduced ? 50 : 520;
      setTimeout(() => this.leaving.set(true), hold);
      setTimeout(() => this.done.emit(), hold + exit);
    });
  }
}
