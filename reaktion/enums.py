from enum import Enum
import strawberry
from django.db.models import TextChoices


class RunEventKindChoices(TextChoices):
    """Event Type for the Event Operator"""

    NEXT = "NEXT", "NEXT (Value represent Item)"
    ERROR = "ERROR", "Error (Value represent Exception)"
    COMPLETE = "COMPLETE", "COMPLETE (Value is none)"
    UNKNOWN = "UNKNOWN", "UNKNOWN (Should never be used)"


class PythonFlowStatusChoices(TextChoices):
    DRAFT = "DRAFT", "DRAFT (Stored, not registered as an action)"
    PUBLISHED = "PUBLISHED", "PUBLISHED (Registered as an action)"
    ARCHIVED = "ARCHIVED", "ARCHIVED (No longer registered; kept for its runs)"


class PythonRunStatusChoices(TextChoices):
    RUNNING = "RUNNING", "RUNNING"
    COMPLETED = "COMPLETED", "COMPLETED"
    FAILED = "FAILED", "FAILED"


class ReactiveImplementationChoices(TextChoices):
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
    BUFFER_COUNT = ("BUFFER_COUNT", "BUFFER_COUNT (Butffer values until the count is reacht)")

    # Delay
    DELAY = "DELAY", "DELAY (Delay the data)"
    DELAY_UNTIL = "DELAY_UNTIL", "DELAY_UNTIL (Delay the data until signal is send)"

    # Transformation
    CHUNK = "CHUNK", "CHUNK (Chunk the data)"
    SPLIT = "SPLIT", "SPLIT (Split the data)"
    OMIT = "OMIT", "OMIT (Omit the data)"
    ENSURE = "ENSURE", "ENSURE (Ensure the data (discards None in the stream))"
    SELECT = "SELECT", "SELECT (Select a key from the data)"

    # Basic Operations
    ADD = "ADD", "ADD (Add a number to the data)"
    SUBTRACT = "SUBTRACT", "SUBTRACT (Subtract a number from the data)"
    MULTIPLY = "MULTIPLY", "MULTIPLY (Multiply the data with a number)"
    DIVIDE = "DIVIDE", "DIVIDE (Divide the data with a number)"
    MODULO = "MODULO", "MODULO (Modulo the data with a number)"
    POWER = "POWER", "POWER (Power the data with a number)"
    JUST = "JUST", "JUST (Emit a constant value)"

    # String Operations
    PREFIX = "PREFIX", "PREFIX (Prefix the data with a string)"
    SUFFIX = "SUFFIX", "SUFFIX (Suffix the data with a string)"

    # Filter operations
    FILTER = "FILTER", "FILTER (Filter the data of a union)"

    # Roarder
    REORDER = "REORDER", "REORDER (Reorder the data)"

    GATE = "GATE", "GATE (Gate the data, first value is gated, second is gate)"

    TO_LIST = "TO_LIST", "TO_LIST (Convert to list)"

    FOREACH = "FOREACH", "FOREACH (Foreach element in list)"

    IF = "IF", "IF (If condition is met)"
    AND = "AND", "AND (AND condition)"
    ALL = "ALL", "ALL (establish if all values are Trueish)"


@strawberry.enum
class RunEventKind(str, Enum):
    """Event Type for the Event Operator"""

    NEXT = "NEXT"
    ERROR = "ERROR"
    COMPLETE = "COMPLETE"
    UNKNOWN = "UNKNOWN"


@strawberry.enum
class RunStatus(str, Enum):
    """Event Type for the Event Operator"""

    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"


@strawberry.enum
class GraphNodeKind(str, Enum):
    """Event Type for the Event Operator"""

    REACTIVE = "REACTIVE"
    ARGS = "ARGS"
    RETURNS = "RETURNS"
    REKUEST = "REKUEST_MAP"
    REKUEST_FILTER = "REKUEST_FILTER"
    AGENT_SUBFLOW = "AGENT_SUBFLOW"


@strawberry.enum
class ReactiveImplementation(str, Enum):
    """Reactive Node Kind"""

    # Combination
    ZIP = "ZIP"
    COMBINELATEST = "COMBINELATEST"
    WITHLATEST = "WITHLATEST"

    # Buffer
    BUFFER_COMPLETE = "BUFFER_COMPLETE"
    BUFFER_UNTIL = "BUFFER_UNTIL"
    BUFFER_COUNT = "BUFFER_COUNT"

    # Delay
    DELAY = "DELAY"
    DELAY_UNTIL = "DELAY_UNTIL"

    # Transformation
    CHUNK = "CHUNK"
    SPLIT = "SPLIT"
    OMIT = "OMIT"
    ENSURE = "ENSURE"
    SELECT = "SELECT"

    # Basic Operations
    ADD = "ADD"
    SUBTRACT = "SUBTRACT"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    MODULO = "MODULO"
    POWER = "POWER"

    # JUST
    JUST = "JUST"

    # String Operations
    PREFIX = "PREFIX"
    SUFFIX = "SUFFIX"

    # Filter operations
    FILTER = "FILTER"

    GATE = "GATE"

    TO_LIST = "TO_LIST"

    # Reorder
    REORDER = "REORDER"

    FOREACH = "FOREACH"

    IF = "IF"
    AND = "AND"
    ALL = "ALL"


@strawberry.enum
class MapStrategy(str, Enum):
    """Map Strategy for Arkitekt"""

    MAP = "MAP"
    MAP_TO = "MAP_TO"
    MAP_FROM = "MAP_FROM"


@strawberry.enum
class ContractStatus(str, Enum):
    """Scope of the Posrts"""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


@strawberry.enum
class GraphEdgeKind(str, Enum):
    """Scope of the Posrt"""

    VANILLA = "VANILLA"
    LOGGING = "LOGGING"


@strawberry.enum
class DemandKind(str, Enum):
    """Scope of the Posrt"""

    ARGS = "args"
    RETURNS = "returns"


@strawberry.enum(description="The lifecycle of a PythonFlow version: only PUBLISHED versions are registered as actions.")
class PythonFlowStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


@strawberry.enum(description="The status of a PythonRun.")
class PythonRunStatus(str, Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
