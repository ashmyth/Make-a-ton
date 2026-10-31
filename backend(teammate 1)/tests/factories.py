import factory
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

from apps.access_control.roles import UserRole
from apps.customers.models import Customer

PASSWORD = "Str0ng!Passw0rd"
_PASSWORD_HASH = make_password(PASSWORD)  # hash once; Argon2 is deliberately slow


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password = _PASSWORD_HASH
    first_name = "Test"
    last_name = "User"
    role = UserRole.CUSTOMER


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    customer_type = Customer.CustomerType.BUSINESS
    display_name = factory.Sequence(lambda n: f"Company {n}")
    contact_person = "Pat Contact"
    email = factory.Sequence(lambda n: f"billing{n}@company.example.com")
    phone = "+1 555 0100"
    billing_street = "1 Main Street"
    billing_city = "Springfield"
    billing_country = "US"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        return model_class.objects.create_with_code(**kwargs)


def customer_payload(**overrides):
    payload = {
        "customer_type": "BUSINESS",
        "display_name": "Globex Corporation",
        "contact_person": "Hank Scorpio",
        "email": "billing@globex.example.com",
        "phone": "+1 555 0199",
        "billing_street": "100 Evil Lane",
        "billing_city": "Cypress Creek",
        "billing_state": "CA",
        "billing_postal_code": "90210",
        "billing_country": "US",
        "tax_identifier": "US-EIN-12-3456789",
        "payment_terms": "NET_30",
    }
    payload.update(overrides)
    return payload
