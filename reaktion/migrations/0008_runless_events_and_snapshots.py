"""Delete the events and snapshots that name no run, before 0009 makes ``run`` required.

Every writer sets ``run`` (``track``, ``snapshot``), and every read reaches them through
``run__flow__organization``: a row without a run was never written by this service and could
not be read. A migration of its own, so that its deletes are committed before the columns are
altered (Postgres refuses to alter a table with pending trigger events).
"""

from django.db import migrations


def delete_runless(apps, schema_editor):
    apps.get_model("reaktion", "RunEvent").objects.filter(run__isnull=True).delete()
    apps.get_model("reaktion", "Snapshot").objects.filter(run__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("reaktion", "0007_python_status_choices"),
    ]

    operations = [
        migrations.RunPython(delete_runless, migrations.RunPython.noop),
    ]
