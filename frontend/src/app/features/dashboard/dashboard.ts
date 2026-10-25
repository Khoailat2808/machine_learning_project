import { CurrencyPipe, DatePipe, DecimalPipe, PercentPipe } from '@angular/common';
import { httpResource } from '@angular/common/http';
import { Component, computed, inject, input } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { Router, RouterLink } from '@angular/router';

import { environment } from '../../../environments/environment';
import { DashboardSummary, ModelInfo } from '../../core/models';
import { COUNTRIES } from '../../shared/constants';

// FR-DASH-01 → 07: KPI, ma trận 2×3, biểu đồ, độ tin cậy mô hình, lọc quốc gia (bộ lọc nằm trên URL)
@Component({
  selector: 'app-dashboard',
  imports: [
    CurrencyPipe, DatePipe, DecimalPipe, PercentPipe, RouterLink,
    MatButtonModule, MatCardModule, MatFormFieldModule, MatProgressBarModule, MatSelectModule,
  ],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard {
  private readonly router = inject(Router);

  readonly country = input<string>(); // ?country=
  protected readonly countries = COUNTRIES;

  protected readonly summary = httpResource<DashboardSummary>(() => {
    const country = this.country();
    return { url: `${environment.apiUrl}/dashboard/summary`, params: country ? { country } : undefined };
  });
  protected readonly info = httpResource<ModelInfo>(() => `${environment.apiUrl}/model/info`);

  // value() ném lỗi khi resource lỗi → luôn kiểm hasValue() trước
  protected readonly histogramMax = computed(() =>
    this.summary.hasValue() ? Math.max(1, ...this.summary.value().p_churn_histogram.map((b) => b.count)) : 1,
  );
  protected readonly countryMax = computed(() =>
    this.summary.hasValue() ? Math.max(1, ...this.summary.value().by_country.map((c) => c.value_at_risk)) : 1,
  );
  protected readonly importanceMax = computed(() =>
    this.info.hasValue() ? this.info.value().global_importance[0]?.mean_abs_shap || 1 : 1,
  );

  setCountry(country: string | undefined): void {
    this.router.navigate([], { queryParams: { country: country || null }, queryParamsHandling: 'merge' });
  }

  /** Query cho trang Khách hàng / Chiến dịch: giữ quốc gia đang lọc. */
  protected linkParams(segment: string) {
    return { segment, country: this.country() || null };
  }
}
