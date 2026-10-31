import re

import pytest

from apps.access_control.roles import UserRole
from apps.audit.models import AuditAction, AuditLog
from apps.customers.models import Customer
from tests.factories import CustomerFactory, UserFactory, customer_payload

URL = "/api/v1/customers/"


@pytest.mark.django_db
class TestCustomerManagement:
    def test_create_customer_generates_code_and_audits(self, make_client, ops):
        response = make_client(ops).post(URL, customer_payload(), format="json")
        assert response.status_code == 201
        assert re.fullmatch(r"CUST-[A-Z0-9]{8}", response.data["customer_code"])
        assert response.data["status"] == "ACTIVE"
        assert response.data["portal_user_id"] is None
        customer = Customer.objects.get(pk=response.data["id"])
        assert customer.tax_identifier == "US-EIN-12-3456789"
        log = AuditLog.objects.get(action=AuditAction.CUSTOMER_CREATED)
        assert log.actor == ops and log.entity_id == str(customer.pk)

    def test_admin_can_create_customer(self, make_client, admin):
        assert make_client(admin).post(URL, customer_payload(), format="json").status_code == 201

    def test_codes_are_unique(self, make_client, ops):
        client = make_client(ops)
        codes = {
            client.post(URL, customer_payload(display_name=f"Co {i}"), format="json").data[
                "customer_code"
            ]
            for i in range(5)
        }
        assert len(codes) == 5

    def test_client_cannot_choose_code_or_status(self, make_client, ops):
        response = make_client(ops).post(
            URL, customer_payload(customer_code="CUST-CHOSEN1", status="ARCHIVED"), format="json"
        )
        assert response.status_code == 201
        assert response.data["customer_code"] != "CUST-CHOSEN1"
        assert response.data["status"] == "ACTIVE"

    @pytest.mark.parametrize(
        "overrides",
        [
            {"display_name": "   "},
            {"email": "not-an-email"},
            {"customer_type": "GOVERNMENT"},
            {"payment_terms": "NET_90"},
            {"billing_country": ""},
        ],
    )
    def test_validation_errors(self, make_client, ops, overrides):
        response = make_client(ops).post(URL, customer_payload(**overrides), format="json")
        assert response.status_code == 400
        assert Customer.objects.count() == 0

    def test_email_is_normalised(self, make_client, ops):
        response = make_client(ops).post(
            URL, customer_payload(email="Billing@Globex.EXAMPLE.com"), format="json"
        )
        assert response.data["email"] == "billing@globex.example.com"

    def test_search_by_name_code_email_and_contact(self, make_client, finance):
        acme = CustomerFactory(display_name="Acme Rockets", email="ap@acme.example.com")
        CustomerFactory(display_name="Initech", contact_person="Bill Lumbergh")
        client = make_client(finance)

        def search(term):
            return {r["id"] for r in client.get(URL, {"search": term}).data["results"]}

        assert search("rockets") == {str(acme.pk)}
        assert search(acme.customer_code.lower()) == {str(acme.pk)}
        assert search("ap@acme") == {str(acme.pk)}
        assert len(search("lumbergh")) == 1
        assert search("zzz-no-match") == set()

    def test_filter_by_status_and_type(self, make_client, ops):
        active = CustomerFactory()
        archived = CustomerFactory(status="ARCHIVED")
        person = CustomerFactory(customer_type="INDIVIDUAL")
        client = make_client(ops)
        ids = lambda params: {r["id"] for r in client.get(URL, params).data["results"]}  # noqa: E731
        assert ids({"status": "ACTIVE"}) == {str(active.pk), str(person.pk)}
        assert ids({"status": "ARCHIVED"}) == {str(archived.pk)}
        assert ids({"customer_type": "INDIVIDUAL"}) == {str(person.pk)}
        assert client.get(URL, {"status": "BOGUS"}).status_code == 400
        assert client.get(URL, {"customer_type": "BOGUS"}).status_code == 400

    def test_list_is_paginated_and_newest_first(self, make_client, ops):
        customers = [CustomerFactory() for _ in range(3)]
        data = make_client(ops).get(URL, {"page_size": 2}).data
        assert data["count"] == 3 and len(data["results"]) == 2 and data["next"]
        assert data["results"][0]["id"] == str(customers[-1].pk)

    def test_update_by_staff_records_field_level_diff(self, make_client, finance):
        customer = CustomerFactory(payment_terms="NET_30", tax_identifier="")
        response = make_client(finance).patch(
            f"{URL}{customer.pk}/",
            {"payment_terms": "NET_60", "tax_identifier": "GB123456789"},
            format="json",
        )
        assert response.status_code == 200
        log = AuditLog.objects.get(action=AuditAction.CUSTOMER_UPDATED)
        assert log.details["changes"] == {
            "payment_terms": ["NET_30", "NET_60"],
            "tax_identifier": ["", "GB123456789"],
        }

    def test_status_cannot_be_changed_through_patch(self, make_client, ops):
        customer = CustomerFactory()
        make_client(ops).patch(f"{URL}{customer.pk}/", {"status": "ARCHIVED"}, format="json")
        customer.refresh_from_db()
        assert customer.status == "ACTIVE"

    def test_unknown_customer_returns_404(self, make_client, ops):
        assert (
            make_client(ops).get(f"{URL}8d2f0f0e-0000-4000-8000-000000000000/").status_code == 404
        )

    def test_delete_and_put_are_not_allowed(self, make_client, admin):
        customer = CustomerFactory()
        client = make_client(admin)
        assert client.delete(f"{URL}{customer.pk}/").status_code == 405
        assert (
            client.put(f"{URL}{customer.pk}/", customer_payload(), format="json").status_code == 405
        )
        assert Customer.objects.filter(pk=customer.pk).exists()

    def test_archive_customer(self, make_client, ops):
        customer = CustomerFactory()
        client = make_client(ops)
        response = client.post(f"{URL}{customer.pk}/archive/")
        assert response.status_code == 200
        assert response.data["status"] == "ARCHIVED"
        customer.refresh_from_db()
        assert customer.status == "ARCHIVED"
        assert AuditLog.objects.filter(
            action=AuditAction.CUSTOMER_ARCHIVED, entity_id=str(customer.pk)
        ).exists()
        assert client.post(f"{URL}{customer.pk}/archive/").status_code == 409

    def test_link_portal_user(self, make_client, ops):
        customer = CustomerFactory()
        user = UserFactory(role=UserRole.CUSTOMER)
        response = make_client(ops).post(
            f"{URL}{customer.pk}/link-portal/", {"user_id": str(user.pk)}, format="json"
        )
        assert response.status_code == 200
        assert response.data["portal_user_id"] == str(user.pk)
        assert response.data["portal_user_email"] == user.email
        user.refresh_from_db()
        assert user.customer_id == customer.pk
        assert AuditLog.objects.filter(action=AuditAction.CUSTOMER_PORTAL_LINKED).exists()

    def test_linked_user_sees_only_their_profile(self, make_client, ops):
        customer = CustomerFactory(display_name="Linked Co")
        user = UserFactory(role=UserRole.CUSTOMER)
        make_client(ops).post(
            f"{URL}{customer.pk}/link-portal/", {"user_id": str(user.pk)}, format="json"
        )
        profile = make_client(user).get(f"{URL}my-profile/")
        assert profile.status_code == 200
        assert profile.data["display_name"] == "Linked Co"

    @pytest.mark.parametrize("role", ["OPERATIONS", "FINANCE", "ADMINISTRATOR"])
    def test_staff_users_cannot_be_linked_as_portal_users(self, make_client, ops, role):
        customer = CustomerFactory()
        staff_user = UserFactory(role=role)
        response = make_client(ops).post(
            f"{URL}{customer.pk}/link-portal/", {"user_id": str(staff_user.pk)}, format="json"
        )
        assert response.status_code == 400
        customer.refresh_from_db()
        assert customer.portal_user is None

    def test_link_portal_rejects_unknown_inactive_and_already_linked_users(
        self, make_client, ops, customer_user
    ):
        customer = CustomerFactory()
        client = make_client(ops)
        link = lambda uid: client.post(  # noqa: E731
            f"{URL}{customer.pk}/link-portal/", {"user_id": str(uid)}, format="json"
        )
        assert link("8d2f0f0e-0000-4000-8000-000000000000").status_code == 400
        assert link(UserFactory(role="CUSTOMER", is_active=False).pk).status_code == 400
        assert link(customer_user.pk).status_code == 400
        assert client.post(f"{URL}{customer.pk}/link-portal/", {}, format="json").status_code == 400

    def test_cannot_relink_customer_that_already_has_portal_user(
        self, make_client, ops, customer_user
    ):
        newcomer = UserFactory(role="CUSTOMER")
        response = make_client(ops).post(
            f"{URL}{customer_user.customer.pk}/link-portal/",
            {"user_id": str(newcomer.pk)},
            format="json",
        )
        assert response.status_code == 409
        customer_user.customer.refresh_from_db()
        assert customer_user.customer.portal_user_id == customer_user.pk

    def test_my_profile_for_unlinked_customer_is_404(self, make_client):
        assert make_client(UserFactory(role="CUSTOMER")).get(f"{URL}my-profile/").status_code == 404

    def test_my_profile_is_customer_only(self, make_client, ops, customer_user):
        assert make_client(ops).get(f"{URL}my-profile/").status_code == 403
        response = make_client(customer_user).get(f"{URL}my-profile/")
        assert response.data["id"] == str(customer_user.customer.pk)

    def test_customer_with_financial_history_style_protection_via_protect_fk(self, customer_user):
        from django.db.models import ProtectedError

        with pytest.raises(ProtectedError):
            customer_user.delete()
