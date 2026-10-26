import { CurrencyPipe, DecimalPipe, PercentPipe } from '@angular/common';
import { HttpClient, httpResource } from '@angular/common/http';
import { Component, computed, inject, input, linkedSignal, signal } from '@angular/core';
import { toObservable, toSignal } from '@angular/core/rxjs-interop';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSliderModule } from '@angular/material/slider';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { debounceTime } from 'rxjs';

import { environment } from '../../../environments/environment';
import { CampaignParams, CampaignPreview, JourneysResponse } from '../../core/models';
import { COUNTRIES, COUNTRY_CITIES, SEGMENT_NAMES, SEGMENTS } from '../../shared/constants';
import { downloadFile } from '../../shared/download';

/** Ô số: trống → null, ngoài miền → NaN để báo lỗi tại ô. */
function parseNumber(value: string, min: number, max = Infinity): number | null {
  if (value.trim() === '') return null;
  const n = Number(value);
  return n >= min && n <= max ? n : NaN;
}

// FR-CAMP-01 → 03: thiết lập → xem trước (tự cập nhật khi đổi tham số) → xuất danh sách
@Component({
  selector: 'app-campaigns',
  imports: [
    CurrencyPipe, DecimalPipe, PercentPipe,
    MatButtonModule, MatCardModule, MatChipsModule, MatFormFieldModule, MatIconModule, MatInputModule,
    MatProgressBarModule, MatProgressSpinnerModule, MatSelectModule, MatSlideToggleModule, MatSliderModule,
    MatTooltipModule,
  ],
  templateUrl: './campaigns.html',
  styleUrl: './campaigns.css',
})
export class Campaigns {
  private readonly http = inject(HttpClient);
  private readonly snackBar = inject(MatSnackBar);

  // Link từ Tổng quan / Lộ trình / hồ sơ khách: ?segment=S1&country=USA
  readonly segment = input<string>();
  readonly country = input<string>();

  protected readonly segmentCodes = SEGMENTS;
  protected readonly countries = COUNTRIES;

  // Tham số (FR-CAMP-01): mặc định S1 + S2, k theo phân khúc, s = 20%
  protected readonly segments = linkedSignal(() => this.segment()?.split(',').filter((s) => SEGMENTS.includes(s)) ?? ['S1', 'S2']);
  protected readonly selectedCountry = linkedSignal(() => this.country() ?? null);
  protected readonly city = linkedSignal<string | null, string | null>({ source: this.selectedCountry, computation: () => null });
  protected readonly budget = signal<number | null>(null);
  protected readonly overrideK = signal(false);
  protected readonly spendPct = signal<number | null>(5); // %, chỉ dùng khi ghi đè
  protected readonly successPct = signal(20);

  protected readonly cities = computed(() => COUNTRY_CITIES[this.selectedCountry() ?? ''] ?? []);
  protected readonly invalid = computed(() => ({
    budget: Number.isNaN(this.budget()),
    spendPct: this.overrideK() && (this.spendPct() === null || Number.isNaN(this.spendPct())),
  }));

  /** Body gửi API; undefined khi tham số chưa hợp lệ (không gọi API). */
  private readonly body = computed<CampaignParams | undefined>(() => {
    const invalid = this.invalid();
    if (!this.segments().length || invalid.budget || invalid.spendPct) return undefined;
    return {
      segments: this.segments(),
      country: this.selectedCountry(),
      city: this.city(),
      budget: this.budget(),
      spend_pct: this.overrideK() ? this.spendPct()! / 100 : null,
      success_rate: this.successPct() / 100,
    };
  });
  // Gõ ngân sách / kéo thanh trượt: chờ 300 ms rồi mới gọi lại
  private readonly request = toSignal(toObservable(this.body).pipe(debounceTime(300)));

  protected readonly preview = httpResource<CampaignPreview>(() => {
    const body = this.request();
    return body && { url: `${environment.apiUrl}/campaigns/preview`, method: 'POST', body };
  });
  // Giữ kết quả cũ trong lúc tính lại → số không nhảy về trống
  protected readonly result = linkedSignal<CampaignPreview | undefined, CampaignPreview | undefined>({
    source: () => (this.preview.hasValue() ? this.preview.value() : undefined),
    computation: (value, previous) => value ?? previous?.value,
  });
  /** Đang chờ debounce hoặc đang tải → kết quả hiện tại chưa khớp tham số. */
  protected readonly pending = computed(() => this.preview.isLoading() || this.body() !== this.request());
  /** Kết quả đang hiện không còn đúng với tham số (đang tính lại hoặc tham số sai) → làm mờ, khóa xuất. */
  protected readonly dim = computed(() => this.pending() || !this.body());

  // Tên, số khách và k mặc định của từng phân khúc
  protected readonly journeys = httpResource<JourneysResponse>(() => `${environment.apiUrl}/journeys`);
  protected readonly info = computed(() => {
    const list = this.journeys.hasValue() ? this.journeys.value().journeys : [];
    return Object.fromEntries(list.map((j) => [j.segment, j])) as Record<string, JourneysResponse['journeys'][number]>;
  });
  protected readonly name = (seg: string) => this.info()[seg]?.name ?? SEGMENT_NAMES[seg];

  protected readonly exporting = signal(false);
  protected readonly pctLabel = (v: number) => `${v}%`;

  protected setBudget(value: string): void {
    this.budget.set(parseNumber(value, 0.01));
  }

  protected setSpendPct(value: string): void {
    this.spendPct.set(parseNumber(value, 0.1, 100));
  }

  protected segmentRoi(s: CampaignPreview['by_segment'][number]): number | null {
    return s.cost ? (s.value_at_risk * (this.successPct() / 100) - s.cost) / s.cost : null;
  }

  protected exportCsv(): void {
    const body = this.request();
    if (!body) return;
    this.exporting.set(true);
    downloadFile(this.http, `${environment.apiUrl}/campaigns/export`, {}, body).subscribe({
      next: () => this.exporting.set(false),
      error: () => {
        this.exporting.set(false);
        this.snackBar.open('Xuất CSV thất bại, thử lại sau.', 'Đóng', { duration: 5000 });
      },
    });
  }
}
