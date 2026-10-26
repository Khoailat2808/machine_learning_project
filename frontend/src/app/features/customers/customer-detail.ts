import { CurrencyPipe, DatePipe, KeyValuePipe, Location, LowerCasePipe, PercentPipe } from '@angular/common';
import { HttpErrorResponse, httpResource } from '@angular/common/http';
import { Component, computed, inject, input } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Router, RouterLink } from '@angular/router';

import { environment } from '../../../environments/environment';
import { CustomerDetail as Detail, ModelInfo } from '../../core/models';
import { CHANNELS, FIELD_LABELS, LEVEL_LABELS, SEGMENT_NAMES, formatField } from '../../shared/constants';
import { JourneyTimeline } from '../../shared/journey-timeline';
import { ReasonList } from '../../shared/reason-list';

const GROUPS = [
  { key: 'profile', title: 'Hồ sơ', icon: 'badge' },
  { key: 'behavior', title: 'Hành vi', icon: 'touch_app' },
  { key: 'purchase', title: 'Mua sắm', icon: 'shopping_cart' },
  { key: 'engagement', title: 'Tương tác', icon: 'forum' },
] as const;

// FR-CUS-03, 04: hồ sơ khách, 3 lý do rủi ro, lộ trình và kênh đề xuất
@Component({
  selector: 'app-customer-detail',
  imports: [
    CurrencyPipe, DatePipe, KeyValuePipe, LowerCasePipe, PercentPipe, RouterLink,
    MatButtonModule, MatCardModule, MatIconModule, MatProgressBarModule, MatTooltipModule,
    JourneyTimeline, ReasonList,
  ],
  templateUrl: './customer-detail.html',
  styleUrl: './customer-detail.css',
})
export class CustomerDetail {
  private readonly location = inject(Location);
  private readonly router = inject(Router);

  readonly id = input.required<string>(); // :id trên route

  protected readonly groups = GROUPS;
  protected readonly labels = FIELD_LABELS;
  protected readonly levels = LEVEL_LABELS;
  protected readonly segmentNames = SEGMENT_NAMES;
  protected readonly channels = CHANNELS;
  protected readonly format = formatField;
  protected readonly keepOrder = () => 0; // keyvalue giữ thứ tự trường như API trả về

  protected readonly detail = httpResource<Detail>(() => `${environment.apiUrl}/customers/${encodeURIComponent(this.id())}`);
  protected readonly info = httpResource<ModelInfo>(() => `${environment.apiUrl}/model/info`);

  protected readonly notFound = computed(() => (this.detail.error() as HttpErrorResponse | undefined)?.status === 404);
  protected readonly tau = computed(() => (this.info.hasValue() ? this.info.value().thresholds.tau : null));

  /** Quay về danh sách giữ nguyên bộ lọc nếu đến từ đó; mở link trực tiếp thì về /customers. */
  back(): void {
    if ((history.state?.navigationId ?? 1) > 1) this.location.back();
    else this.router.navigate(['/customers']);
  }
}
