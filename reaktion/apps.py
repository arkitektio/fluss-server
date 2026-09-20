from django.apps import AppConfig


class ReaktionConfig(AppConfig):
    """The fluss workflow app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "reaktion"

    def ready(self) -> None:
        """Register the embedding system checks.

        They assert that the model's width, ``EMBEDDINGS.DIMENSIONS`` and the ``vector(N)``
        columns agree; ``migrate`` runs the database-tagged one at every boot, so a mismatch
        stops the service before it serves a wrong search.
        """
        import embeddings.checks  # noqa: F401
