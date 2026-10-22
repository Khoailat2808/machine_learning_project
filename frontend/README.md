# frontend — Angular

Phụ trách: **team FE** (Tiến, Thành). Spec: [docs/02-FRD.md](../docs/02-FRD.md), [docs/04-api-contract.md](../docs/04-api-contract.md), [docs/06-marketing-journeys.md](../docs/06-marketing-journeys.md).

## Cấu trúc dự kiến

```text
frontend/src/app/
├── core/          # AuthService, HttpInterceptor (gắn JWT, tự refresh), route guard đăng nhập
├── shared/        # component dùng chung: bảng, thẻ KPI, badge segment, empty state
└── features/
    ├── dashboard/ # FR-DASH: KPI, ma trận 2×3, biểu đồ, độ tin cậy mô hình
    ├── customers/ # FR-CUS: danh sách, bộ lọc, hồ sơ, export
    ├── predict/   # FR-PRED: form 23 trường, kết quả
    ├── journeys/  # FR-SEG: 6 lộ trình, ngưỡng chỉ đọc
    └── campaigns/ # FR-CAMP: thiết lập, xem trước ROI, xuất danh sách
```

## Thư viện chính

Angular 21 (standalone components), Angular Material, ng2-charts (Chart.js).

## Quy ước

- Gọi API qua service, base URL lấy từ `environment.ts` (`http://localhost:8000/api/v1`).
- Bộ lọc danh sách khách lưu trên URL query để copy link được.
- Validate form theo bảng 23 trường trong [02-FRD.md](../docs/02-FRD.md) mục 9; City lọc theo Country.
- ROI và VaR giữ lại luôn kèm nhãn "ước tính theo giả định".
- Tuần 2–3 làm trên mock API của BE; tuần 4 chuyển sang API thật.
