import { Component, input } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';

import { JourneyStep } from '../core/models';

/** Các bước lộ trình theo ngày (kênh, hành động, ưu đãi) — dùng ở hồ sơ khách, Lộ trình, Chấm điểm. */
@Component({
  selector: 'app-journey-timeline',
  imports: [MatIconModule],
  template: `
    <ol class="timeline">
      @for (s of steps(); track $index) {
        <li>
          <span class="day">Ngày {{ s.day }}</span>
          <div>
            <span class="channel">{{ s.channel }}</span>
            <p>{{ s.action }}</p>
            @if (s.offer) {
              <span class="offer"><mat-icon inline>redeem</mat-icon> {{ s.offer }}</span>
            }
          </div>
        </li>
      }
    </ol>
  `,
  styles: `
    .timeline { list-style: none; margin: 8px 0 8px 6px; padding: 0; border-left: 2px solid var(--mat-sys-outline-variant); }
    li { display: grid; grid-template-columns: 64px 1fr; gap: 8px; padding: 0 0 12px 14px; position: relative; }
    li:last-child { padding-bottom: 0; }
    li::before {
      content: ''; position: absolute; left: -7px; top: 4px; width: 12px; height: 12px;
      border-radius: 50%; background: var(--mat-sys-primary);
    }
    p { margin: 2px 0; }
    .day { font: var(--mat-sys-label-large); color: var(--mat-sys-primary); }
    .channel { font: var(--mat-sys-body-small); color: var(--mat-sys-on-surface-variant); }
    .offer {
      display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 8px;
      font: var(--mat-sys-label-medium);
      background: var(--mat-sys-tertiary-container); color: var(--mat-sys-on-tertiary-container);
    }
  `,
})
export class JourneyTimeline {
  readonly steps = input.required<JourneyStep[]>();
}
