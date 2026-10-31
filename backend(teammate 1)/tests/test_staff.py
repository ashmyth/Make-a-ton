import pytest

from apps.access_control.roles import UserRole
from apps.accounts.models import User
from apps.audit.models import AuditAction, AuditLog
from tests.factories import PASSWORD, UserFactory
from tests.test_rbac import STAFF, staff_payload

LOGIN = "/api/v1/auth/login/"


@pytest.mark.django_db
class TestStaffManagement:
    def test_create_staff_hashes_password_and_audits(self, make_client, admin):
        response = make_client(admin).post(STAFF, staff_payload(role="FINANCE"), format="json")
        assert response.status_code == 201
        assert response.data["role"] == "FINANCE"
        assert "password" not in response.data
        user = User.objects.get(email="new.ops@example.com")
        assert user.password.startswith("argon2$argon2id$")
        log = AuditLog.objects.get(action=AuditAction.STAFF_CREATED)
        assert log.actor == admin and log.entity_id == str(user.pk)

    def test_new_staff_member_can_sign_in(self, make_client, admin, api):
        make_client(admin).post(STAFF, staff_payload(), format="json")
        response = api.post(
            LOGIN, {"email": "new.ops@example.com", "password": PASSWORD}, format="json"
        )
        assert response.status_code == 200
        assert response.data["role"] == "OPERATIONS"

    @pytest.mark.parametrize("role", ["ADMINISTRATOR", "CUSTOMER", "SUPERUSER"])
    def test_cannot_create_staff_with_other_roles(self, make_client, admin, role):
        response = make_client(admin).post(STAFF, staff_payload(role=role), format="json")
        assert response.status_code == 400
        assert "role" in response.data

    def test_create_rejects_weak_password_and_duplicate_email(self, make_client, admin, ops):
        client = make_client(admin)
        weak = client.post(STAFF, staff_payload(password="weak"), format="json")
        assert weak.status_code == 400 and "password" in weak.data
        dup = client.post(STAFF, staff_payload(email=ops.email.upper()), format="json")
        assert dup.status_code == 400 and "email" in dup.data

    def test_list_excludes_customers_and_supports_filters(
        self, make_client, admin, ops, finance, customer_user
    ):
        client = make_client(admin)
        emails = {row["email"] for row in client.get(STAFF).data["results"]}
        assert emails == {admin.email, ops.email, finance.email}
        only_fin = client.get(STAFF, {"role": "FINANCE"}).data["results"]
        assert [row["email"] for row in only_fin] == [finance.email]
        assert client.get(STAFF, {"search": "OPS@"}).data["count"] == 1
        assert client.get(STAFF, {"is_active": "maybe"}).status_code == 400

    def test_customer_user_not_reachable_through_staff_api(self, make_client, admin, customer_user):
        client = make_client(admin)
        assert client.get(f"{STAFF}{customer_user.pk}/").status_code == 404
        assert client.post(f"{STAFF}{customer_user.pk}/deactivate/").status_code == 404

    def test_update_name_and_role_is_audited_with_diff(self, make_client, admin, ops):
        response = make_client(admin).patch(
            f"{STAFF}{ops.pk}/", {"role": "FINANCE", "first_name": "Renamed"}, format="json"
        )
        assert response.status_code == 200
        ops.refresh_from_db()
        assert ops.role == UserRole.FINANCE and ops.first_name == "Renamed"
        log = AuditLog.objects.get(action=AuditAction.STAFF_UPDATED)
        assert log.details["changes"]["role"] == ["OPERATIONS", "FINANCE"]

    def test_role_change_applies_to_live_session_immediately(self, make_client, admin, ops):
        ops_client = make_client(ops)
        assert ops_client.post("/api/v1/customers/", {}, format="json").status_code == 400
        make_client(admin).patch(f"{STAFF}{ops.pk}/", {"role": "FINANCE"}, format="json")
        assert ops_client.post("/api/v1/customers/", {}, format="json").status_code == 403

    def test_cannot_change_administrator_role_or_own_role(self, make_client, admin):
        other_admin = UserFactory(role=UserRole.ADMINISTRATOR)
        client = make_client(admin)
        assert (
            client.patch(
                f"{STAFF}{other_admin.pk}/", {"role": "FINANCE"}, format="json"
            ).status_code
            == 400
        )
        assert (
            client.patch(f"{STAFF}{admin.pk}/", {"role": "FINANCE"}, format="json").status_code
            == 400
        )
        assert (
            client.patch(f"{STAFF}{admin.pk}/", {"last_name": "Boss"}, format="json").status_code
            == 200
        )

    def test_noop_update_writes_no_audit_entry(self, make_client, admin, ops):
        make_client(admin).patch(f"{STAFF}{ops.pk}/", {"first_name": ops.first_name}, format="json")
        assert not AuditLog.objects.filter(action=AuditAction.STAFF_UPDATED).exists()

    def test_put_and_delete_are_not_allowed(self, make_client, admin, ops):
        client = make_client(admin)
        assert client.delete(f"{STAFF}{ops.pk}/").status_code == 405
        assert client.put(f"{STAFF}{ops.pk}/", {}, format="json").status_code == 405

    def test_admin_can_deactivate_staff_without_deleting_history(self, make_client, admin, ops):
        AuditLog.objects.create(actor=ops, action="SOMETHING_ELSE")
        response = make_client(admin).post(f"{STAFF}{ops.pk}/deactivate/")
        assert response.status_code == 200
        assert response.data["is_active"] is False
        ops.refresh_from_db()
        assert ops.is_active is False
        assert AuditLog.objects.filter(actor=ops).exists()
        log = AuditLog.objects.get(action=AuditAction.STAFF_DEACTIVATED)
        assert log.actor == admin and log.entity_id == str(ops.pk)

    def test_deactivated_staff_cannot_login(self, make_client, admin, ops, api):
        make_client(admin).post(f"{STAFF}{ops.pk}/deactivate/")
        response = api.post(LOGIN, {"email": ops.email, "password": PASSWORD}, format="json")
        assert response.status_code == 401

    def test_deactivation_ends_live_sessions_even_after_reactivation(self, make_client, admin, ops):
        ops_client = make_client(ops)
        assert ops_client.get("/api/v1/auth/me/").status_code == 200
        admin_client = make_client(admin)
        admin_client.post(f"{STAFF}{ops.pk}/deactivate/")
        assert ops_client.get("/api/v1/auth/me/").status_code == 403
        admin_client.post(f"{STAFF}{ops.pk}/activate/")
        assert ops_client.get("/api/v1/auth/me/").status_code == 403

    def test_admin_cannot_deactivate_self(self, make_client, admin):
        response = make_client(admin).post(f"{STAFF}{admin.pk}/deactivate/")
        assert response.status_code == 400
        admin.refresh_from_db()
        assert admin.is_active

    def test_double_deactivate_and_double_activate_conflict(self, make_client, admin, ops):
        client = make_client(admin)
        assert client.post(f"{STAFF}{ops.pk}/activate/").status_code == 409
        client.post(f"{STAFF}{ops.pk}/deactivate/")
        assert client.post(f"{STAFF}{ops.pk}/deactivate/").status_code == 409

    def test_activate_restores_login_and_clears_lockout(self, make_client, admin, ops, api):
        client = make_client(admin)
        client.post(f"{STAFF}{ops.pk}/deactivate/")
        User.objects.filter(pk=ops.pk).update(failed_login_attempts=5)
        response = client.post(f"{STAFF}{ops.pk}/activate/")
        assert response.status_code == 200
        assert AuditLog.objects.filter(action=AuditAction.STAFF_ACTIVATED).count() == 1
        login = api.post(LOGIN, {"email": ops.email, "password": PASSWORD}, format="json")
        assert login.status_code == 200
