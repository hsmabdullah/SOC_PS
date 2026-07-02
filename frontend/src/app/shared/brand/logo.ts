import { ChangeDetectionStrategy, Component, input, signal } from '@angular/core';

/**
 * Pak Suzuki brand lockup.
 *
 * The vertical variant renders the provided brand asset
 * `branding/Suzuki_logo_2025_(vertical).png` (drop the PNG into
 * `frontend/public/branding/`). Until the PNG is present — and always for
 * the compact `mark` variant — an inline SVG rendition of the "S" mark in
 * brand red is used, so the app never shows a broken image.
 */
@Component({
  selector: 'soc-logo',
  templateUrl: './logo.html',
  styleUrl: './logo.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LogoComponent {
  /** 'mark' = S emblem only · 'vertical' = full vertical lockup */
  readonly variant = input<'mark' | 'vertical'>('mark');
  readonly markSize = input(36);

  protected readonly pngFailed = signal(false);
  protected readonly pngSrc = 'branding/Suzuki_logo_2025_(vertical).png';
}
