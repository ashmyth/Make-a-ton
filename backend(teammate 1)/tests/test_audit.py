import pytest
from django.db import DatabaseError, connection, transaction

from apps.audit.models import AppendOnlyError, AuditAction, AuditLog
from apps.audit.services import diff_fields, get_client_ip, record_audit
from tests.factories import UserFactory

AUDIT = "/api/v1/audit/"


@pytest.mark.django_db
class TestAuditApi:
    def test_admin_lists_newest_first_with_actor_email(self, make_client, admin):
        record_audit(action="A_FIRST", actor=admin, entity_type="User", entity_id=admin.pk)
        record_audit(action="B_SECOND", actor=admin, entity_type="User", entity_id=admin.pk)
        rows = make_client(admin).get(AUDIT).data["results"]
        actions = [r["action"] for r in rows if r["action"] in {"A_FIRST", "B_SECOND"}]
        assert actions == ["B_SECOND", "A_FIRST"]
        assert rows[0]["actor_email"] == admin.email

    def test_filters(self, make_client, admin, ops):
        record_audit(action="X_ONE", actor=ops, entity_type="Customer", entity_id="c-1")
        record_audit(action="X_TWO", actor=admin, entity_type="User", entity_id="u-9")
        client = make_client(admin)
        assert client.get(AUDIT, {"action": "X_ONE"}).data["count"] == 1
        assert client.get(AUDIT, {"entity_type": "User", "entity_id": "u-9"}).data["count"] == 1
        assert client.get(AUDIT, {"actor": str(ops.pk), "action": "X_ONE"}).data["count"] == 1
        assert client.get(AUDIT, {"search": ops.email[:8], "action": "X_ONE"}).data["count"] == 1
        assert client.get(AUDIT, {"search": "u-9"}).data["count"] == 1
        assert client.get(AUDIT, {"from": "2999-01-01T00:00:00Z"}).data["count"] == 0
        assert (
            client.get(AUDIT, {"to": "2999-01-01T00:00:00Z", "action": "X_ONE"}).data["count"] == 1
        )

    def test_invalid_filters_return_400(self, make_client, admin):
        client = make_client(admin)
        assert client.get(AUDIT, {"actor": "not-a-uuid"}).status_code == 400
        assert client.get(AUDIT, {"from": "yesterday"}).status_code == 400

    def test_retrieve_single_entry(self, make_client, admin):
        entry = record_audit(action="X_ONE", actor=admin, details={"k": "v"})
        response = make_client(admin).get(f"{AUDIT}{entry.pk}/")
        assert response.status_code == 200
        assert response.data["details"] == {"k": "v"}

    def test_api_is_read_only(self, make_client, admin):
        entry = record_audit(action="X_ONE", actor=admin)
        client = make_client(admin)
        assert client.post(AUDIT, {"action": "FORGED"}, format="json").status_code == 405
        assert client.delete(f"{AUDIT}{entry.pk}/").status_code == 405
        assert client.patch(f"{AUDIT}{entry.pk}/", {}, format="json").status_code == 405


@pytest.mark.django_db
class TestAuditImmutability:
    def test_model_blocks_update_and_delete(self):
        entry = record_audit(action="X_ONE")
        entry.action = "TAMPERED"
        with pytest.raises(AppendOnlyError):
            entry.save()
        with pytest.raises(AppendOnlyError):
            entry.delete()
        with pytest.raises(AppendOnlyError):
            AuditLog.objects.filter(pk=entry.pk).update(action="TAMPERED")
        with pytest.raises(AppendOnlyError):
            AuditLog.objects.filter(pk=entry.pk).delete()

    def test_database_trigger_blocks_raw_sql_tampering(self):
        entry = record_audit(action="X_ONE")
        for sql in (
            "UPDATE brightloop_audit_logs SET action = 'TAMPERED' WHERE id = %s",
            "DELETE FROM brightloop_audit_logs WHERE id = %s",
        ):
            with (
                pytest.raises(DatabaseError, match="append-only"),
                transaction.atomic(),
                connection.cursor() as cursor,
            ):
                cursor.execute(sql, [entry.pk])
        assert AuditLog.objects.get(pk=entry.pk).action == "X_ONE"

    def test_actor_with_history_cannot_be_deleted(self):
        from django.db.models import ProtectedError

        user = UserFactory()
        record_audit(action="X_ONE", actor=user)
        with pytest.raises(ProtectedError):
            user.delete()


class TestAuditServices:
    def test_diff_fields(self):
        assert diff_fields({"a": 1, "b": "x"}, {"a": 2, "b": "x"}) == {"a": [1, 2]}

    def test_client_ip_without_proxy_uses_remote_addr(self, rf, settings):
        settings.TRUSTED_PROXY_COUNT = 0
        request = rf.get("/", REMOTE_ADDR="10.0.0.5", HTTP_X_FORWARDED_FOR="1.2.3.4")
        assert get_client_ip(request) == "10.0.0.5"

    def test_client_ip_behind_one_trusted_proxy_ignores_spoofed_entries(self, rf, settings):
        settings.TRUSTED_PROXY_COUNT = 1
        request = rf.get("/", REMOTE_ADDR="10.0.0.5", HTTP_X_FORWARDED_FOR="6.6.6.6, 203.0.113.7")
        assert get_client_ip(request) == "203.0.113.7"

    def test_client_ip_without_request(self):
        assert get_client_ip(None) is None

    @pytest.mark.django_db
    def test_anonymous_actor_is_stored_as_null(self):
        from django.contrib.auth.models import AnonymousUser

        entry = record_audit(action=AuditAction.LOGIN_FAILED, actor=AnonymousUser())
        assert entry.actor is None


@pytest.mark.django_db
class TestOpenApi:
    def test_docs_and_schema_are_served(self, api):
        assert api.get("/api/docs/").status_code == 200
        schema = api.get("/api/schema/")
        assert schema.status_code == 200
        assert b"/api/v1/customers/{id}/link-portal/" in schema.content
