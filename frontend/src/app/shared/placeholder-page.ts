import { Component, input } from '@angular/core';

// Trang tạm cho từng route; team FE thay bằng component thật trong features/<tên>/
@Component({
  selector: 'app-placeholder-page',
  template: `<h1>{{ title() }}</h1><p>Đang xây dựng.</p>`,
})
export class PlaceholderPage {
  readonly title = input('');
}
