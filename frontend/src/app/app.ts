import { ChangeDetectionStrategy, Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { SplashComponent } from './features/splash/splash';
import { HeaderComponent } from './layout/header/header';

/**
 * Root shell: sticky brand header + routed content, with the animated
 * splash overlaid on first load. The dashboard renders (and fetches)
 * beneath the splash, so the reveal is seamless.
 */
@Component({
  selector: 'app-root',
  imports: [RouterOutlet, HeaderComponent, SplashComponent],
  templateUrl: './app.html',
  styleUrl: './app.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class App {
  protected readonly splashVisible = signal(true);
}
