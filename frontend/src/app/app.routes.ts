import { Routes } from '@angular/router';

import { PlaceholderPage } from './shared/placeholder-page';

export const NAV_ITEMS = [
  { path: 'dashboard', title: 'Tổng quan', icon: 'dashboard' },
  { path: 'customers', title: 'Khách hàng', icon: 'groups' },
  { path: 'predict', title: 'Chấm điểm', icon: 'calculate' },
  { path: 'journeys', title: 'Lộ trình', icon: 'alt_route' },
  { path: 'models', title: 'Mô hình', icon: 'model_training' }, // chỉ Admin — guard thêm ở FR-AUTH
];

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
  ...NAV_ITEMS.map(({ path, title }) => ({ path, title, component: PlaceholderPage, data: { title } })),
  { path: '**', redirectTo: 'dashboard' },
];
