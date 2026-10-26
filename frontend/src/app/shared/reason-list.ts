import { Component, input } from '@angular/core';

import { Reason } from '../core/models';
import { formatField } from './constants';

/** BR-05: tối đa 3 lý do đẩy p_churn lên, mỗi lý do so giá trị của khách với trung bình toàn tệp. */
@Component({
  selector: 'app-reason-list',
  template: `
    @if (reasons().length) {
      <ol class="reasons">
        @for (r of reasons(); track r.feature) {
          @let c = compare(r);
          <li>
            <div class="head">
              <span class="label">{{ r.label }}</span>
              <strong>{{ format(r.feature, r.value) }}</strong>
            </div>
            @if (c) {
              <div class="bars" aria-hidden="true">
                <span class="row"><span class="bar mine" [style.width.%]="c.value"></span></span>
                <span class="row"><span class="bar avg" [style.width.%]="c.avg"></span></span>
              </div>
              <span class="small">Trung bình {{ format(r.feature, r.avg) }} · {{ c.diff }}</span>
            }
          </li>
        }
      </ol>
      <div class="legend small">
        <span><i class="dot mine"></i> Khách này</span>
        <span><i class="dot avg"></i> Trung bình toàn tệp</span>
      </div>
    } @else {
      <p class="small">Không có yếu tố nào đẩy xác suất rời bỏ lên đáng kể.</p>
    }
  `,
  styles: `
    .reasons { margin: 8px 0 0; padding-left: 20px; display: flex; flex-direction: column; gap: 16px; }
    li::marker { font-weight: 600; color: var(--mat-sys-primary); }
    .head { display: flex; justify-content: space-between; gap: 8px; }
    .label { font: var(--mat-sys-title-small); }
    .bars { display: flex; flex-direction: column; gap: 3px; margin: 6px 0 4px; }
    .row { height: 8px; border-radius: 4px; background: var(--mat-sys-surface-container); }
    .bar { display: block; height: 100%; border-radius: 4px; }
    .mine { background: var(--mat-sys-error); }
    .avg { background: var(--mat-sys-outline); }
    .small { font: var(--mat-sys-body-small); color: var(--mat-sys-on-surface-variant); }
    .legend { display: flex; gap: 16px; margin-top: 16px; }
    .dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; vertical-align: middle; }
  `,
})
export class ReasonList {
  readonly reasons = input.required<Reason[]>();
  protected readonly format = formatField;

  /** Vạch so sánh giá trị của khách với trung bình toàn tệp (cùng thang). */
  protected compare(r: Reason): { value: number; avg: number; diff: string } | null {
    if (typeof r.value !== 'number' || r.avg === null) return null;
    const max = Math.max(r.value, r.avg) || 1;
    const pct = r.avg ? Math.round(((r.value - r.avg) / r.avg) * 100) : 0;
    const diff = pct === 0 ? 'bằng trung bình' : `${pct > 0 ? 'cao' : 'thấp'} hơn trung bình ${Math.abs(pct)}%`;
    return { value: (r.value / max) * 100, avg: (r.avg / max) * 100, diff };
  }
}
