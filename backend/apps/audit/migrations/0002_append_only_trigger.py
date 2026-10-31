from django.db import migrations

CREATE_PG = """
CREATE OR REPLACE FUNCTION brightloop_audit_logs_append_only() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'brightloop_audit_logs is append-only';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER brightloop_audit_logs_immutable
BEFORE UPDATE OR DELETE ON brightloop_audit_logs
FOR EACH ROW EXECUTE FUNCTION brightloop_audit_logs_append_only();
"""

DROP_PG = """
DROP TRIGGER IF EXISTS brightloop_audit_logs_immutable ON brightloop_audit_logs;
DROP FUNCTION IF EXISTS brightloop_audit_logs_append_only();
"""

CREATE_SQLITE_UPDATE = """
CREATE TRIGGER IF NOT EXISTS brightloop_audit_logs_no_update
BEFORE UPDATE ON brightloop_audit_logs
BEGIN
    SELECT RAISE(ABORT, 'brightloop_audit_logs is append-only');
END;
"""

CREATE_SQLITE_DELETE = """
CREATE TRIGGER IF NOT EXISTS brightloop_audit_logs_no_delete
BEFORE DELETE ON brightloop_audit_logs
BEGIN
    SELECT RAISE(ABORT, 'brightloop_audit_logs is append-only');
END;
"""

DROP_SQLITE_UPDATE = "DROP TRIGGER IF EXISTS brightloop_audit_logs_no_update;"
DROP_SQLITE_DELETE = "DROP TRIGGER IF EXISTS brightloop_audit_logs_no_delete;"


def apply_trigger(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(CREATE_PG)
    elif schema_editor.connection.vendor == "sqlite":
        schema_editor.execute(CREATE_SQLITE_UPDATE)
        schema_editor.execute(CREATE_SQLITE_DELETE)


def remove_trigger(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(DROP_PG)
    elif schema_editor.connection.vendor == "sqlite":
        schema_editor.execute(DROP_SQLITE_UPDATE)
        schema_editor.execute(DROP_SQLITE_DELETE)


class Migration(migrations.Migration):
    dependencies = [("audit", "0001_initial")]
    operations = [migrations.RunPython(apply_trigger, reverse_code=remove_trigger)]
