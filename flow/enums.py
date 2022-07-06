from balder.enum import InputEnum
from django.db.models import TextChoices


class EventType(TextChoices):
    """Variety expresses the Type of Representation we are dealing with"""

    NEXT = "NEXT", "NEXT (Value represent Labels)"
    ERROR = "ERROR", "Error (Value represent Intensity)"
    COMPLETE = "COMPLETE", "COMPLETE (First three channel represent RGB)"
    UNKNOWN = "UNKNOWN", "UNKNOWN (Value represent Intensity)"


EventTypeInput = InputEnum.from_choices(EventType)
