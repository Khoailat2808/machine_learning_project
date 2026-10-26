import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { Predict } from './predict';

describe('Predict', () => {
  Element.prototype.scrollIntoView ??= () => {}; // jsdom không có

  function setup() {
    TestBed.configureTestingModule({ providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()] });
    const fixture = TestBed.createComponent(Predict);
    fixture.detectChanges();
    const component = fixture.componentInstance as any;
    return { fixture, component, form: component.form, http: TestBed.inject(HttpTestingController) };
  }

  it('khóa Thành phố tới khi chọn Quốc gia, đổi quốc gia thì xóa thành phố cũ', () => {
    const { form } = setup();
    expect(form.controls.City.disabled).toBe(true);
    form.controls.Country.setValue('UK');
    form.controls.City.setValue('London');
    expect(form.controls.City.enabled).toBe(true);
    form.controls.Country.setValue('USA');
    expect(form.controls.City.value).toBeNull();
  });

  it('chặn tại ô: Age = 200, thiếu trường bắt buộc, số lẻ ở trường số nguyên', () => {
    const { component, form } = setup();
    form.controls.Age.setValue(200);
    form.controls.Login_Frequency.setValue(2.5);
    expect(component.errorText('Age')).toBe('Từ 13 đến 100');
    expect(component.errorText('Gender')).toBe('Bắt buộc');
    expect(component.errorText('Login_Frequency')).toBe('Phải là số nguyên');
  });

  it('lỗi 400 của backend hiện tại đúng ô', () => {
    const { component, form, http } = setup();
    component.fill({ Gender: 'Male', Country: 'UK', City: 'London', Signup_Quarter: 'Q1', Membership_Years: 1,
      Login_Frequency: 3, Cart_Abandonment_Rate: 50, Total_Purchases: 5, Average_Order_Value: 80 });
    component.submit();
    http.expectOne((r) => r.url.endsWith('/predict'))
      .flush({ errors: { City: 'Thành phố không thuộc quốc gia đã chọn.' } }, { status: 400, statusText: 'Bad Request' });
    expect(component.errorText('City')).toBe('Thành phố không thuộc quốc gia đã chọn.');
    expect(form.controls.City.touched).toBe(true);
  });

  it('hiện kết quả: phân khúc, số trường ước lượng, nút lưu', () => {
    const { fixture, component, http } = setup();
    component.fill({ Gender: 'Male', Country: 'UK', City: 'London', Signup_Quarter: 'Q1', Membership_Years: 1,
      Login_Frequency: 3, Cart_Abandonment_Rate: 50, Total_Purchases: 5, Average_Order_Value: 80 });
    component.submit();
    http.expectOne((r) => r.url.endsWith('/predict')).flush({
      p_churn: 0.7, risk_label: 'High', clv_pred: 50, clv_potential: 200, clv_tier: 'Mid', value_at_risk: 140,
      segment: 'S2', channel: 'Email', model_version: 'churn_v1', saved: false, customer_id: null,
      journey: { journey_id: 'J2', name: 'Tiềm năng dễ mất', goal: 'Giữ lại', kpi: 'k', max_spend_pct: 0.05,
        steps: [{ day: 0, channel: 'Email', action: 'Nhắc giỏ', offer: 'Freeship' }] },
      top_reasons: [{ feature: 'Customer_Service_Calls', label: 'Số lần gọi CSKH', value: 9, avg: 5.7, shap: 0.2 }],
      imputed_fields: ['Age', 'Returns_Rate'],
    });
    fixture.detectChanges();
    const text: string = fixture.nativeElement.textContent;
    expect(text).toContain('S2 · Tiềm năng dễ mất');
    expect(text).toContain('2 trường được ước lượng');
    expect(text).toContain('Lưu vào danh sách');
    component.form.controls.Age.setValue(30);
    expect(component.stale()).toBe(true);
  });
});
