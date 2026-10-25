import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Router, provideRouter } from '@angular/router';

import { environment } from '../../environments/environment';
import { authInterceptor } from './auth.interceptor';
import { AuthService } from './auth.service';
import { authGuard } from './auth.guard';

const REFRESH_URL = `${environment.apiUrl}/auth/refresh`;

describe('auth', () => {
  let http: HttpClient;
  let backend: HttpTestingController;

  beforeEach(() => {
    localStorage.setItem('access', 'old');
    localStorage.setItem('refresh', 'r');
    localStorage.setItem('username', 'marketer');
    TestBed.configureTestingModule({
      providers: [provideRouter([{ path: 'login', children: [] }]),provideHttpClient(withInterceptors([authInterceptor])), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpClient);
    backend = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    backend.verify();
    localStorage.clear();
  });

  it('gắn Bearer, gặp 401 thì refresh rồi gửi lại với token mới', () => {
    let body: unknown;
    http.get('/x').subscribe((res) => (body = res));

    const first = backend.expectOne('/x');
    expect(first.request.headers.get('Authorization')).toBe('Bearer old');
    first.flush(null, { status: 401, statusText: 'Unauthorized' });

    const refresh = backend.expectOne(REFRESH_URL);
    expect(refresh.request.body).toEqual({ refresh: 'r' });
    refresh.flush({ access: 'new' });

    const retry = backend.expectOne('/x');
    expect(retry.request.headers.get('Authorization')).toBe('Bearer new');
    retry.flush({ ok: true });

    expect(body).toEqual({ ok: true });
    expect(localStorage.getItem('access')).toBe('new');
  });

  it('refresh hỏng thì đăng xuất', () => {
    http.get('/x').subscribe({ error: () => undefined });
    backend.expectOne('/x').flush(null, { status: 401, statusText: 'Unauthorized' });
    backend.expectOne(REFRESH_URL).flush(null, { status: 401, statusText: 'Unauthorized' });

    expect(TestBed.inject(AuthService).username()).toBeNull();
    expect(localStorage.getItem('access')).toBeNull();
  });

  it('guard chuyển về /login kèm returnUrl khi chưa đăng nhập', () => {
    TestBed.inject(AuthService).username.set(null);
    const result = TestBed.runInInjectionContext(() => authGuard(null!, { url: '/customers?segment=S1' } as never));
    expect(TestBed.inject(Router).serializeUrl(result as never)).toBe('/login?returnUrl=%2Fcustomers%3Fsegment%3DS1');
  });
});
