import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.access_control.roles import UserRole
from tests.factories import CustomerFactory, UserFactory


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Create the DB cache table (used for throttling) in the test database."""
    with django_db_blocker.unblock():
        call_command("createcachetable")


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def make_client():
    def _make(user):
        client = APIClient()
        client.force_login(user)
        return client

    return _make


@pytest.fixture
def admin(db):
    return UserFactory(role=UserRole.ADMINISTRATOR, email="admin@example.com")


@pytest.fixture
def ops(db):
    return UserFactory(role=UserRole.OPERATIONS, email="ops@example.com")


@pytest.fixture
def finance(db):
    return UserFactory(role=UserRole.FINANCE, email="finance@example.com")


@pytest.fixture
def customer_user(db):
    user = UserFactory(role=UserRole.CUSTOMER, email="alice@acme.example.com")
    CustomerFactory(display_name="Acme Corporation", portal_user=user)
    user.refresh_from_db()
    return user


@pytest.fixture
def other_customer(db):
    return CustomerFactory(display_name="Other Co")
