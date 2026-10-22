# 01 – BRD: Tài liệu yêu cầu nghiệp vụ

> Trạng thái: v2 · Cập nhật: 19/10/2026 · Chủ trì: Trần Anh Khoa
> v2 định hướng lại sản phẩm: từ "hệ thống quản lý mô hình churn" sang **công cụ ra quyết định cho bộ phận marketing**. Lý do ghi ở D-17, [09-decision-log.md](09-decision-log.md).

## 1. Bối cảnh và vấn đề

Một doanh nghiệp thương mại điện tử có 50.000 khách, trong đó 28,9% đã rời bỏ. Bộ phận marketing hiện gửi cùng một chiến dịch cho mọi khách, nên gặp ba vấn đề:

1. **Không biết ai sắp rời.** Khách có nguy cơ không được giữ chân kịp lúc.
2. **Không biết khách nào đáng giữ.** Ưu đãi bị chia đều, kể cả cho khách mang lại rất ít lợi nhuận.
3. **Không biết chi bao nhiêu là hợp lý.** Không ước tính được một chiến dịch giữ chân sẽ tốn bao nhiêu và đem lại bao nhiêu trước khi chạy.

## 2. Mục tiêu sản phẩm

Xây một **webapp nội bộ giúp marketing trả lời 3 câu hỏi trước mỗi chiến dịch giữ chân**:

| Câu hỏi của marketing | Hệ thống trả lời bằng | Kỹ thuật bên dưới |
| --- | --- | --- |
| **Giữ ai?** | Danh sách khách xếp theo giá trị đang bị đe dọa (Value at Risk) | Mô hình ML dự báo P(churn) + công thức CLV |
| **Làm gì với họ?** | 6 phân khúc, mỗi phân khúc có một lộ trình hành động dựa trên nghiên cứu, kèm 3 lý do rủi ro của từng khách | Ma trận Risk × CLV, SHAP |
| **Chi bao nhiêu, thu về gì?** | Mô phỏng chiến dịch: số khách nhắm tới, chi phí, giá trị kỳ vọng giữ lại được, ROI; xuất danh sách để gửi | Công thức kỳ vọng trên P(churn) và CLV |

Đầu ra cụ thể mà marketer mang đi dùng là **một file danh sách khách (CSV) đã có phân khúc, lộ trình, kênh và lý do**, đưa thẳng vào công cụ gửi email/SMS.

Chỉ số dùng chung để ưu tiên: **Value at Risk (VaR) = P(churn) × CLV tiềm năng**. Cách tính CLV xem [05-clv-methodology.md](05-clv-methodology.md).

## 3. Người dùng

| Vai trò | Họ cần gì từ hệ thống | Tần suất |
| --- | --- | --- |
| **Marketing Manager** | Biết giá trị đang bị đe dọa nằm ở đâu, nên dồn ngân sách vào phân khúc nào, và một chiến dịch có đáng chạy không (ROI) | Hằng tuần / trước mỗi đợt chiến dịch |
| **CRM Executive** | Lọc đúng tệp khách, hiểu vì sao từng khách bị gắn rủi ro, xuất danh sách đi gửi; chấm điểm nhanh cho khách mới | Hằng ngày |
| **Nhóm dữ liệu** (vận hành, không phải người dùng chính) | Train lại mô hình, cập nhật dữ liệu và tài khoản bằng script / Django Admin, **không qua giao diện marketing** | Khi có dữ liệu mới |

User stories chính:

- *Manager:* xem tổng VaR theo 6 phân khúc để biết dồn ngân sách vào đâu.
- *Manager:* nhập ngân sách và giả định tỷ lệ thành công, xem chiến dịch nên nhắm bao nhiêu khách và ROI kỳ vọng trước khi duyệt.
- *Manager:* biết yếu tố nào đẩy churn lên nhiều nhất trên toàn tệp để đề xuất sửa vấn đề gốc (CSKH, checkout).
- *CRM:* lọc khách theo phân khúc, quốc gia, mức rủi ro; xuất CSV có sẵn kênh gợi ý và lý do chính.
- *CRM:* mở hồ sơ một khách, thấy P(churn), CLV, 3 lý do và lộ trình đề xuất.
- *CRM:* nhập thông tin một khách mới và nhận ngay phân khúc + lộ trình.

## 4. Phạm vi

**Trong phạm vi**

| Mã | Yêu cầu nghiệp vụ |
| --- | --- |
| BRQ-01 | Cho thấy tổng quan sức khỏe tệp khách: tỷ lệ rủi ro, tổng CLV, tổng VaR, phân bố theo 6 phân khúc và quốc gia. |
| BRQ-02 | Xếp hạng và lọc khách theo mức giá trị bị đe dọa; mỗi khách có giải thích dễ hiểu vì sao bị gắn rủi ro. |
| BRQ-03 | Gợi ý lộ trình hành động cho từng phân khúc (kênh, bước, ưu đãi, KPI, mức chi tối đa). |
| BRQ-04 | Mô phỏng một chiến dịch giữ chân trước khi chạy: số khách, chi phí, giá trị kỳ vọng giữ lại, ROI. |
| BRQ-05 | Xuất danh sách khách mục tiêu để đưa vào công cụ gửi bên ngoài. |
| BRQ-06 | Chấm điểm khách mới (từng khách) và xếp ngay vào phân khúc. |
| BRQ-07 | Cho marketer biết mô hình đáng tin đến đâu (độ chính xác, giới hạn) bằng ngôn ngữ dễ hiểu. |

**Ngoài phạm vi**

| Không làm | Lý do |
| --- | --- |
| Retrain, upload dataset, quản lý version mô hình trên web | Là việc của nhóm dữ liệu, không phải marketing; làm bằng script (D-17) |
| Chỉnh ngưỡng churn / tier CLV / tham số CLV trên web | Ngưỡng cố định theo mô hình đã chốt, tránh mỗi người một số liệu (D-17) |
| Gửi email/SMS thật, tích hợp ESP | Hệ thống dừng ở bước xuất danh sách |
| Đo kết quả chiến dịch thật, A/B test | Không có khách thật và thời gian quan sát; ROI chỉ là mô phỏng theo giả định |
| Real-time streaming, retrain tự động | Dữ liệu là snapshot tĩnh |
| Deploy online | Chạy local, nộp repo (D-05) |

## 5. Ma trận phân khúc

Khách được xếp theo 2 trục độc lập: **rủi ro** (P(churn) ≥ τ → Cao) và **giá trị** (CLV tiềm năng chia 3 tier theo phân vị 33/67). τ = 0,186, chọn tối ưu F2 để ưu tiên không bỏ sót khách sắp rời (D-14).

| Phân khúc | Rủi ro | CLV | Mục tiêu marketing | Chi tối đa / khách |
| --- | --- | --- | --- | --- |
| S1 – VIP nguy cơ | Cao | High | Giữ lại bằng mọi kênh cá nhân | 10% CLV tiềm năng |
| S2 – Tiềm năng dễ mất | Cao | Mid | Giữ lại bằng nhắc giỏ, miễn phí vận chuyển | 5% |
| S3 – Giá trị thấp rủi ro | Cao | Low | Hỏi lý do, chi phí thấp | 2% |
| S4 – Khách trung thành | Thấp | High | Khuếch đại: giới thiệu, hạng thành viên | 3% |
| S5 – Ổn định cần nuôi | Thấp | Mid | Tăng giá trị đơn, đưa lên S4 | 3% |
| S6 – Phổ thông | Thấp | Low | Duy trì chi phí thấp | 1% |

Chạy thử với τ = 0,5: **S1 + S2 chiếm 15,1% số khách nhưng 67,7% tổng VaR**. Đây là luận điểm kinh doanh chính của sản phẩm. Lộ trình chi tiết và nguồn nghiên cứu: [06-marketing-journeys.md](06-marketing-journeys.md).

## 6. Chỉ số thành công

| Nhóm | Chỉ số | Ngưỡng đạt |
| --- | --- | --- |
| Giá trị cho marketing | Story của Manager và CRM (mục 3) chạy trọn trên giao diện | 6/6 |
| Giá trị cho marketing | Từ Dashboard đến file CSV danh sách S1 | ≤ 3 thao tác |
| Giá trị cho marketing | Mô phỏng chiến dịch S1 + S2 hiển thị số khách, chi phí, VaR giữ lại kỳ vọng, ROI | Có, khớp tính tay |
| Mô hình churn | ROC-AUC / Recall trên test | ≥ 0,90 / ≥ 0,80 (đã đạt: 0,918 / 0,858) |
| CLV | Spearman(CLV tiềm năng, Lifetime_Value lịch sử) | ≥ 0,5 (chạy thử 0,61) |
| Giải thích | Mỗi khách có top 3 lý do SHAP bằng tiếng Việt | 100% |
| Hệ thống | Chấm 1 khách mới / tải Dashboard | < 500 ms / < 2 giây |

## 7. Giả định và ràng buộc

- Dữ liệu là dataset tổng hợp đã được thầy duyệt (D-01); số liệu đẹp hơn thực tế, phải nêu hạn chế trong báo cáo.
- Nhãn `Churned` được giả định ứng với chu kỳ 1 năm (đang chờ thầy xác nhận).
- Tỷ lệ thành công của chiến dịch là **giả định do marketer nhập**, không phải số đo được; giao diện phải ghi rõ điều này.
- Hạn nộp 09/11/2026; 6 thành viên (BA & Model 2, BE 2, FE 2); Angular + Django + SQLite, chạy local.

## 8. Rủi ro

| Rủi ro | Giảm thiểu |
| --- | --- |
| Marketer hiểu ROI mô phỏng là kết quả chắc chắn | Hiển thị nhãn "ước tính theo giả định" và cho chỉnh giả định ngay trên màn hình |
| Dữ liệu tổng hợp cho metrics đẹp bất thường | Kiểm tra leakage, báo cáo độ lệch chuẩn CV, nêu rõ hạn chế |
| Nghẽn tích hợp FE–BE | API contract ([04-api-contract.md](04-api-contract.md)) + mock API trước |
| Thầy clone repo không chạy được | Test clone trên máy Windows mới theo README |

## 9. Câu hỏi mở

- [ ] (Thầy) Nhãn `Churned` đo trong chu kỳ bao lâu? — *ảnh hưởng công thức CLV*
- [ ] (Thầy) Horizon 3 năm, trừ hàng trả lại, biên lợi nhuận 33% có phù hợp không?
- [ ] (Nhóm) Tỷ lệ thành công mặc định cho mô phỏng chiến dịch: đang để 20%, cần nguồn tham chiếu. Màn hình luôn hiện kèm **tỷ lệ hòa vốn** nên kết luận không phụ thuộc hoàn toàn vào con số này.
- [x] Deploy online hay local? → Local.
- [x] Marketer có chỉnh ngưỡng không? → Không; ngưỡng cố định theo mô hình (D-17).
