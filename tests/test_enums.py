"""The GraphQL enum and the database choices for reactive implementations must not drift."""

from reaktion.enums import ReactiveImplementation, ReactiveImplementationChoices


def test_reactive_implementation_choices_match_graphql_enum() -> None:
    """Every implementation the API accepts can be stored, and vice versa."""
    assert {m.value for m in ReactiveImplementation} == {
        m.value for m in ReactiveImplementationChoices
    }
