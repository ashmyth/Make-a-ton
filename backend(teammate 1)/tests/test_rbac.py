from types import SimpleNamespace

import pytest
from rest_framework.test import APIRequestFactory

from apps.access_control.permissions import (
    CustomerDataIsolation,
    IsAdministrator,
    IsCustomerUser,
    IsFinanceStaff,
    IsOperationsStaff,
    IsStaffUser,
)
from apps.access_control.scoping import scope_to_customer
from apps.customers.models import Customer
from tests.factories import UserFactory, customer_payload

STAFF = "/api/v1/staff/"
CUSTOMERS = "/api/v1/customers/"
AUDIT = "/api/v1/audit/"


def staff_payload(**overrides):
    payload = {
        "email": "new.ops@example.com",
        "first_name": "New",
        "last_name": "Ops",
        "role": "OPERATIONS",
        "password": "Str0ng!Passw0rd",
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
class TestRoleBasedAccessControl:
    def test_anonymous_is_rejected_everywhere(self, api):
        for url in (STAFF, CUSTOMERS, AUDIT, CUSTOMERS + "my-profile/"):
            assert api.get(url).status_code == 403, url

    def test_operations_cannot_create_staff_account(self, make_client, ops):
        response = make_client(ops).post(STAFF, staff_payload(), format="json")
        assert response.status_code == 403

    def test_finance_cannot_list_staff(self, make_client, finance):
        assert make_client(finance).get(STAFF).status_code == 403

    def test_admin_can_create_staff_account(self, make_client, admin):
        response = make_client(admin).post(STAFF, staff_payload(), format="json")
        assert response.status_code == 201

    def test_customer_cannot_access_staff_or_audit_endpoints(self, make_client, customer_user):
        client = make_client(customer_user)
        assert client.get(STAFF).status_code == 403
        assert client.post(STAFF, staff_payload(), format="json").status_code == 403
        assert client.get(AUDIT).status_code == 403
        assert client.get(CUSTOMERS).status_code == 403

    @pytest.mark.parametrize("fixture", ["ops", "finance"])
    def test_non_admin_staff_cannot_read_audit_log(self, request, make_client, fixture):
        assert make_client(request.getfixturevalue(fixture)).get(AUDIT).status_code == 403

    def test_customer_cannot_view_other_customer_record(
        self, make_client, customer_user, other_customer
    ):
        response = make_client(customer_user).get(f"{CUSTOMERS}{other_customer.pk}/")
        assert response.status_code == 403
        assert other_customer.display_name not in response.content.decode()

    def test_customer_cannot_patch_other_customer_record(
        self, make_client, customer_user, other_customer
    ):
        response = make_client(customer_user).patch(
            f"{CUSTOMERS}{other_customer.pk}/", {"phone": "+1 555 9999"}, format="json"
        )
        assert response.status_code == 403
        other_customer.refresh_from_db()
        assert other_customer.phone != "+1 555 9999"

    def test_customer_can_view_own_record(self, make_client, customer_user):
        response = make_client(customer_user).get(f"{CUSTOMERS}{customer_user.customer.pk}/")
        assert response.status_code == 200
        assert response.data["display_name"] == "Acme Corporation"

    def test_customer_can_update_contact_and_address_only(self, make_client, customer_user):
        client = make_client(customer_user)
        url = f"{CUSTOMERS}{customer_user.customer.pk}/"
        ok = client.patch(
            url, {"phone": "+1 555 7777", "billing_city": "Shelbyville"}, format="json"
        )
        assert ok.status_code == 200
        assert ok.data["billing_city"] == "Shelbyville"

    @pytest.mark.parametrize(
        "field,value",
        [
            ("display_name", "Hijacked"),
            ("customer_type", "INDIVIDUAL"),
            ("tax_identifier", "FAKE-TAX"),
            ("payment_terms", "NET_60"),
            ("status", "ARCHIVED"),
            ("customer_code", "CUST-HACKED1"),
            ("portal_user_id", "00000000-0000-0000-0000-000000000000"),
        ],
    )
    def test_customer_cannot_modify_forbidden_fields(
        self, make_client, customer_user, field, value
    ):
        customer = customer_user.customer
        before = Customer.objects.values().get(pk=customer.pk)
        response = make_client(customer_user).patch(
            f"{CUSTOMERS}{customer.pk}/", {field: value}, format="json"
        )
        assert response.status_code == 403
        assert field in response.data["detail"]
        assert Customer.objects.values().get(pk=customer.pk) == before

    def test_customer_cannot_create_customers(self, make_client, customer_user):
        response = make_client(customer_user).post(CUSTOMERS, customer_payload(), format="json")
        assert response.status_code == 403

    def test_finance_can_read_but_not_create_or_archive_customers(
        self, make_client, finance, other_customer
    ):
        client = make_client(finance)
        assert client.get(CUSTOMERS).status_code == 200
        assert client.get(f"{CUSTOMERS}{other_customer.pk}/").status_code == 200
        assert client.post(CUSTOMERS, customer_payload(), format="json").status_code == 403
        assert client.post(f"{CUSTOMERS}{other_customer.pk}/archive/").status_code == 403

    def test_deactivated_user_loses_access_with_existing_session(self, make_client, ops):
        client = make_client(ops)
        assert client.get(CUSTOMERS).status_code == 200
        ops.is_active = False
        ops.save()
        assert client.get(CUSTOMERS).status_code == 403


@pytest.mark.django_db
class TestPermissionClasses:
    def _request(self, user):
        request = APIRequestFactory().get("/")
        request.user = user
        return request

    @pytest.mark.parametrize(
        "permission,allowed",
        [
            (IsAdministrator, {"ADMINISTRATOR"}),
            (IsOperationsStaff, {"ADMINISTRATOR", "OPERATIONS"}),
            (IsFinanceStaff, {"ADMINISTRATOR", "FINANCE"}),
            (IsStaffUser, {"ADMINISTRATOR", "OPERATIONS", "FINANCE"}),
            (IsCustomerUser, {"CUSTOMER"}),
        ],
    )
    def test_role_matrix(self, permission, allowed):
        for role in ("ADMINISTRATOR", "OPERATIONS", "FINANCE", "CUSTOMER"):
            user = UserFactory(role=role)
            assert permission().has_permission(self._request(user), None) is (role in allowed)

    def test_inactive_user_is_denied(self):
        user = UserFactory(role="ADMINISTRATOR", is_active=False)
        assert not IsAdministrator().has_permission(self._request(user), None)

    def test_data_isolation_with_foreign_key_style_objects(self, customer_user, other_customer):
        permission = CustomerDataIsolation()
        request = self._request(customer_user)
        own = SimpleNamespace(customer_id=customer_user.customer.pk)
        foreign = SimpleNamespace(customer_id=other_customer.pk)
        orphan = SimpleNamespace(customer_id=None)
        assert permission.has_object_permission(request, None, own)
        assert not permission.has_object_permission(request, None, foreign)
        assert not permission.has_object_permission(request, None, orphan)

    def test_unlinked_customer_user_owns_nothing(self, other_customer):
        user = UserFactory(role="CUSTOMER")
        request = self._request(user)
        assert not CustomerDataIsolation().has_object_permission(request, None, other_customer)

    def test_scope_to_customer(self, admin, customer_user, other_customer):
        queryset = Customer.objects.all()
        assert scope_to_customer(queryset, admin, field="id").count() == 2
        scoped = scope_to_customer(queryset, customer_user, field="id")
        assert list(scoped) == [customer_user.customer]
        assert scope_to_customer(queryset, UserFactory(role="CUSTOMER"), field="id").count() == 0

    def test_request_user_exposes_customer_contract(self, customer_user):
        assert customer_user.customer_id == customer_user.customer.pk
        assert UserFactory().customer is None
        assert UserFactory().customer_id is None
