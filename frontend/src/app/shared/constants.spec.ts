import { formatField } from './constants';
import { ViPaginatorIntl } from './paginator-intl';

describe('formatField', () => {
  it('định dạng tỷ lệ, số, chữ và giá trị trống', () => {
    expect(formatField('Cart_Abandonment_Rate', 68.3)).toBe('68,3%');
    expect(formatField('Credit_Balance', 1123.456)).toBe('1.123,46');
    expect(formatField('Gender', 'Female')).toBe('Nữ');
    expect(formatField('Signup_Quarter', 'Q1')).toBe('Q1');
    expect(formatField('Age', null)).toBe('—');
  });

  it('nhãn phân trang tiếng Việt', () => {
    expect(new ViPaginatorIntl().getRangeLabel(1, 50, 5330)).toBe('51–100 / 5.330');
  });
});
