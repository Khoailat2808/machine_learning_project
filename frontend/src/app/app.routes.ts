import { Routes } from '@angular/router';

import { authGuard } from './core/auth.guard';

export const NAV_ITEMS = [
  { path: 'dashboard', title: 'Tổng quan', icon: 'dashboard' },
  { path: 'customers', title: 'Khách hàng', icon: 'groups' },
  { path: 'journeys', title: 'Lộ trình', icon: 'alt_route' },
  { path: 'campaigns', title: 'Chiến dịch', icon: 'campaign' },
  { path: 'predict', title: 'Chấm điểm', icon: 'calculate' },
];

export const routes: Routes = [
  { path: 'login', title: 'Đăng nhập', loadComponent: () => import('./features/login/login').then((m) => m.Login) },
  {
    path: '',
    canActivateChild: [authGuard],
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
      { path: 'dashboard', title: 'Tổng quan', loadComponent: () => import('./features/dashboard/dashboard').then((m) => m.Dashboard) },
      { path: 'customers', title: 'Khách hàng', loadComponent: () => import('./features/customers/customer-list').then((m) => m.CustomerList) },
      { path: 'customers/:id', title: 'Hồ sơ khách', loadComponent: () => import('./features/customers/customer-detail').then((m) => m.CustomerDetail) },
      { path: 'journeys', title: 'Lộ trình', loadComponent: () => import('./features/journeys/journeys').then((m) => m.Journeys) },
      { path: 'predict', title: 'Chấm điểm', loadComponent: () => import('./features/predict/predict').then((m) => m.Predict) },
      { path: 'campaigns', title: 'Chiến dịch', loadComponent: () => import('./features/campaigns/campaigns').then((m) => m.Campaigns) },
    ],
  },
  { path: '**', redirectTo: 'dashboard' },
];
