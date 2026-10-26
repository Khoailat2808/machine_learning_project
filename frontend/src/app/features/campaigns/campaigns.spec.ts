import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { Campaigns } from './campaigns';

const PREVIEW = {
  eligible: 10, selected: 4, total_cost: 100, total_value_at_risk: 1000, expected_saved: 200, roi: 1,
  break_even_rate: 0.1, is_estimate: true,
  by_segment: [{ segment: 'S1', selected: 4, cost: 100, value_at_risk: 1000 }],
};

describe('Campaigns', () => {
  const debounce = () => new Promise((r) => setTimeout(r, 350));

  async function setup(segment?: string) {
    TestBed.configureTestingModule({ providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()] });
    const fixture = TestBed.createComponent(Campaigns);
    if (segment) fixture.componentRef.setInput('segment', segment);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    http.expectOne((r) => r.url.endsWith('/journeys')).flush({ thresholds: {}, journeys: [] });
    await debounce();
    fixture.detectChanges();
    return { fixture, component: fixture.componentInstance as any, http };
  }

  it('mặc định S1 + S2, k theo phân khúc, s = 20%', async () => {
    const { http } = await setup();
    const req = http.expectOne((r) => r.url.endsWith('/campaigns/preview'));
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ segments: ['S1', 'S2'], country: null, city: null, budget: null,
      spend_pct: null, success_rate: 0.2 });
  });

  it('link ?segment=S1 chọn sẵn S1; ngân sách sai thì không gọi API', async () => {
    const { fixture, component, http } = await setup('S1');
    expect(http.expectOne((r) => r.url.endsWith('/preview')).request.body.segments).toEqual(['S1']);
    component.setBudget('-5');
    fixture.detectChanges();
    await debounce();
    http.expectNone((r) => r.url.endsWith('/preview'));
    expect(component.dim()).toBe(true);
  });

  it('hiện ROI kèm nhãn ước tính và nút xuất đúng số khách', async () => {
    const { fixture, http } = await setup();
    http.expectOne((r) => r.url.endsWith('/preview')).flush(PREVIEW);
    await fixture.whenStable();
    fixture.detectChanges();
    const text: string = fixture.nativeElement.textContent;
    expect(text).toContain('Ước tính theo giả định');
    expect(text).toMatch(/\+100\s?%/);
    expect(text).toContain('Xuất danh sách 4 khách');
  });

  it('không khách nào khớp → trạng thái trống, không chia cho 0', async () => {
    const { fixture, http } = await setup();
    http.expectOne((r) => r.url.endsWith('/preview'))
      .flush({ ...PREVIEW, eligible: 0, selected: 0, total_cost: 0, roi: null, break_even_rate: null, by_segment: [] });
    await fixture.whenStable();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Không có khách nào khớp bộ lọc');
  });
});
