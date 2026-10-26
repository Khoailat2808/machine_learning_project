import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { Journeys } from './journeys';

describe('Journeys', () => {
  it('hiện ngưỡng chỉ đọc và thẻ lộ trình', async () => {
    TestBed.configureTestingModule({ providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()] });
    const fixture = TestBed.createComponent(Journeys);
    fixture.detectChanges();
    TestBed.inject(HttpTestingController).expectOne((r) => r.url.endsWith('/journeys')).flush({
      thresholds: { tau: 0.1857, clv_p33: 141.83, clv_p67: 333.53 },
      journeys: [{ journey_id: 'J1', segment: 'S1', name: 'VIP nguy cơ', risk: 'High', tier: 'High', count: 5330,
        value_at_risk: 3106866.77, goal: 'Giữ lại', kpi: 'Mua lại 30 ngày', max_spend_pct: 0.1,
        research: ['Lemmens & Gupta 2020'], steps: [{ day: 0, channel: 'Phone', action: 'Gọi', offer: null }] }],
    });
    await fixture.whenStable();
    fixture.detectChanges();
    const text: string = fixture.nativeElement.textContent;
    expect(text).toMatch(/τ = 18[.,]6%/); // test không nạp locale vi
    expect(text).toContain('VIP nguy cơ');
    expect(text).toContain('100% tổng VaR');
    expect(text).toContain('Lemmens & Gupta 2020');
  });
});
