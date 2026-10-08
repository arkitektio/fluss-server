from django.db import migrations


def _rewrite(apps, old: str, new: str) -> None:
    PythonFlow = apps.get_model("reaktion", "PythonFlow")
    for flow in PythonFlow.objects.exclude(manifest=[]).iterator():
        manifest = [{**entry, "effect": new} if entry.get("effect") == old else entry for entry in flow.manifest or []]
        if manifest != flow.manifest:
            flow.manifest = manifest
            flow.save(update_fields=["manifest"])


def physical_to_irreversible(apps, schema_editor):
    """A manifest entry's effect is rekuest's Effects now: PHYSICAL is spelled IRREVERSIBLE."""
    _rewrite(apps, "PHYSICAL", "IRREVERSIBLE")


def irreversible_to_physical(apps, schema_editor):
    _rewrite(apps, "IRREVERSIBLE", "PHYSICAL")


class Migration(migrations.Migration):

    dependencies = [
        ("reaktion", "0004_python_flow"),
    ]

    operations = [
        migrations.RunPython(physical_to_irreversible, irreversible_to_physical),
    ]
