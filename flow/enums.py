from balder.enum import InputEnum
from django.db.models import TextChoices
import graphene


class EventType(TextChoices):
    """Event Type for the Event Operator"""

    NEXT = "NEXT", "NEXT (Value represent Item)"
    ERROR = "ERROR", "Error (Value represent Exception)"
    COMPLETE = "COMPLETE", "COMPLETE (Value is none)"
    UNKNOWN = "UNKNOWN", "UNKNOWN (Should never be used)"


class MapStrategy(graphene.Enum):
    """Maping Strategy for the Map Operator"""

    MAP = "MAP"
    MERGEMAP = "MERGEMAP"
    SWITCHMAP = "SWITCHMAP"
    CONCATMAP = "CONCATMAP"


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

    TO_LIST = "TO_LIST", "TO_LIST (Convert to list)"

    FOREACH = "FOREACH", "FOREACH (Foreach element in list)"

    IF = "IF", "IF (If condition is met)"
    AND = "AND", "AND (AND condition)"


EventTypeInput = InputEnum.from_choices(EventType)
ReactiveImplementation = InputEnum.from_choices(ReactiveImplementationModel)
