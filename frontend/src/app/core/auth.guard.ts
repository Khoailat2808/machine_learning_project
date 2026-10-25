import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService } from './auth.service';

// Chưa đăng nhập → /login, nhớ trang đang mở để quay lại sau khi đăng nhập
export const authGuard: CanActivateFn = (_route, state) =>
  inject(AuthService).username() !== null ||
  inject(Router).createUrlTree(['/login'], { queryParams: { returnUrl: state.url } });
