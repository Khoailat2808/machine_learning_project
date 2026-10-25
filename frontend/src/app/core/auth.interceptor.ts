import { HttpErrorResponse, HttpInterceptorFn, HttpRequest } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, switchMap, throwError } from 'rxjs';

import { AuthService } from './auth.service';

const withToken = (req: HttpRequest<unknown>, token: string | null) =>
  token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;

// Gắn Bearer; gặp 401 thì refresh một lần rồi gửi lại, refresh hỏng thì đăng xuất (FR-AUTH-02).
// ponytail: các request 401 cùng lúc mỗi cái tự refresh; gộp bằng shareReplay nếu thấy refresh dồn dập.
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  if (req.url.includes('/auth/')) return next(req);
  const auth = inject(AuthService);

  return next(withToken(req, auth.access)).pipe(
    catchError((err) => {
      if (!(err instanceof HttpErrorResponse) || err.status !== 401 || !auth.access) return throwError(() => err);
      return auth.refresh().pipe(
        catchError((refreshErr) => {
          auth.logout();
          return throwError(() => refreshErr);
        }),
        switchMap((token) => next(withToken(req, token))),
      );
    }),
  );
};
