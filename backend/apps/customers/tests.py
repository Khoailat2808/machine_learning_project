"""Customer input domains and dataset column mapping."""

from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import COUNTRY_CITIES, Customer


def customer_data() -> dict[str, object]:
    """Minimal valid customer, leaving all fourteen optional inputs absent."""
    return dict(customer_id="CUS00001", gender="Female", country="USA", city="Houston",
                signup_quarter="Q2", membership_years=1.5, login_frequency=8,
                cart_abandonment_rate=65, total_purchases=7.5,
                average_order_value=95.5, source="form")


class CustomerTests(TestCase):
    def test_optional_inputs_and_column_names(self) -> None:
        customer = Customer(**customer_data())
        customer.full_clean()
        customer.save()
        customer.refresh_from_db()
        inputs = [field for field in Customer._meta.fields if field.db_column]
        self.assertEqual(len(inputs), 23)
        optional = [field for field in inputs if field.null]
        self.assertEqual(len(optional), 14)
        for field in inputs:
            self.assertEqual(field.name, field.column.lower())
        for field in optional:
            self.assertTrue(field.blank)
            self.assertIsNone(getattr(customer, field.name))
        self.assertEqual(customer.total_purchases, 7.5)
        self.assertNotIn("Lifetime_Value", [field.column for field in inputs])
        self.assertNotIn("Churned", [field.column for field in inputs])

    def test_choices_and_country_city_dependency(self) -> None:
        for field in ("gender", "country", "city", "signup_quarter", "source"):
            with self.subTest(field=field):
                customer = Customer(**(customer_data() | {field: "invalid"}))
                with self.assertRaises(ValidationError):
                    customer.full_clean()
        for country, cities in COUNTRY_CITIES.items():
            for city in cities:
                Customer(**(customer_data() | {"country": country, "city": city})).full_clean()
        with self.assertRaises(ValidationError) as error:
            Customer(**(customer_data() | {"city": "London"})).full_clean()
        self.assertIn("city", error.exception.message_dict)

    def test_numeric_bounds_and_required_inputs(self) -> None:
        for field in Customer._meta.fields:
            if not field.db_column or field.get_internal_type() not in ("IntegerField", "FloatField"):
                continue
            for validator in field.validators:
                limit = getattr(validator, "limit_value", None)
                if limit is None:
                    continue
                invalid = limit - 1 if validator.code == "min_value" else limit + 1
                with self.subTest(field=field.name, invalid=invalid):
                    customer = Customer(**(customer_data() | {field.name: invalid}))
                    with self.assertRaises(ValidationError):
                        customer.full_clean()
        with self.assertRaises(ValidationError):
            Customer(**(customer_data() | {"average_order_value": 0})).full_clean()
        for field in ("gender", "country", "city", "signup_quarter", "membership_years",
                      "login_frequency", "cart_abandonment_rate", "total_purchases", "average_order_value"):
            with self.subTest(required=field), self.assertRaises(ValidationError):
                Customer(**(customer_data() | {field: None})).full_clean()
