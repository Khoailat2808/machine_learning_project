import { CurrencyPipe, LowerCasePipe, PercentPipe } from '@angular/common';
import { HttpClient, HttpErrorResponse, httpResource } from '@angular/common/http';
import { Component, ElementRef, computed, inject, signal, viewChild } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormControl, FormGroup, ReactiveFormsModule, ValidatorFn, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Router, RouterLink } from '@angular/router';

import { environment } from '../../../environments/environment';
import { ModelInfo, PredictResult } from '../../core/models';
import { CHANNELS, COUNTRIES, COUNTRY_CITIES, FIELD_LABELS, LEVEL_LABELS, SEGMENT_NAMES } from '../../shared/constants';
import { JourneyTimeline } from '../../shared/journey-timeline';
import { ReasonList } from '../../shared/reason-list';

interface Field {
  key: string;
  kind: 'int' | 'float' | 'select';
  min?: number;
  max?: number;
  required?: boolean;
  unit?: string;
  options?: { value: string; label: string }[];
}

// FR-PRED: bảng validate 23 trường (docs/02 mục 9), cùng miền với model Customer ở backend
const GROUPS: { title: string; icon: string; fields: Field[] }[] = [
  {
    title: 'Hồ sơ', icon: 'badge', fields: [
      { key: 'Gender', kind: 'select', required: true,
        options: [{ value: 'Male', label: 'Nam' }, { value: 'Female', label: 'Nữ' }, { value: 'Other', label: 'Khác' }] },
      { key: 'Age', kind: 'int', min: 13, max: 100 },
      { key: 'Country', kind: 'select', required: true, options: COUNTRIES.map((c) => ({ value: c, label: c })) },
      { key: 'City', kind: 'select', required: true },
      { key: 'Signup_Quarter', kind: 'select', required: true,
        options: ['Q1', 'Q2', 'Q3', 'Q4'].map((q) => ({ value: q, label: q })) },
      { key: 'Membership_Years', kind: 'float', min: 0, max: 10, required: true, unit: 'năm' },
    ],
  },
  {
    title: 'Hành vi', icon: 'touch_app', fields: [
      { key: 'Login_Frequency', kind: 'int', min: 0, max: 50, required: true },
      { key: 'Session_Duration_Avg', kind: 'float', min: 0, max: 120, unit: 'phút' },
      { key: 'Pages_Per_Session', kind: 'float', min: 0, max: 30 },
      { key: 'Mobile_App_Usage', kind: 'float', min: 0, max: 100 },
      { key: 'Wishlist_Items', kind: 'int', min: 0, max: 50 },
      { key: 'Cart_Abandonment_Rate', kind: 'float', min: 0, max: 100, required: true, unit: '%' },
    ],
  },
  {
    title: 'Mua sắm', icon: 'shopping_cart', fields: [
      { key: 'Total_Purchases', kind: 'float', min: 0, max: 150, required: true },
      { key: 'Average_Order_Value', kind: 'float', min: 0.01, max: 10000, required: true, unit: 'USD' },
      { key: 'Days_Since_Last_Purchase', kind: 'int', min: 0, max: 365, unit: 'ngày' },
      { key: 'Discount_Usage_Rate', kind: 'float', min: 0, max: 100, unit: '%' },
      { key: 'Returns_Rate', kind: 'float', min: 0, max: 100, unit: '%' },
      { key: 'Payment_Method_Diversity', kind: 'int', min: 1, max: 5 },
      { key: 'Credit_Balance', kind: 'float', min: 0, max: 10000, unit: 'USD' },
    ],
  },
  {
    title: 'Tương tác', icon: 'forum', fields: [
      { key: 'Email_Open_Rate', kind: 'float', min: 0, max: 100, unit: '%' },
      { key: 'Customer_Service_Calls', kind: 'int', min: 0, max: 30 },
      { key: 'Product_Reviews_Written', kind: 'int', min: 0, max: 30 },
      { key: 'Social_Media_Engagement_Score', kind: 'float', min: 0, max: 100 },
    ],
  },
];
const FIELDS = GROUPS.flatMap((g) => g.fields);

// Hai khách thật trong tệp (CUS16791 → S1, CUS41124 → S4) để demo nhanh; trường trống sẽ được ước lượng
const PRESETS: { label: string; icon: string; values: Record<string, number | string | null> }[] = [
  {
    label: 'Khách VIP có dấu hiệu rời bỏ', icon: 'warning',
    values: { Age: 41, Gender: 'Female', Country: 'USA', City: 'Chicago', Signup_Quarter: 'Q2', Membership_Years: 0.3,
      Login_Frequency: 20, Session_Duration_Avg: 35.6, Pages_Per_Session: 12.5, Mobile_App_Usage: 23.9,
      Wishlist_Items: 8, Cart_Abandonment_Rate: 53.1, Total_Purchases: 17, Average_Order_Value: 133.03,
      Days_Since_Last_Purchase: null, Discount_Usage_Rate: 52.9, Returns_Rate: null, Payment_Method_Diversity: 1,
      Credit_Balance: 1348, Email_Open_Rate: 25.9, Customer_Service_Calls: 7, Product_Reviews_Written: 7,
      Social_Media_Engagement_Score: 54.2 },
  },
  {
    label: 'Khách trung thành', icon: 'verified',
    values: { Age: 51, Gender: 'Female', Country: 'UK', City: 'Leeds', Signup_Quarter: 'Q3', Membership_Years: 0.1,
      Login_Frequency: 21, Session_Duration_Avg: 35.5, Pages_Per_Session: 12.1, Mobile_App_Usage: 34.3,
      Wishlist_Items: 10, Cart_Abandonment_Rate: 26, Total_Purchases: 19, Average_Order_Value: 148.97,
      Days_Since_Last_Purchase: 1, Discount_Usage_Rate: 52.2, Returns_Rate: 6.8, Payment_Method_Diversity: 1,
      Credit_Balance: 4861, Email_Open_Rate: 44.5, Customer_Service_Calls: 1, Product_Reviews_Written: 4,
      Social_Media_Engagement_Score: 25.1 },
  },
];

function validators(f: Field): ValidatorFn[] {
  return [
    ...(f.required ? [Validators.required] : []),
    ...(f.min !== undefined ? [Validators.min(f.min)] : []),
    ...(f.max !== undefined ? [Validators.max(f.max)] : []),
    ...(f.kind === 'int' ? [Validators.pattern(/^-?\d+$/)] : []),
  ];
}

// FR-PRED-01 → 03: form 23 trường, chấm điểm, lưu khách mới; lỗi chặn tại ô và hiện lỗi 400 của backend
@Component({
  selector: 'app-predict',
  imports: [
    CurrencyPipe, LowerCasePipe, PercentPipe, ReactiveFormsModule, RouterLink,
    MatButtonModule, MatCardModule, MatFormFieldModule, MatIconModule, MatInputModule, MatProgressSpinnerModule,
    MatSelectModule, MatSnackBarModule, MatTooltipModule, JourneyTimeline, ReasonList,
  ],
  templateUrl: './predict.html',
  styleUrl: './predict.css',
})
export class Predict {
  private readonly http = inject(HttpClient);
  private readonly snackBar = inject(MatSnackBar);
  private readonly router = inject(Router);
  private readonly resultEl = viewChild<ElementRef<HTMLElement>>('resultPanel');

  protected readonly groups = GROUPS;
  protected readonly presets = PRESETS;
  protected readonly labels = FIELD_LABELS;
  protected readonly levels = LEVEL_LABELS;
  protected readonly segmentNames = SEGMENT_NAMES;
  protected readonly channels = CHANNELS;
  protected readonly requiredCount = FIELDS.filter((f) => f.required).length;

  protected readonly form = new FormGroup(
    Object.fromEntries(FIELDS.map((f) => [f.key, new FormControl<number | string | null>(null, validators(f))])),
  );

  private readonly country = toSignal(this.form.controls['Country'].valueChanges, { initialValue: null });
  protected readonly cities = computed(() => COUNTRY_CITIES[this.country() as string] ?? []);

  protected readonly result = signal<PredictResult | null>(null);
  protected readonly loading = signal(false);
  protected readonly saving = signal(false);
  protected readonly error = signal<string | null>(null);
  /** Form đổi sau lần chấm gần nhất → kết quả đang hiện là của dữ liệu cũ. */
  protected readonly stale = signal(false);

  protected readonly info = httpResource<ModelInfo>(() => `${environment.apiUrl}/model/info`);
  protected readonly tau = computed(() => (this.info.hasValue() ? this.info.value().thresholds.tau : null));

  constructor() {
    // Thành phố phụ thuộc quốc gia: khóa khi chưa chọn quốc gia, xóa khi không còn thuộc quốc gia mới
    const city = this.form.controls['City'];
    city.disable();
    this.form.controls['Country'].valueChanges.subscribe((country) => {
      const options = COUNTRY_CITIES[country as string];
      if (city.value && !options?.includes(city.value as string)) city.setValue(null);
      if (options) city.enable({ emitEvent: false });
      else city.disable({ emitEvent: false });
    });
    this.form.valueChanges.subscribe(() => {
      if (this.result() && !this.loading()) this.stale.set(true);
    });
  }

  protected errorText(key: string): string {
    const errors = this.form.controls[key].errors;
    if (!errors) return '';
    if (errors['server']) return errors['server'];
    if (errors['required']) return 'Bắt buộc';
    if (errors['pattern']) return 'Phải là số nguyên';
    const f = FIELDS.find((x) => x.key === key)!;
    if (key === 'Average_Order_Value' && errors['min']) return 'Phải lớn hơn 0';
    return `Từ ${f.min} đến ${f.max}`;
  }

  protected fill(values: Record<string, number | string | null>): void {
    this.form.reset(values);
  }

  protected clear(): void {
    this.form.reset();
    this.result.set(null);
    this.error.set(null);
  }

  protected submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      document.querySelector<HTMLElement>('.predict-form .mat-form-field-invalid input, .predict-form .mat-form-field-invalid mat-select')?.focus();
      return;
    }
    this.send(false);
  }

  protected save(): void {
    this.send(true);
  }

  private send(save: boolean): void {
    (save ? this.saving : this.loading).set(true);
    this.error.set(null);
    this.http
      .post<PredictResult>(`${environment.apiUrl}/predict`, this.form.getRawValue(), { params: save ? { save: 'true' } : {} })
      .subscribe({
        next: (r) => {
          this.result.set(r);
          this.stale.set(false);
          this.loading.set(false);
          this.saving.set(false);
          if (save) {
            this.snackBar
              .open(`Đã lưu khách ${r.customer_id} vào danh sách.`, 'Xem hồ sơ', { duration: 6000 })
              .onAction()
              .subscribe(() => this.router.navigate(['/customers', r.customer_id]));
          } else if (window.innerWidth < 1100) {
            setTimeout(() => this.resultEl()?.nativeElement.scrollIntoView({ behavior: 'smooth', block: 'start' }));
          }
        },
        error: (e: HttpErrorResponse) => {
          this.loading.set(false);
          this.saving.set(false);
          const errors: Record<string, string> | undefined = e.error?.errors;
          if (e.status === 400 && errors) {
            for (const [key, msg] of Object.entries(errors)) this.form.controls[key]?.setErrors({ server: msg });
            this.form.markAllAsTouched();
            this.error.set('Dữ liệu chưa hợp lệ, xem các ô báo đỏ.');
          } else {
            this.error.set('Không chấm điểm được. Kiểm tra backend đã chạy chưa.');
          }
        },
      });
  }
}
