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
