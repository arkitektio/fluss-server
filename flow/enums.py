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
    AS_COMPLETED = "AS_COMPLETED"
    ORDERED = "ORDERED"


class Scope(graphene.Enum):
    """Scope of the Port"""

    GLOBAL = "GLOBAL"
    LOCAL = "LOCAL"


class ContractStatus(graphene.Enum):
    """Scope of the Port"""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


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

    # Delay
    DELAY = "DELAY", "DELAY (Delay the data)"
    DELAY_UNTIL = "DELAY_UNTIL", "DELAY_UNTIL (Delay the data until signal is send)"

    # Transformation
    CHUNK = "CHUNK", "CHUNK (Chunk the data)"
    SPLIT = "SPLIT", "SPLIT (Split the data)"
    OMIT = "OMIT", "OMIT (Omit the data)"
    ENSURE = "ENSURE", "ENSURE (Ensure the data (discards None in the stream))"

    # Basic Operations
    ADD = "ADD", "ADD (Add a number to the data)"
    SUBTRACT = "SUBTRACT", "SUBTRACT (Subtract a number from the data)"
    MULTIPLY = "MULTIPLY", "MULTIPLY (Multiply the data with a number)"
    DIVIDE = "DIVIDE", "DIVIDE (Divide the data with a number)"
    MODULO = "MODULO", "MODULO (Modulo the data with a number)"
    POWER = "POWER", "POWER (Power the data with a number)"

    # String Operations
    PREFIX = "PREFIX", "PREFIX (Prefix the data with a string)"
    SUFFIX = "SUFFIX", "SUFFIX (Suffix the data with a string)"

    # Filter operations
    FILTER = "FILTER", "FILTER (Filter the data of a union)"

    GATE = "GATE", "GATE (Gate the data, first value is gated, second is gate)"

    TO_LIST = "TO_LIST", "TO_LIST (Convert to list)"

    FOREACH = "FOREACH", "FOREACH (Foreach element in list)"

    IF = "IF", "IF (If condition is met)"
    AND = "AND", "AND (AND condition)"
    ALL = "ALL", "ALL (establish if all values are Trueish)"


EventTypeInput = InputEnum.from_choices(EventType)
ReactiveImplementation = InputEnum.from_choices(ReactiveImplementationModel)
