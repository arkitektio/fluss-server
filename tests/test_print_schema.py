"""Smoke tests: the GraphQL schema must render the way client codegen reads it.

No database required -- these only import and render the schema.

``str(schema)`` is deliberately *not* the whole story here. Client codegen
(``pnpm fluss``) reaches the schema two ways, and both convert every input
default back into an AST literal: ``printSchema`` and a full introspection
query that selects ``defaultValue``. A default that cannot be represented as a
literal -- notably an object default such as ``{}`` on a custom scalar -- makes
both of those raise ``Cannot convert value to AST`` while ``str(schema)``
stays happily green, so assert on the codegen paths themselves.
"""

from graphql import get_introspection_query, graphql_sync
from graphql.utilities import print_schema

from fluss_server.schema import schema


def test_print_schema():
    sdl = str(schema)
    print(sdl)  # visible with `pytest -s`
    assert sdl.strip(), "Schema SDL should not be empty"


def test_schema_prints_every_input_default_as_a_literal():
    """``printSchema`` over the whole schema -- the path graphql-codegen uses."""
    sdl = print_schema(schema._schema)
    assert "type Query" in sdl


def test_schema_introspects_with_default_values():
    """Full introspection including ``defaultValue`` -- codegen's other entry point."""
    result = graphql_sync(
        schema._schema,
        get_introspection_query(descriptions=True, input_value_deprecation=True),
    )
    assert not result.errors, result.errors


def test_value_map_inputs_default_to_null_not_an_empty_object():
    """``ValueMap`` is a custom scalar: an ``= {}`` default is unrepresentable in SDL."""
    sdl = print_schema(schema._schema)
    assert "constantsMap: ValueMap = null" in sdl
    assert "globalsMap: ValueMap = null" in sdl
    assert "ValueMap = {}" not in sdl


def test_embedding_columns_stay_out_of_the_schema():
    """The vector columns are storage, not API: no type or input may expose them."""
    from fluss_server.schema import schema

    assert "embedding" not in str(schema).lower()
