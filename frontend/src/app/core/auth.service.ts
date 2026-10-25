import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, map } from 'rxjs';

import { environment } from '../../environments/environment';

const ACCESS = 'access';
const REFRESH = 'refresh';
const USERNAME = 'username';

interface LoginResponse {
  access: string;
  refresh: string;
  user: { username: string };
}

// FR-AUTH-01, 02: JWT lưu localStorage; access 30 phút, refresh 1 ngày (BE quyết định)
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  readonly username = signal(localStorage.getItem(USERNAME));

  get access(): string | null {
    return localStorage.getItem(ACCESS);
  }

  login(username: string, password: string): Observable<void> {
    return this.http.post<LoginResponse>(`${environment.apiUrl}/auth/login`, { username, password }).pipe(
      map((res) => {
        localStorage.setItem(ACCESS, res.access);
        localStorage.setItem(REFRESH, res.refresh);
        localStorage.setItem(USERNAME, res.user.username);
        this.username.set(res.user.username);
      }),
    );
  }

  refresh(): Observable<string> {
    return this.http
      .post<{ access: string }>(`${environment.apiUrl}/auth/refresh`, { refresh: localStorage.getItem(REFRESH) })
      .pipe(
        map((res) => {
          localStorage.setItem(ACCESS, res.access);
          return res.access;
        }),
      );
  }

  logout(): void {
    [ACCESS, REFRESH, USERNAME].forEach((key) => localStorage.removeItem(key));
    this.username.set(null);
    this.router.navigate(['/login']);
  }
}
