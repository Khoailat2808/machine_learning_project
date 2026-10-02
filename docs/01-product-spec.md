# 01 – Product spec

> Trạng thái: v1 · Cập nhật: 02/10/2026 · Chủ trì: Trần Anh Khoa

## 1. Bài toán

28,9% khách hàng trong dữ liệu đã rời bỏ, nhưng doanh nghiệp đang gửi cùng một chiến dịch cho mọi người: khách sắp rời không được giữ chân kịp, còn ngân sách ưu đãi bị rải đều cho cả khách giá trị thấp. Đội marketing cần biết **ai sắp rời**, **họ đáng giá bao nhiêu** và **nên làm gì với từng nhóm**, ngay trong một công cụ nội bộ.

**Ý tưởng cốt lõi.** Một mô hình học máy dự báo xác suất churn. CLV được tính bằng công thức chiết khấu lợi nhuận ròng trong 3 năm, với hệ số giữ chân lấy từ xác suất churn của mô hình ([05-clv-methodology.md](05-clv-methodology.md)). Khách được xếp vào ma trận 2 × 3 (Risk cao/thấp × CLV tiềm năng High/Mid/Low) = 6 phân khúc, mỗi phân khúc gắn một lộ trình marketing có cơ sở nghiên cứu. Chỉ số ưu tiên chung là **Value at Risk (VaR) = P(churn) × CLV tiềm năng**.

## 2. Mục tiêu

1. Mô hình churn đạt **ROC-AUC ≥ 0,90** và **Recall ≥ 0,80** trên tập test (baseline chưa tinh chỉnh: AUC 0,918).
2. CLV được tính cho 100% khách theo công thức chiết khấu lợi nhuận ròng 3 năm; tham số biên lợi nhuận và lãi suất chiết khấu chỉnh được; xếp hạng CLV tiềm năng tương quan **Spearman ≥ 0,5** với giá trị chi tiêu lịch sử (chạy thử: khoảng 0,61).
3. Marketer xem được danh sách khách xếp theo VaR và lộ trình đề xuất cho từng người trong **≤ 3 thao tác**.
4. Chấm điểm một khách mới qua API **< 500 ms**; chấm lại toàn bộ 50.000 khách **< 2 phút**.
5. Mọi dự đoán có giải thích (**top 3 yếu tố SHAP**) để marketer hiểu vì sao khách bị gắn rủi ro.

## 3. Ngoài phạm vi (non-goals)

| Không làm | Lý do |
| --- | --- |
| Gửi email/SMS thật | Hệ thống chỉ đề xuất lộ trình và xuất danh sách; tích hợp ESP (Mailchimp, Zalo OA) để giai đoạn sau |
| Retrain tự động theo lịch | Retrain kích hoạt thủ công từ trang Admin; MLOps đầy đủ vượt quá 6 tuần |
| Real-time streaming | Dữ liệu là bảng snapshot tĩnh, batch scoring là đủ |
| Dùng BG/NBD/Pareto-NBD làm CLV chính thức | BG/NBD chạy được nhưng khớp kém với nhãn churn (AUC 0,61); chỉ dùng kiểm định chéo |
| A/B test thật | Không có khách thật, kênh gửi và thời gian quan sát; uplift chỉ mô phỏng bằng giả định |
| Deploy online | Đã chốt chạy local, nộp repo cho thầy |

## 4. Persona và user stories

**Marketing Manager** (quyết định ngân sách)

- Xem tổng quan số khách theo 6 phân khúc và tổng VaR, để biết dồn ngân sách giữ chân vào đâu.
- Biết yếu tố nào đẩy churn lên nhiều nhất trên toàn tệp, để đề xuất sửa vấn đề gốc (CSKH, checkout).

**CRM Executive** (triển khai chiến dịch)

- Lọc danh sách theo phân khúc, quốc gia, mức rủi ro và xuất CSV để đưa vào công cụ gửi email.
- Mở hồ sơ một khách và thấy P(churn), CLV, 3 lý do chính, lộ trình đề xuất.
- Nhập thông tin khách mới (form hoặc CSV) và nhận điểm ngay.

**Admin / Data Analyst** (quản lý mô hình)

- Upload dataset mới và kích hoạt retrain.
- So sánh metrics các version và chọn version đang chạy, để rollback khi bản mới kém hơn.
- Là vai trò **duy nhất** được chỉnh ngưỡng churn, ngưỡng tier CLV và tham số CLV.
- Edge case: file upload sai schema bị từ chối, báo rõ cột thiếu/sai kiểu, không ghi đè dữ liệu cũ.

## 5. Ma trận phân khúc

Ngưỡng churn τ mặc định = ngưỡng tối ưu F2 trên validation (ưu tiên recall). CLV chia tier theo phân vị 33/67 của **CLV tiềm năng** để trục giá trị không trùng với trục rủi ro. Chỉ Admin chỉnh được các ngưỡng.

| Phân khúc | Churn risk | CLV tier | Lộ trình đề xuất (tóm tắt) | Kênh |
| --- | --- | --- | --- | --- |
| S1 – VIP nguy cơ | Cao | High | CSKH liên hệ cá nhân trong 48h, xử lý khiếu nại, quyền lợi phi giá, voucher có hạn sau cùng | Phone, email cá nhân |
| S2 – Tiềm năng dễ mất | Cao | Mid | Nhắc giỏ hàng bỏ dở, miễn phí vận chuyển, voucher 10% có hạn nếu vẫn chưa mua | Email hoặc push theo Email_Open_Rate |
| S3 – Giá trị thấp rủi ro | Cao | Low | Khảo sát lý do rời bỏ, ưu đãi rẻ có điều kiện, không voucher lớn | Email tự động |
| S4 – Khách trung thành | Thấp | High | Hạng Gold, mua sớm, giới thiệu bạn bè, mời đánh giá; không giảm giá | Email, app |
| S5 – Ổn định cần nuôi | Thấp | Mid | Hạng Silver, cross-sell theo wishlist có sàng lọc, bundle tăng AOV | Email, social |
| S6 – Phổ thông | Thấp | Low | Newsletter định kỳ, kích hoạt dùng app | Newsletter, SMS |

Chạy thử với τ = 0,5: S1 3.837, S2 3.697, S3 4.814, S4 12.663, S5 13.303, S6 11.686 khách. **S1 + S2 chiếm 15,1% số khách nhưng 67,7% tổng VaR.** Chi tiết và nguồn nghiên cứu: [06-marketing-journeys.md](06-marketing-journeys.md).

## 6. Chỉ số thành công

| Loại | Chỉ số | Ngưỡng đạt | Stretch |
| --- | --- | --- | --- |
| Model churn | ROC-AUC trên test | ≥ 0,90 | ≥ 0,93 |
| Model churn | Recall tại ngưỡng F2 | ≥ 0,80 | ≥ 0,85 |
| CLV | Spearman(CLV tiềm năng, Lifetime_Value lịch sử) | ≥ 0,5 | ≥ 0,6 |
| CLV | Tỷ lệ khách đổi tier khi d chạy 8% → 12% | Báo cáo được | ≤ 10% |
| Hệ thống | Latency `/predict` p95 | < 500 ms | < 200 ms |
| Hệ thống | Batch score 50.000 khách | < 2 phút | < 30 giây |
| Sản phẩm | Story CRM Executive chạy trọn vẹn | 5/5 | — |
| Kinh doanh (mô phỏng) | VaR nhắm tới bởi S1 + S2 | Hiển thị trên dashboard | — |

## 7. Rủi ro

| Rủi ro | Giảm thiểu |
| --- | --- |
| Dữ liệu tổng hợp cho metrics đẹp bất thường | Nêu rõ hạn chế, kiểm tra leakage, báo cáo thêm độ lệch chuẩn CV |
| Nghẽn tích hợp FE–BE ở tuần 4 | Chốt API contract 09/10; BE dựng mock API ngay tuần 2 |
| SQLite chỉ cho 1 tiến trình ghi | Bật WAL, chỉ Job runner ghi hàng loạt, mỗi lần 1 job; cần thì đổi sang PostgreSQL bằng `DATABASES` |
| Thầy clone repo không chạy được | Test clone trên máy Windows mới ở tuần 5 theo README |

## 8. Câu hỏi mở

- [ ] (Thầy) Nhãn `Churned` đo trong chu kỳ bao lâu? Công thức CLV đang giả định 1 năm. — *chặn tuần 3*
- [ ] (Thầy) Các lựa chọn horizon 3 năm, trừ hàng trả lại, biên lợi nhuận 33% có phù hợp không? — *đã gửi mail*
- [x] Deploy online hay local? → Local, nộp repo.
- [x] Marketer có được chỉnh ngưỡng? → Không, chỉ Admin.
- [x] Database? → SQLite.
