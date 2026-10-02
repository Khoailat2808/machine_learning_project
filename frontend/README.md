# frontend — Angular

Phụ trách: **team FE** (Tiến, Thành). Spec: [docs/02-functional-requirements.md](../docs/02-functional-requirements.md), [docs/04-api-contract.md](../docs/04-api-contract.md), [docs/06-marketing-journeys.md](../docs/06-marketing-journeys.md).

## Cấu trúc dự kiến

```text
frontend/src/app/
├── core/          # AuthService, HttpInterceptor (gắn JWT, tự refresh), route guard theo vai trò
├── shared/        # component dùng chung: bảng, thẻ KPI, badge segment, empty state
└── features/
    ├── dashboard/ # FR-DASH: KPI, ma trận 2×3, biểu đồ
    ├── customers/ # FR-CUS: danh sách, bộ lọc, hồ sơ, export
    ├── predict/   # FR-PRED: form 23 trường, kết quả
    ├── journeys/  # FR-SEG: 6 lộ trình, ngưỡng (chỉ đọc với Marketer)
    └── models/    # FR-MDL: version, retrain, theo dõi job (chỉ Admin)
```

## Thư viện chính

Angular 17+ (standalone components), Angular Material, ng2-charts (Chart.js).

## Quy ước

- Gọi API qua service, base URL lấy từ `environment.ts` (`http://localhost:8000/api/v1`).
- Bộ lọc danh sách khách lưu trên URL query để copy link được.
- Validate form theo bảng 23 trường trong [02-functional-requirements.md](../docs/02-functional-requirements.md) mục 6; City lọc theo Country.
- Marketer: ẩn menu Models, ô ngưỡng hiển thị chỉ đọc (dựa vào `editable` trong `/models/active/thresholds`).
- Tuần 2–3 làm trên mock API của BE; tuần 4 chuyển sang API thật.
