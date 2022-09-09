from balder.enum import InputEnum
from django.db.models import TextChoices


class EventType(TextChoices):
    """Variety expresses the Type of Representation we are dealing with"""

    NEXT = "NEXT", "NEXT (Value represent Labels)"
    ERROR = "ERROR", "Error (Value represent Intensity)"
    COMPLETE = "COMPLETE", "COMPLETE (First three channel represent RGB)"
    UNKNOWN = "UNKNOWN", "UNKNOWN (Value represent Intensity)"


class ReactiveImplementationModel(TextChoices):
    # Combination
    ZIP = "ZIP", "ZIP (Zip the data)"
    COMBINELATEST = (
        "COMBINELATEST",
        "COMBINELATEST (Combine values with latest value from each stream)",
    )
    WITHLATEST = (
        "WITHLATEST",
        "WITHLATEST (Combine a leading value with the latest value)",
    )
    BUFFER_COMPLETE = (
        "BUFFER_COMPLETE",
        "BUFFER_COMPLETE (Buffer values until complete is retrieved)",
    )
    BUFFER_UNTIL = (
        "BUFFER_UNTIL",
        "BUFFER_UNTIL (Buffer values until signal is send)",
    )

    # Transformation
    CHUNK = "CHUNK", "CHUNK (Chunk the data)"
    SPLIT = "SPLIT", "SPLIT (Split the data)"
    OMIT = "OMIT", "OMIT (Omit the data)"


EventTypeInput = InputEnum.from_choices(EventType)
ReactiveImplementation = InputEnum.from_choices(ReactiveImplementationModel)
