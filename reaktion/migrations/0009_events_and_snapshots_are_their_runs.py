"""A run's events and snapshots name their run: they are part of it, and in a collaboration with it.

The previous release runs on the result: it never writes a row without a run.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reaktion", "0008_runless_events_and_snapshots"),
    ]

    operations = [
        migrations.AlterField(
            model_name="runevent",
            name="run",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="events", to="reaktion.run"),
        ),
        migrations.AlterField(
            model_name="snapshot",
            name="run",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="snapshots", to="reaktion.run"),
        ),
    ]
