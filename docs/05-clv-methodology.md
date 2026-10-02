# 05 – Phương pháp tính CLV

> Kết luận: dùng **CLV 3 năm trên lợi nhuận ròng sau trả hàng, chiết khấu 10%/năm, tỷ lệ giữ chân lấy từ mô hình churn**. BG/NBD chỉ dùng để kiểm định chéo.
> Hướng tiếp cận đã được thầy duyệt; các tham số cụ thể (3 năm, trừ trả hàng, g = 33%, giả định chu kỳ nhãn 1 năm) đang chờ thầy góp ý.

## 1. Công thức

Với khách i:

```math
f_i = \frac{\text{Total\_Purchases}_i}{\max(\text{Membership\_Years}_i,\ 0.5)}
\qquad
m_i = \text{AOV}_i \times (1 - \text{Returns\_Rate}_i) \times f_i \times g
```

```math
\text{CLV}^{\text{kỳ vọng}}_i = \sum_{t=1}^{3} \frac{m_i\, r_i^{\,t}}{(1+d)^t},\quad r_i = 1 - p_i
\qquad
\text{CLV}^{\text{tiềm năng}}_i = \sum_{t=1}^{3} \frac{m_i\, \bar r^{\,t}}{(1+d)^t} = 1.334\, m_i
\qquad
\text{VaR}_i = p_i \times \text{CLV}^{\text{tiềm năng}}_i
```

| Tham số | Mặc định | Cơ sở |
| --- | --- | --- |
| T – horizon | 3 năm | Giới hạn hệ số nhân ở 2,44 thay vì 9,0 khi r = 0,99 (horizon vô hạn); lựa chọn của nhóm |
| g – biên lợi nhuận gộp | 33% | Gross margin Retail (General) Mỹ 33,18% ([Damodaran, 1/2026](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/margin.html)) |
| d – lãi suất chiết khấu | 10%/năm | Giả định; 8–12% không làm khách nào đổi tier |
| Doanh thu ròng | AOV × (1 − Returns_Rate) | Trừ hàng trả lại; làm 2,9% khách đổi tier |
| f – tần suất mua/năm | trung vị 4,7 | Membership_Years tối thiểu 0,5; cắt ở p99 (≈ 41 lần/năm) |
| r – tỷ lệ giữ chân cá nhân | 1 − p_churn | Từ model churn đã hiệu chỉnh xác suất; giả định nhãn Churned ứng với chu kỳ 1 năm |
| r̄ – tỷ lệ giữ chân trung bình | 0,711 | 1 − tỷ lệ churn toàn tệp; hệ số 3 năm = 1,334 |
| Quy ước thời điểm | t chạy từ 1 | Khách phải còn ở lại qua năm t mới tạo lợi nhuận năm t; khớp công thức m × r / (1 + d − r) |

**Vì sao cần hai giá trị.** CLV kỳ vọng đã chứa sẵn xác suất churn, nên nếu chia tier theo nó thì khách rủi ro cao gần như rơi hết vào tier Low và ô S1 chỉ còn 154 khách. Vì vậy:

- **CLV tiềm năng** → chia tier và tính VaR (trục giá trị độc lập với trục rủi ro).
- **CLV kỳ vọng** → hiển thị trong hồ sơ khách và tổng hợp trên dashboard.

## 2. Các phương án đã xem xét

[Gupta et al. (2006)](https://journals.sagepub.com/doi/10.1177/1094670506293810) chia mô hình CLV thành 6 nhóm (RFM, xác suất, kinh tế lượng, persistence, học máy, diffusion). Với dữ liệu dạng bảng snapshot, 4 phương án sau là khả thi:

| Phương án | Nguồn | Phù hợp với dữ liệu nhóm | Kết luận |
| --- | --- | --- | --- |
| Hồi quy có giám sát trên `Lifetime_Value` | Nhóm học máy trong Gupta et al. (2006) | Nhãn là chi tiêu quá khứ (Pearson 0,88 với Total_Purchases × AOV), model học lại quá khứ | Loại |
| Margin multiple, horizon vô hạn: m × r / (1 + d − r) | [Gupta & Lehmann (2003)](https://business.columbia.edu/faculty/research/customers-assets); Gupta et al. (2006) | Đủ dữ liệu; nhưng r gần 1 cho hệ số 9,0 (giả định khách ở lại > 10 năm) | Mốc so sánh |
| Tổng chiết khấu horizon hữu hạn: Σ m × rᵗ / (1 + d)ᵗ | [Berger & Nasr (1998)](https://www.sciepub.com/reference/261627); Gupta et al. (2006) | Đủ dữ liệu, kiểm soát được giả định thời gian gắn bó | **Chọn** |
| BG/NBD + Gamma-Gamma | [Fader, Hardie & Lee (2005a)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=578087); [Gamma-Gamma note](https://www.brucehardie.com/notes/025/gamma_gamma.pdf) | Chỉ cần recency, frequency, tuổi khách nên chạy được; nhưng khớp kém với nhãn churn | Kiểm định chéo (P1) |

## 3. Kết quả chạy thử (50.000 khách)

p_churn out-of-fold 5-fold từ model baseline, g = 33%, d = 10%, τ = 0,5.

| Biến thể | Trung bình (USD) | Trung vị (USD) | Spearman với Lifetime_Value | Khách ô S1 | VaR của S1 + S2 |
| --- | --- | --- | --- | --- | --- |
| A1. Vô hạn, kỳ vọng | 1.213 | 569 | 0,39 | 5 | 2,9% |
| A2. Vô hạn, tiềm năng | 529 | 321 | 0,61 | 3.869 | 67,8% |
| B1. 3 năm, kỳ vọng | 470 | 247 | 0,42 | 154 | 8,8% |
| B2. 3 năm, tiềm năng | 386 | 235 | 0,61 | 3.869 | 67,8% |
| **C. 3 năm, tiềm năng, doanh thu ròng** | **358** | **218** | **0,61** | **3.837** | **67,7%** |
| D. BG/NBD + Gamma-Gamma, 36 tháng | 713 | 428 | 0,62 | 3.893 | 67,7% |

- Biến thể “kỳ vọng” làm S1 gần như biến mất → phải chia tier bằng biến thể “tiềm năng”.
- A2, B2, C xếp hạng gần như giống nhau; horizon chỉ đổi mức USD.
- BG/NBD xếp hạng CLV gần trùng công thức (Spearman 0,98 với B2), nhưng xác suất “còn sống” chỉ đạt AUC 0,61 so với nhãn Churned (model ML: 0,92). Tham số a ≈ 0,003 → mô hình gần như không thấy ai rời đi, có thể do dữ liệu tổng hợp không sinh theo cơ chế BG/NBD giả định.
- Với công thức C: tổng CLV kỳ vọng ≈ 21,8 triệu USD, tổng VaR ≈ 5,0 triệu USD, P33/P67 của CLV tiềm năng = 143 / 342 USD.

## 4. Giới hạn cần ghi trong báo cáo

- **Tỷ lệ giữ chân không đổi theo thời gian.** [Fader & Hardie (2010)](https://faculty.wharton.upenn.edu/wp-content/uploads/2012/04/Fader_hardie_contractual_mksc_10.pdf) chỉ ra dùng một tỷ lệ chung làm giá trị tập khách bị đánh giá thấp khoảng 25–50%. CLV kỳ vọng giảm bớt vấn đề nhờ r riêng từng khách; CLV tiềm năng dùng r̄ nên mức USD có thể thấp hơn thực tế nhưng xếp hạng không đổi. Bài này làm cho bối cảnh có hợp đồng, chỉ nên dẫn như cảnh báo về hướng sai lệch.
- **Chu kỳ nhãn Churned chưa rõ.** Nếu không phải 1 năm thì phải quy đổi r về năm.
- **p_churn cần hiệu chỉnh xác suất** (calibration curve + isotonic/Platt) trước khi đưa vào CLV.
- **Biên lợi nhuận và chi phí phục vụ không theo từng khách** (chưa trừ chi phí CSKH) — mở rộng ở P2.
- **Dữ liệu tổng hợp**, số liệu trên từ model baseline chưa làm sạch.

## 5. Gợi ý cài đặt `ml_engine/src/clv.py`

```python
import numpy as np
import pandas as pd

def clv_components(df: pd.DataFrame, p_churn: np.ndarray, *, g=0.33, d=0.10,
                   horizon=3, r_bar=None, freq_cap=None):
    """Trả về DataFrame gồm clv_pred (kỳ vọng), clv_potential, value_at_risk."""
    tp = df["Total_Purchases"].clip(lower=0)
    years = df["Membership_Years"].clip(lower=0.5)
    freq = tp / years
    if freq_cap is not None:                 # lưu p99 của tập train trong clv_config
        freq = freq.clip(upper=freq_cap)
    returns = (df["Returns_Rate"].clip(0, 100) / 100).fillna(0)
    m = df["Average_Order_Value"] * (1 - returns) * freq * g

    r = 1 - np.asarray(p_churn)
    if r_bar is None:
        r_bar = r.mean()
    t = np.arange(1, horizon + 1)
    disc = (1 + d) ** t
    mult_expected = (r[:, None] ** t / disc).sum(axis=1)
    mult_potential = (r_bar ** t / disc).sum()

    out = pd.DataFrame(index=df.index)
    out["clv_pred"] = m * mult_expected
    out["clv_potential"] = m * mult_potential
    out["value_at_risk"] = np.asarray(p_churn) * out["clv_potential"]
    return out.round(2)
```

`AOV` nên được cắt ở p99 và `Returns_Rate` impute median trong `clean.py` trước khi gọi hàm này.

## 6. Nguồn

1. Berger, P. D., & Nasr, N. I. (1998). Customer lifetime value: Marketing models and applications. *Journal of Interactive Marketing*, 12(1), 17–30.
2. Damodaran, A. (2026). Operating and net margins by industry (US), dữ liệu tháng 1/2026.
3. Fader, P. S., Hardie, B. G. S., & Lee, K. L. (2005a). “Counting your customers” the easy way: An alternative to the Pareto/NBD model. *Marketing Science*, 24(2), 275–284.
4. Fader, P. S., Hardie, B. G. S., & Lee, K. L. (2005b). RFM and CLV: Using iso-value curves for customer base analysis. *Journal of Marketing Research*, 42(4), 415–430.
5. Fader, P. S., & Hardie, B. G. S. (2010). Customer-base valuation in a contractual setting: The perils of ignoring heterogeneity. *Marketing Science*, 29(1), 85–93.
6. Gupta, S., & Lehmann, D. R. (2003). Customers as assets. *Journal of Interactive Marketing*, 17(1), 9–24.
7. Gupta, S., Hanssens, D., Hardie, B., Kahn, W., Kumar, V., Lin, N., Ravishanker, N., & Sriram, S. (2006). Modeling customer lifetime value. *Journal of Service Research*, 9(2), 139–155.

> Số tập/số kỳ của một số bài cần kiểm tra lại bản gốc qua thư viện UEL trước khi đưa vào báo cáo.
