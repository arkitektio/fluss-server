"""Workspaces and flows embed their title + description (pgvector) for the semantic ``search``.

``VectorExtension`` creates ``vector`` in this database. ``makemigrations`` cannot emit it --
re-add it by hand if this history is ever regenerated -- and the test suite never runs it
(schema is built with run-syncdb; ``tests/conftest.py`` installs the extension itself). It only
runs on a real ``migrate``: a no-op where the daten init script already created it, a loud
failure on a daten image without pgvector, which is the right place to fail.

The backfill embeds every existing row in this transaction. That is cheap (a static model,
~1 ms a row) and means search works the moment the release is up; the in-process healer
(``embeddings.healer``, started from ``fluss_server/asgi.py``) would otherwise do it within a
sweep.
"""

from typing import Any

import pgvector.django.vector
from django.conf import settings
from django.db import migrations, models
from pgvector.django import VectorExtension

BATCH = 500
EMBEDDED = ("Workspace", "Flow")


def backfill_embeddings(apps: Any, schema_editor: Any) -> None:
    """Embed every workspace / flow that has text, with the configured model; no-op when disabled."""
    from embeddings import engine

    if not engine.enabled():
        return
    current = engine.model_id()
    for model_name in EMBEDDED:
        model = apps.get_model("reaktion", model_name)
        queryset = model.objects.exclude(embedding_model=current).order_by("pk").only("pk", "title", "description")
        while True:
            rows = list(queryset[:BATCH])
            if not rows:
                break
            sources = [engine.source_text(row.title, row.description) for row in rows]
            vectors = iter(engine.embed_texts([source for source in sources if source is not None]))
            for row, source in zip(rows, sources, strict=True):
                row.embedding = next(vectors) if source is not None else None
                row.embedding_model = current
            model.objects.bulk_update(rows, ["embedding", "embedding_model"])


class Migration(migrations.Migration):
    """Extension, the columns on two models, the healer's indexes, and the backfill."""

    dependencies = [
        ("authentikate", "0006_alter_app_identifier_alter_release_unique_together"),
        ("reaktion", "0002_reactive_implementation_select_just"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        VectorExtension(),
        migrations.AddField(
            model_name="flow",
            name="embedding",
            field=pgvector.django.vector.VectorField(blank=True, dimensions=256, editable=False, help_text="Unit-length embedding of name + description, by the model named in embedding_model; NULL when there is no text to embed", null=True),
        ),
        migrations.AddField(
            model_name="flow",
            name="embedding_model",
            field=models.CharField(blank=True, default="", editable=False, help_text="The embedding model that produced `embedding`. Rows whose value differs from the configured model are re-embedded in-process and are excluded from vector search until then", max_length=200),
        ),
        migrations.AddField(
            model_name="workspace",
            name="embedding",
            field=pgvector.django.vector.VectorField(blank=True, dimensions=256, editable=False, help_text="Unit-length embedding of name + description, by the model named in embedding_model; NULL when there is no text to embed", null=True),
        ),
        migrations.AddField(
            model_name="workspace",
            name="embedding_model",
            field=models.CharField(blank=True, default="", editable=False, help_text="The embedding model that produced `embedding`. Rows whose value differs from the configured model are re-embedded in-process and are excluded from vector search until then", max_length=200),
        ),
        migrations.AddIndex(
            model_name="flow",
            index=models.Index(fields=["embedding_model"], name="flow_emb_model_idx"),
        ),
        migrations.AddIndex(
            model_name="workspace",
            index=models.Index(fields=["embedding_model"], name="workspace_emb_model_idx"),
        ),
        migrations.RunPython(backfill_embeddings, migrations.RunPython.noop),
    ]
