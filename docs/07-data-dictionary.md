# 07 – Data dictionary

File: `ml_engine/data/raw/ecommerce_customer_dataset.csv` · 50.000 dòng × 25 cột · không trùng lặp · không có customer ID (hệ thống tự sinh `CUS00001…`). Tỷ lệ churn 28,9%.

## 1. Các cột

| Cột | Kiểu | Missing | Min | Trung vị | Max | Vai trò |
| --- | --- | --- | --- | --- | --- | --- |
| Age | số | 5,0% | 5 | 38 | 200 | Feature |
| Gender | phân loại (3) | 0% | — | — | — | Feature: Male, Female, Other |
| Country | phân loại (8) | 0% | — | — | — | Feature |
| City | phân loại (40) | 0% | — | — | — | Feature, phụ thuộc Country |
| Membership_Years | số | 0% | 0,1 | 2,5 | 10 | Feature; mẫu số tần suất trong CLV |
| Login_Frequency | số | 0% | 0 | 11 | 46 | Feature |
| Session_Duration_Avg | số (phút) | 6,8% | 1 | 26,8 | 75,6 | Feature |
| Pages_Per_Session | số | 6,0% | 1 | 8,4 | 24,1 | Feature |
| Cart_Abandonment_Rate | số (%) | 0% | 0 | 58,1 | 143,7 | Feature |
| Wishlist_Items | số | 8,0% | 0 | 4 | 28 | Feature |
| Total_Purchases | số | 0% | −13 | 12 | 128,7 | Feature; tử số tần suất trong CLV |
| Average_Order_Value | số (USD) | 0% | 26,38 | 112,97 | 9.666,38 | Feature; thành phần CLV |
| Days_Since_Last_Purchase | số (ngày) | 6,0% | 0 | 21 | 287 | Feature (recency) |
| Discount_Usage_Rate | số (%) | 7,0% | 0,24 | 40,2 | 116,6 | Feature |
| Returns_Rate | số (%) | 9,0% | 0 | 5,4 | 99,6 | Feature; trừ doanh thu trong CLV |
| Email_Open_Rate | số (%) | 5,1% | 0 | 19,7 | 91,7 | Feature |
| Customer_Service_Calls | số | 0,3% | 0 | 5 | 21 | Feature |
| Product_Reviews_Written | số | 7,0% | 0 | 2 | 21 | Feature |
| Social_Media_Engagement_Score | số (0–100) | 12,0% | 0 | 27,6 | 100 | Feature |
| Mobile_App_Usage | số | 10,0% | 0 | 18,6 | 61,9 | Feature |
| Payment_Method_Diversity | số | 5,0% | 1 | 2 | 5 | Feature |
| Lifetime_Value | số (USD) | 0% | 0 | 1.243,41 | 8.987,24 | **Không dùng làm feature** (leakage); chỉ đối chiếu CLV |
| Credit_Balance | số (USD) | 11,0% | 0 | 1.896 | 7.197 | Feature |
| Churned | 0/1 | 0% | 0 | 0 | 1 | **Nhãn** model churn |
| Signup_Quarter | phân loại (4) | 0% | — | — | — | Feature: Q1–Q4 |

`Lifetime_Value` tương quan Pearson 0,88 với Total_Purchases × AOV, tức gần với chi tiêu đã qua, không phải CLV tương lai.

## 2. Thành phố theo quốc gia

| Country | Số khách | Cities |
| --- | --- | --- |
| USA | 17.384 | Chicago, Houston, Los Angeles, New York, Phoenix |
| UK | 7.534 | Birmingham, Glasgow, Leeds, London, Manchester |
| Canada | 6.023 | Calgary, Montreal, Ottawa, Toronto, Vancouver |
| Germany | 4.925 | Berlin, Cologne, Frankfurt, Hamburg, Munich |
| Australia | 4.061 | Adelaide, Brisbane, Melbourne, Perth, Sydney |
| France | 4.013 | Lyon, Marseille, Nice, Paris, Toulouse |
| India | 3.512 | Bangalore, Chennai, Delhi, Hyderabad, Mumbai |
| Japan | 2.548 | Kyoto, Nagoya, Osaka, Tokyo, Yokohama |

## 3. Lỗi dữ liệu và quy tắc làm sạch (`clean.py`)

| Vấn đề | Quy mô | Xử lý |
| --- | --- | --- |
| Missing values | 15/25 cột, 0,3–12% mỗi cột | Median imputer (fit trên train) + cờ `is_missing_<col>` cho cột > 8% |
| Age vô lý | 30 dòng < 13, 20 dòng > 100 | Gán NaN rồi impute |
| Total_Purchases âm | 40 dòng < 0; 11.241 dòng không nguyên | Clip ≥ 0; giữ số lẻ |
| Tỷ lệ > 100% | Cart_Abandonment 30 dòng, Discount_Usage 207 dòng | Clip [0, 100] |
| Outlier AOV | 25 dòng > 1.000 USD | Winsorize p99 (lưu ngưỡng vào config) |
| LTV = 0 | 9 dòng | Giữ, kiểm tra riêng khi đối chiếu CLV |

Mọi ngưỡng (median, p99) fit trên tập train và lưu cùng pipeline, để `/predict` xử lý khách mới y hệt.

## 4. Tín hiệu chính (EDA nhanh)

| Biến | Tương quan với Churned | Tương quan với Lifetime_Value |
| --- | --- | --- |
| Customer_Service_Calls | +0,29 | −0,30 |
| Cart_Abandonment_Rate | +0,28 | −0,50 |
| Days_Since_Last_Purchase | +0,15 | ≈ 0 |
| Pages_Per_Session | −0,23 | +0,53 |
| Session_Duration_Avg | −0,23 | +0,55 |
| Mobile_App_Usage | −0,22 | +0,53 |
| Email_Open_Rate | −0,22 | +0,47 |
| Total_Purchases | −0,16 | +0,62 |

Tương quan Lifetime_Value–Churned ≈ −0,01 → hai trục rủi ro và giá trị gần như độc lập.

Baseline (HistGradientBoosting mặc định, chưa làm sạch, split 80/20): **ROC-AUC 0,918, PR-AUC 0,881**.
