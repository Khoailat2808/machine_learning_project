"""Customer input schema; cleaning and imputation belong to import/seed."""

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models


COUNTRY_CITIES = {
    "USA": ("Chicago", "Houston", "Los Angeles", "New York", "Phoenix"),
    "UK": ("Birmingham", "Glasgow", "Leeds", "London", "Manchester"),
    "Canada": ("Calgary", "Montreal", "Ottawa", "Toronto", "Vancouver"),
    "Germany": ("Berlin", "Cologne", "Frankfurt", "Hamburg", "Munich"),
    "Australia": ("Adelaide", "Brisbane", "Melbourne", "Perth", "Sydney"),
    "France": ("Lyon", "Marseille", "Nice", "Paris", "Toulouse"),
    "India": ("Bangalore", "Chennai", "Delhi", "Hyderabad", "Mumbai"),
    "Japan": ("Kyoto", "Nagoya", "Osaka", "Tokyo", "Yokohama"),
}


def numeric_input(column: str, maximum: float, *, minimum: float = 0,
                  integer: bool = False, optional: bool = False) -> models.Field:
    """Apply FR-PRED bounds and preserve the original dataset column name."""
    field_type = models.IntegerField if integer else models.FloatField
    return field_type(db_column=column, null=optional, blank=optional,
                      validators=[MinValueValidator(minimum), MaxValueValidator(maximum)])


def positive_aov(value: float) -> None:
    """AOV has a strictly positive lower bound."""
    if value <= 0:
        raise ValidationError("Phải lớn hơn 0.")


class Customer(models.Model):
    """23 input attributes; no target or historical lifetime value."""

    class Gender(models.TextChoices):
        MALE = "Male"
        FEMALE = "Female"
        OTHER = "Other"

    Country = models.TextChoices("Country", {name.upper(): name for name in COUNTRY_CITIES})
    City = models.TextChoices("City", {city.upper().replace(" ", "_"): city
                                      for cities in COUNTRY_CITIES.values() for city in cities})

    class Quarter(models.TextChoices):
        Q1 = "Q1"
        Q2 = "Q2"
        Q3 = "Q3"
        Q4 = "Q4"

    class Source(models.TextChoices):
        SEED = "seed"
        UPLOAD = "upload"
        FORM = "form"

    customer_id = models.CharField(primary_key=True, max_length=32,
                                  validators=[RegexValidator(r"^CUS[0-9]{5,}$")])
    age = numeric_input("Age", 100, minimum=13, integer=True, optional=True)
    gender = models.CharField(max_length=6, choices=Gender, db_column="Gender")
    country = models.CharField(max_length=9, choices=Country, db_column="Country")
    city = models.CharField(max_length=11, choices=City, db_column="City")
    signup_quarter = models.CharField(max_length=2, choices=Quarter, db_column="Signup_Quarter")
    membership_years = numeric_input("Membership_Years", 10)
    login_frequency = numeric_input("Login_Frequency", 50, integer=True)
    session_duration_avg = numeric_input("Session_Duration_Avg", 120, optional=True)
    pages_per_session = numeric_input("Pages_Per_Session", 30, optional=True)
    cart_abandonment_rate = numeric_input("Cart_Abandonment_Rate", 100)
    wishlist_items = numeric_input("Wishlist_Items", 50, integer=True, optional=True)
    total_purchases = numeric_input("Total_Purchases", 150)
    average_order_value = models.FloatField(db_column="Average_Order_Value",
                                           validators=[positive_aov, MaxValueValidator(10000)])
    days_since_last_purchase = numeric_input("Days_Since_Last_Purchase", 365, integer=True, optional=True)
    discount_usage_rate = numeric_input("Discount_Usage_Rate", 100, optional=True)
    returns_rate = numeric_input("Returns_Rate", 100, optional=True)
    email_open_rate = numeric_input("Email_Open_Rate", 100, optional=True)
    customer_service_calls = numeric_input("Customer_Service_Calls", 30, integer=True, optional=True)
    product_reviews_written = numeric_input("Product_Reviews_Written", 30, integer=True, optional=True)
    social_media_engagement_score = numeric_input("Social_Media_Engagement_Score", 100, optional=True)
    mobile_app_usage = numeric_input("Mobile_App_Usage", 100, optional=True)
    payment_method_diversity = numeric_input("Payment_Method_Diversity", 5, minimum=1, integer=True, optional=True)
    credit_balance = numeric_input("Credit_Balance", 10000, optional=True)
    source = models.CharField(max_length=6, choices=Source)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "customers"
        indexes = [models.Index(fields=["country"], name="customers_country_idx")]

    def clean(self) -> None:
        """Validate the dependent city without changing input values."""
        super().clean()
        if self.country in COUNTRY_CITIES and self.city not in COUNTRY_CITIES[self.country]:
            raise ValidationError({"city": "Thành phố không thuộc quốc gia đã chọn."})

    def __str__(self) -> str:
        return self.customer_id
