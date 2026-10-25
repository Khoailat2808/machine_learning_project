import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, input, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { Router } from '@angular/router';

import { AuthService } from '../../core/auth.service';

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule, MatButtonModule, MatCardModule, MatFormFieldModule, MatInputModule, MatProgressBarModule],
  template: `
    <mat-card appearance="outlined">
      @if (loading()) {
        <mat-progress-bar mode="indeterminate" />
      }
      <mat-card-header>
        <mat-card-title>CLV &amp; Churn</mat-card-title>
        <mat-card-subtitle>Đăng nhập để tiếp tục</mat-card-subtitle>
      </mat-card-header>
      <form [formGroup]="form" (ngSubmit)="submit()">
        <mat-card-content>
          <mat-form-field appearance="outline">
            <mat-label>Tên đăng nhập</mat-label>
            <input matInput formControlName="username" autocomplete="username" />
            <mat-error>Nhập tên đăng nhập</mat-error>
          </mat-form-field>
          <mat-form-field appearance="outline">
            <mat-label>Mật khẩu</mat-label>
            <input matInput type="password" formControlName="password" autocomplete="current-password" />
            <mat-error>Nhập mật khẩu</mat-error>
          </mat-form-field>
          @if (error()) {
            <p class="error" role="alert">{{ error() }}</p>
          }
        </mat-card-content>
        <mat-card-actions>
          <button mat-flat-button type="submit" [disabled]="loading()">Đăng nhập</button>
        </mat-card-actions>
      </form>
    </mat-card>
  `,
  styles: `
    :host {
      display: grid;
      place-items: center;
      min-height: 100%;
      padding: 16px;
      box-sizing: border-box;
    }
    mat-card {
      width: 100%;
      max-width: 380px;
      overflow: hidden;
    }
    mat-card-content {
      display: flex;
      flex-direction: column;
      padding-top: 16px;
    }
    mat-card-actions {
      padding: 0 16px 16px;
    }
    button {
      width: 100%;
    }
    .error {
      color: var(--mat-sys-error);
      margin: 0 0 8px;
    }
  `,
})
export class Login {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly returnUrl = input<string>(); // query ?returnUrl= do authGuard gắn
  protected readonly loading = signal(false);
  protected readonly error = signal('');
  protected readonly form = inject(NonNullableFormBuilder).group({
    username: ['', Validators.required],
    password: ['', Validators.required],
  });

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const { username, password } = this.form.getRawValue();
    this.loading.set(true);
    this.error.set('');
    this.auth.login(username, password).subscribe({
      next: () => this.router.navigateByUrl(this.returnUrl() || '/dashboard'),
      error: (err: HttpErrorResponse) => {
        this.loading.set(false);
        // FR-AUTH-01: một thông báo chung, không nói sai username hay mật khẩu
        this.error.set(
          err.status === 401
            ? 'Tên đăng nhập hoặc mật khẩu không đúng.'
            : 'Không kết nối được máy chủ. Kiểm tra backend đã chạy chưa.',
        );
      },
    });
  }
}
