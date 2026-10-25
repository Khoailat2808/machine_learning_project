import { Injectable } from '@angular/core';
import { MatPaginatorIntl } from '@angular/material/paginator';

// NFR-02: nhãn phân trang tiếng Việt
@Injectable()
export class ViPaginatorIntl extends MatPaginatorIntl {
  override itemsPerPageLabel = 'Số dòng mỗi trang';
  override nextPageLabel = 'Trang sau';
  override previousPageLabel = 'Trang trước';
  override firstPageLabel = 'Trang đầu';
  override lastPageLabel = 'Trang cuối';
  override getRangeLabel = (page: number, pageSize: number, length: number) => {
    if (length === 0) return '0 / 0';
    const start = page * pageSize + 1;
    return `${start.toLocaleString('vi-VN')}–${Math.min(start + pageSize - 1, length).toLocaleString('vi-VN')} / ${length.toLocaleString('vi-VN')}`;
  };
}
