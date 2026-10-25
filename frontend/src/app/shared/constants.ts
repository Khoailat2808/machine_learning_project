// Miền dữ liệu cố định, khớp COUNTRY_CITIES ở backend/apps/customers/models.py
export const COUNTRY_CITIES: Record<string, string[]> = {
  USA: ['Chicago', 'Houston', 'Los Angeles', 'New York', 'Phoenix'],
  UK: ['Birmingham', 'Glasgow', 'Leeds', 'London', 'Manchester'],
  Canada: ['Calgary', 'Montreal', 'Ottawa', 'Toronto', 'Vancouver'],
  Germany: ['Berlin', 'Cologne', 'Frankfurt', 'Hamburg', 'Munich'],
  Australia: ['Adelaide', 'Brisbane', 'Melbourne', 'Perth', 'Sydney'],
  France: ['Lyon', 'Marseille', 'Nice', 'Paris', 'Toulouse'],
  India: ['Bangalore', 'Chennai', 'Delhi', 'Hyderabad', 'Mumbai'],
  Japan: ['Kyoto', 'Nagoya', 'Osaka', 'Tokyo', 'Yokohama'],
};

export const COUNTRIES = Object.keys(COUNTRY_CITIES);

// Tên mặc định theo docs/06 (nội dung lộ trình sửa qua Django Admin; mã S1–S6 cố định)
export const SEGMENT_NAMES: Record<string, string> = {
  S1: 'VIP nguy cơ',
  S2: 'Tiềm năng dễ mất',
  S3: 'Giá trị thấp rủi ro',
  S4: 'Khách trung thành',
  S5: 'Ổn định cần nuôi',
  S6: 'Phổ thông',
};
export const SEGMENTS = Object.keys(SEGMENT_NAMES);

export const LEVEL_LABELS: Record<string, string> = { High: 'Cao', Mid: 'Trung bình', Low: 'Thấp' };

export const CHANNELS: Record<string, { label: string; icon: string }> = {
  Phone: { label: 'Điện thoại', icon: 'call' },
  Email: { label: 'Email', icon: 'mail' },
  'Push app / SMS': { label: 'Push app / SMS', icon: 'sms' },
};

// Nhãn 23 trường input, khớp LABELS ở ml_engine/src/explain.py
export const FIELD_LABELS: Record<string, string> = {
  Age: 'Tuổi',
  Gender: 'Giới tính',
  Country: 'Quốc gia',
  City: 'Thành phố',
  Signup_Quarter: 'Quý đăng ký',
  Membership_Years: 'Số năm là thành viên',
  Login_Frequency: 'Số lần đăng nhập',
  Session_Duration_Avg: 'Thời lượng phiên (phút)',
  Pages_Per_Session: 'Số trang mỗi phiên',
  Cart_Abandonment_Rate: 'Tỷ lệ bỏ giỏ hàng',
  Wishlist_Items: 'Số món trong wishlist',
  Total_Purchases: 'Tổng số lần mua',
  Average_Order_Value: 'Giá trị đơn trung bình (USD)',
  Days_Since_Last_Purchase: 'Số ngày từ lần mua cuối',
  Discount_Usage_Rate: 'Tỷ lệ dùng mã giảm giá',
  Returns_Rate: 'Tỷ lệ trả hàng',
  Email_Open_Rate: 'Tỷ lệ mở email',
  Customer_Service_Calls: 'Số lần gọi CSKH',
  Product_Reviews_Written: 'Số đánh giá sản phẩm',
  Social_Media_Engagement_Score: 'Mức tương tác mạng xã hội',
  Mobile_App_Usage: 'Mức dùng app',
  Payment_Method_Diversity: 'Số phương thức thanh toán',
  Credit_Balance: 'Số dư tín dụng (USD)',
};

const PERCENT_FIELDS = new Set(['Cart_Abandonment_Rate', 'Discount_Usage_Rate', 'Returns_Rate', 'Email_Open_Rate']);
const number = new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 });

const VALUE_LABELS: Record<string, string> = { Male: 'Nam', Female: 'Nữ', Other: 'Khác' };

/** Giá trị một trường để hiển thị: tỷ lệ thêm %, số theo kiểu Việt Nam, trống → —. */
export function formatField(field: string, value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === '') return '—';
  if (typeof value === 'string') return VALUE_LABELS[value] ?? value;
  return number.format(value) + (PERCENT_FIELDS.has(field) ? '%' : '');
}
