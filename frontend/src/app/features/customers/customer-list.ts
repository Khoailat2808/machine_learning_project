import { CurrencyPipe, PercentPipe, DecimalPipe } from '@angular/common';
import { HttpClient, httpResource } from '@angular/common/http';
import { Component, ElementRef, computed, inject, input, linkedSignal, signal, viewChild } from '@angular/core';
import { takeUntilDestroyed, toSignal } from '@angular/core/rxjs-interop';
import { BreakpointObserver } from '@angular/cdk/layout';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatPaginatorIntl, MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatSortModule, Sort } from '@angular/material/sort';
import { MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Router, RouterLink } from '@angular/router';
import { Subject, debounceTime, distinctUntilChanged, map } from 'rxjs';

import { environment } from '../../../environments/environment';
import { CustomerRow, Page } from '../../core/models';
import { COUNTRIES, COUNTRY_CITIES, LEVEL_LABELS, SEGMENT_NAMES, SEGMENTS } from '../../shared/constants';
import { downloadFile } from '../../shared/download';
import { ViPaginatorIntl } from '../../shared/paginator-intl';

type Filters = Partial<Record<'segment' | 'risk' | 'tier' | 'country' | 'city' | 'q' | 'sort' | 'page', string | null>>;

// FR-CUS-01, 02, 05: toàn bộ trạng thái (lọc, tìm, sắp xếp, trang) nằm trên URL query
@Component({
  selector: 'app-customer-list',
  imports: [
    CurrencyPipe, DecimalPipe, PercentPipe, RouterLink,
    MatButtonModule, MatChipsModule, MatFormFieldModule, MatIconModule, MatInputModule, MatPaginatorModule,
    MatProgressBarModule, MatProgressSpinnerModule, MatSelectModule, MatSortModule, MatTableModule, MatTooltipModule,
  ],
  providers: [{ provide: MatPaginatorIntl, useClass: ViPaginatorIntl }],
  templateUrl: './customer-list.html',
  styleUrl: './customer-list.css',
})
export class CustomerList {
  private readonly router = inject(Router);
  private readonly http = inject(HttpClient);
  private readonly snackBar = inject(MatSnackBar);
  private readonly tableTop = viewChild<ElementRef<HTMLElement>>('tableTop');

  // Query params (withComponentInputBinding)
  readonly segment = input<string>();
  readonly risk = input<string>();
  readonly tier = input<string>();
  readonly country = input<string>();
  readonly city = input<string>();
  readonly q = input<string>();
  readonly sort = input<string>();
  readonly page = input<string>();

  protected readonly segments = SEGMENTS;
  protected readonly segmentNames = SEGMENT_NAMES;
  protected readonly levels = LEVEL_LABELS;
  protected readonly countries = COUNTRIES;
  // Màn hình hẹp: bỏ nơi ở / CLV, đưa VaR lên trước để không phải cuộn ngang
  protected readonly narrow = toSignal(
    inject(BreakpointObserver).observe('(max-width: 700px)').pipe(map((r) => r.matches)),
    { initialValue: false },
  );
  protected readonly columns = computed(() =>
    this.narrow()
      ? ['customer_id', 'segment', 'value_at_risk', 'p_churn']
      : ['customer_id', 'location', 'segment', 'p_churn', 'clv_potential', 'value_at_risk'],
  );

  protected readonly selectedSegments = computed(() => this.segment()?.split(',').filter(Boolean) ?? []);
  protected readonly cities = computed(() => COUNTRY_CITIES[this.country() ?? ''] ?? []);
  protected readonly sortState = computed(() => {
    const sort = this.sort() || '-value_at_risk';
    return { active: sort.replace('-', ''), direction: sort.startsWith('-') ? 'desc' : 'asc' } as const;
  });
  protected readonly pageIndex = computed(() => Math.max(0, Number(this.page() || 1) - 1));
  protected readonly activeFilters = computed(
    () => [this.segment(), this.risk(), this.tier(), this.country(), this.city(), this.q()].filter(Boolean).length,
  );

  private readonly params = computed(() => {
    const p: Record<string, string> = {};
    for (const key of ['segment', 'risk', 'tier', 'country', 'city', 'q', 'sort', 'page'] as const) {
      const v = this[key]();
      if (v) p[key] = v;
    }
    return p;
  });

  protected readonly result = httpResource<Page<CustomerRow>>(() => ({
    url: `${environment.apiUrl}/customers`,
    params: this.params(),
  }));
  // Giữ bảng cũ trong lúc tải trang mới → không nhấp nháy
  protected readonly data = linkedSignal<Page<CustomerRow> | undefined, Page<CustomerRow> | undefined>({
    source: () => (this.result.hasValue() ? this.result.value() : undefined),
    computation: (value, previous) => value ?? previous?.value,
  });

  protected readonly exporting = signal(false);
  private readonly search$ = new Subject<string>();

  constructor() {
    this.search$
      .pipe(debounceTime(350), distinctUntilChanged(), takeUntilDestroyed())
      .subscribe((q) => this.update({ q: q.trim() || null }));
  }

  /** Đổi bộ lọc → về trang 1. */
  update(filters: Filters, keepPage = false): void {
    const queryParams = keepPage ? filters : { ...filters, page: null };
    this.router.navigate([], { queryParams, queryParamsHandling: 'merge' });
  }

  onSearch(value: string): void {
    this.search$.next(value);
  }

  setSegments(values: string[]): void {
    this.update({ segment: values.length ? [...values].sort().join(',') : null });
  }

  setCountry(country: string): void {
    this.update({ country: country || null, city: null });
  }

  onSort(sort: Sort): void {
    this.update({ sort: sort.direction === 'asc' ? sort.active : `-${sort.active}` });
  }

  onPage(event: PageEvent): void {
    this.update({ page: event.pageIndex ? String(event.pageIndex + 1) : null }, true);
    this.tableTop()?.nativeElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  clearFilters(): void {
    this.router.navigate([], { queryParams: { sort: this.sort() || null } });
  }

  open(row: CustomerRow): void {
    this.router.navigate(['/customers', row.customer_id]);
  }

  exportCsv(): void {
    const { page, ...params } = this.params();
    this.exporting.set(true);
    downloadFile(this.http, `${environment.apiUrl}/customers/export`, params).subscribe({
      next: () => this.exporting.set(false),
      error: () => {
        this.exporting.set(false);
        this.snackBar.open('Xuất CSV thất bại, thử lại sau.', 'Đóng', { duration: 5000 });
      },
    });
  }
}
