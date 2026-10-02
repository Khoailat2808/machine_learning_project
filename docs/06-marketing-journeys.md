# 06 – Lộ trình marketing theo phân khúc

> Mỗi lộ trình dựa trên hai nguồn: tín hiệu từ dữ liệu của nhóm và nghiên cứu trên tạp chí marketing hàng đầu (JM, JMR, Marketing Science, JCR, HBR). S1 và S2 chiếm 15% số khách nhưng giữ 68% tổng Value at Risk, nên ngân sách và nhân lực dồn vào hai lộ trình này.

## 1. Ba nguyên tắc chung

**Nhắm theo giá trị, không chỉ theo rủi ro.** [Ascarza (2018)](https://www.hbs.edu/faculty/Pages/item.aspx?num=54936) chỉ ra khách rủi ro cao nhất chưa chắc là mục tiêu tốt nhất cho chương trình giữ chân; điều quyết định là khách có phản hồi với can thiệp hay không. [Lemmens & Gupta (2020)](https://www.rsm.nl/discovery/2020/managing-churn/) xếp khách theo lợi nhuận kỳ vọng của việc giữ chân thay vì rủi ro, với cùng ngân sách ước tính tăng ít nhất 4% lợi nhuận sau một chiến dịch. Vì vậy hệ thống xếp hàng bằng VaR và chia chi phí theo tier giá trị. Khi triển khai thật, mỗi lộ trình nên giữ ngẫu nhiên ~10% khách không liên hệ để đo uplift (P2).

**Ưu đãi phi giá trước, giảm giá sâu sau cùng.** [Anderson & Simester (2004)](https://www.scholars.northwestern.edu/en/publications/long-run-effects-of-promotion-depth-on-new-versus-established-cus/) cho thấy giảm giá sâu làm khách quen mua ít hơn về sau. [Thomas, Blattberg & Fox (2004)](https://journals.sagepub.com/doi/10.1509/jmkr.41.1.31.25086): dùng giá thấp để kéo khách quay lại rồi trở về giá bình thường. Voucher luôn có thời hạn và đứng sau quyền lợi như miễn phí vận chuyển, hỗ trợ ưu tiên.

**Không phải khách trung thành nào cũng đáng đầu tư.** [Reinartz & Kumar (2002)](https://www.thecasecentre.org/products/view?id=40943), phân tích 16.000 khách của 4 công ty: khách trung thành chưa chắc có lãi, khách có lãi chưa chắc trung thành. S4 ≈ “true friends”, S1–S2 gần “butterflies”, S6 ≈ “barnacles”, S3 ≈ “strangers”.

## 2. Tổng quan

Số khách từ lần chạy thử với τ = 0,5; sẽ đổi sau khi tune model. Mức chi tối đa là đề xuất của nhóm, tính theo % CLV tiềm năng của từng khách.

| Phân khúc | Số khách | Mục tiêu | Chiến thuật chính | Chi tối đa / khách | KPI chính | Nghiên cứu nền |
| --- | --- | --- | --- | --- | --- | --- |
| S1 – VIP nguy cơ | 3.837 | Giữ lại | Liên hệ cá nhân trong 48h, xử lý khiếu nại, quyền lợi phi giá, voucher có hạn sau cùng | 10% | Mua lại 30 ngày, VaR giữ được | Lemmens & Gupta 2020; Knox & van Oest 2014; Thomas et al. 2004 |
| S2 – Tiềm năng dễ mất | 3.697 | Giữ lại | Nhắc giỏ hàng, miễn phí vận chuyển, đổi kênh nếu ít mở email | 5% | Khôi phục giỏ, mua lại 30 ngày | Baymard 2025; Anderson & Simester 2004 |
| S3 – Giá trị thấp rủi ro | 4.814 | Tìm lý do, chi phí thấp | Khảo sát lý do rời bỏ, ưu đãi rẻ có điều kiện, tự động hoàn toàn | 2% | Tỷ lệ trả lời, chi phí/khách giữ được | Reinartz & Kumar 2002; Kumar et al. 2015 |
| S4 – Khách trung thành | 12.663 | Khuếch đại | Hạng Gold, giới thiệu bạn bè, mời đánh giá; không giảm giá | 3% | Khách mới từ giới thiệu, retention 12 tháng | Drèze & Nunes 2009; Schmitt et al. 2011 |
| S5 – Ổn định cần nuôi | 13.303 | Tăng giá trị | Cross-sell theo wishlist có sàng lọc, bundle, hạng Silver | 3% | AOV, tỷ lệ lên S4 | Shah et al. 2012; Drèze & Nunes 2009 |
| S6 – Phổ thông | 11.686 | Chi phí thấp | Newsletter, kích hoạt dùng app | 1% | Chi phí/khách, tỷ lệ lên S5 | Reinartz & Kumar 2002 |

**Cá nhân hóa trong phân khúc.** Lý do số 1 trong `top_reasons` chọn nhánh: gọi CSKH nhiều → nhánh xử lý khiếu nại; bỏ giỏ cao → nhánh nhắc giỏ; mở email thấp → chuyển sang push app. Ba biến này cũng là 3 tín hiệu churn mạnh nhất: khách đã rời gọi CSKH trung bình 6,9 lần (so với 5,2), bỏ giỏ 64% (so với 54%), mở email 15,9% (so với 22,9%).

## 3. Chi tiết từng lộ trình

### S1 – VIP nguy cơ (Risk cao × CLV High)

Giá trị lớn và đang có nguy cơ, nên mỗi khách giữ được bù được chi phí liên hệ cá nhân (Lemmens & Gupta). [Reichheld & Sasser (1990)](https://www.bain.com/insights/zero-defections-quality-comes-to-services-harvard-business-review-hbr/): giảm tỷ lệ rời bỏ vài điểm phần trăm có thể làm lợi nhuận tăng mạnh. [Knox & van Oest (2014)](https://research.tilburguniversity.edu/en/publications/customer-complaints-and-recovery-effectiveness-a-customer-base-ap), 20.000 khách của một nhà bán lẻ online/catalog: khiếu nại làm tăng rõ khả năng rời bỏ, khắc phục giảm được tác động nhưng hầu như không xóa hết → phải xử lý sớm.

| Ngày | Kênh | Hành động |
| --- | --- | --- |
| 0–2 | Điện thoại / email cá nhân | CSKH liên hệ, xử lý vấn đề tồn đọng (ưu tiên khách có lý do số 1 là gọi CSKH nhiều) |
| 2 | Email | Quyền lợi phi giá: miễn phí vận chuyển 3 tháng, hỗ trợ ưu tiên |
| 7 | Email / push | Nếu chưa mua lại: voucher 10–15%, hạn 14 ngày, hết hạn về giá thường |
| 30 | Email | Khảo sát hài lòng 1 câu |

KPI: mua lại trong 30 ngày, VaR giữ được, số khiếu nại được đóng.

### S2 – Tiềm năng dễ mất (Risk cao × CLV Mid)

Tỷ lệ bỏ giỏ là tín hiệu churn mạnh thứ hai. [Baymard Institute (9/2025)](https://baymard.com/lists/cart-abandonment-rate), tổng hợp 50 nghiên cứu: tỷ lệ bỏ giỏ trung bình 70,22%; lý do hàng đầu là chi phí phát sinh (40%), giao chậm (20%), bắt tạo tài khoản (18%). Đánh vào chi phí vận chuyển trước khi giảm giá.

| Ngày | Kênh | Hành động |
| --- | --- | --- |
| 0 | Email hoặc push (theo Email_Open_Rate) | Nhắc giỏ hàng, hiển thị sẵn tổng chi phí |
| 2 | Email / push | Miễn phí vận chuyển cho giỏ đó, link thanh toán không cần đăng nhập lại |
| 5 | Email | Gợi ý sản phẩm thay thế từ wishlist |
| 10 | Email | Voucher 10%, hạn 7 ngày, chỉ khi vẫn chưa mua |

KPI: tỷ lệ khôi phục giỏ, mua lại 30 ngày, tỷ lệ dùng voucher (càng thấp càng tốt).

### S3 – Giá trị thấp rủi ro (Risk cao × CLV Low)

Nhóm “strangers”: không nên đổ tiền giữ bằng mọi giá. [Kumar, Bhagwat & Zhang (2015)](https://journals.sagepub.com/doi/abs/10.1509/jm.14.0107): lý do rời đi dự báo được cả khả năng quay lại lẫn lợi nhuận “vòng đời thứ hai” → hỏi lý do trước, chỉ đầu tư vào lý do sửa được.

| Ngày | Kênh | Hành động |
| --- | --- | --- |
| 0 | Email tự động | Khảo sát 1 câu: lý do ít mua (giá, vận chuyển, sản phẩm, dịch vụ) |
| 3 | Email tự động | Chỉ với khách chọn “giá”/“vận chuyển”: miễn phí vận chuyển đơn kế tiếp |
| 14 | — | Không phản hồi → về nhịp newsletter của S6; không gọi điện, không voucher lớn |

KPI: tỷ lệ trả lời khảo sát, chi phí trên mỗi khách giữ được, phân bố lý do rời bỏ.

### S4 – Khách trung thành (Risk thấp × CLV High)

Không cần giảm giá (Anderson & Simester). [Drèze & Nunes (2009)](https://www.sciencedaily.com/releases/2008/12/081215111425.htm): hạng cao nhất càng đông thì cảm nhận đẳng cấp càng loãng, thêm hạng dưới làm hạng trên thấy đặc biệt hơn. [Schmitt, Skiera & Van den Bulte (2011)](https://faculty.wharton.upenn.edu/wp-content/uploads/2012/04/Schmitt-Skiera-vandenBulte-2011-Referral-Programs-Customer-Value.pdf): khách đến qua giới thiệu có giá trị cao hơn ít nhất 16% và giữ chân tốt hơn.

| Ngày | Kênh | Hành động |
| --- | --- | --- |
| 0 | Email + app | Mời hạng Gold (giới hạn trong nhóm CLV cao nhất), mua sớm sản phẩm mới |
| 7 | Email | Chương trình giới thiệu bạn bè, thưởng cả hai bên |
| 14 sau mỗi đơn | Email | Mời viết đánh giá |

KPI: khách mới từ giới thiệu, retention 12 tháng, tỷ lệ chuyển sang rủi ro cao.

### S5 – Ổn định cần nuôi (Risk thấp × CLV Mid)

Đưa khách lên S4 bằng tăng giá trị đơn và mua thêm ngành hàng. Nhưng [Shah, Kumar, Qu & Chen (2012)](https://www.denishshah.com/research.html) ghi nhận 10–35% khách cross-buy tại 5 công ty không có lãi, gắn với trả hàng nhiều, đòi hỏi dịch vụ cao và chỉ mua hàng giảm sâu ([tóm tắt công bố](https://www.prweb.com/releases/big_data_analytics_study_reveals_that_adverse_cross_buying_customer_behavior_will_decrease_a_firm_s_profits_between_39_to_88_/prweb11235309.htm)) → loại khách có Returns_Rate hoặc Discount_Usage_Rate thuộc top 25% khỏi danh sách cross-sell. Hạng Silver dưới Gold vừa tạo mục tiêu lên hạng vừa làm Gold có giá trị hơn.

| Ngày | Kênh | Hành động |
| --- | --- | --- |
| 0 | Email + app | Vào hạng Silver, hiển thị tiến độ lên Gold |
| 3 | Email / social | Gợi ý từ wishlist và ngành hàng bổ sung (đã sàng lọc) |
| 10 | Email | Bundle 2–3 sản phẩm tăng giá trị đơn |

KPI: AOV, số ngành hàng mỗi khách mua, tỷ lệ lên S4 sau 6 tháng.

### S6 – Phổ thông (Risk thấp × CLV Low)

Nhóm “barnacles”: ở lại nhưng ít lãi → kênh gần như không tốn chi phí. Trong dữ liệu, mức dùng app tương quan nghịch với churn (r = −0,22) và thuận với Lifetime_Value (r = 0,53), nên kích hoạt dùng app là đòn bẩy rẻ nhất (tương quan, chưa phải nhân quả).

| Ngày | Kênh | Hành động |
| --- | --- | --- |
| 0 | Email | Newsletter 2 tuần/lần |
| 7 | Email + SMS | Mời cài và dùng app, ưu đãi nhỏ cho đơn đầu trên app |

KPI: chi phí trên mỗi khách, tỷ lệ dùng app, tỷ lệ lên S5.

## 4. Nguồn

1. Anderson, E. T., & Simester, D. I. (2004). Long-run effects of promotion depth on new versus established customers. *Marketing Science*, 23(1), 4–20.
2. Ascarza, E. (2018). Retention futility: Targeting high-risk customers might be ineffective. *Journal of Marketing Research*, 55(1), 80–98.
3. Baymard Institute (2025). Cart abandonment rate statistics, cập nhật 22/9/2025.
4. Drèze, X., & Nunes, J. C. (2009). Feeling superior: The impact of loyalty program structure on consumers’ perceptions of status. *Journal of Consumer Research*, 35(6), 890–905.
5. Knox, G., & van Oest, R. (2014). Customer complaints and recovery effectiveness: A customer base approach. *Journal of Marketing*, 78(5), 42–57.
6. Kumar, V., Bhagwat, Y., & Zhang, X. (2015). Regaining “lost” customers. *Journal of Marketing*, 79(4), 34–55.
7. Lemmens, A., & Gupta, S. (2020). Managing churn to maximize profits. *Marketing Science*.
8. Reichheld, F. F., & Sasser, W. E. (1990). Zero defections: Quality comes to services. *Harvard Business Review*, 68(5).
9. Reinartz, W., & Kumar, V. (2002). The mismanagement of customer loyalty. *Harvard Business Review*, 80(7).
10. Schmitt, P., Skiera, B., & Van den Bulte, C. (2011). Referral programs and customer value. *Journal of Marketing*, 75(1), 46–59.
11. Shah, D., Kumar, V., Qu, Y., & Chen, S. (2012). Unprofitable cross-buying. *Journal of Marketing*, 76(3), 78–95.
12. Thomas, J. S., Blattberg, R. C., & Fox, E. J. (2004). Recapturing lost customers. *Journal of Marketing Research*, 41(1), 31–45.

> Số tập/số kỳ của Drèze & Nunes, Schmitt et al., Reinartz & Kumar, Reichheld & Sasser cần kiểm tra bản gốc qua thư viện UEL. Con số 10–35% của Shah et al. lấy từ bản tóm tắt công bố.
