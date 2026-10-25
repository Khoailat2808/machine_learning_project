import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';

/** Tải file cần token (không dùng được <a href>): nhận blob, lấy tên từ Content-Disposition rồi lưu. */
export function downloadFile(http: HttpClient, url: string, params: HttpParams | Record<string, string>): Observable<void> {
  return http.get(url, { params, responseType: 'blob', observe: 'response' }).pipe(
    map((res) => {
      const name = /filename="?([^"]+)"?/.exec(res.headers.get('Content-Disposition') ?? '')?.[1] ?? 'export.csv';
      const link = document.createElement('a');
      link.href = URL.createObjectURL(res.body!);
      link.download = name;
      link.click();
      URL.revokeObjectURL(link.href);
    }),
  );
}
