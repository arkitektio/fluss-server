"""A definition whose action carries protocol hints is read, not refused.

The vendored ``rekuest_core`` models forbid unknown keys, so a field the rekuest service
learned has to be learned here too.
"""

import pytest
from pydantic import ValidationError

from rekuest_core.inputs.models import DefinitionInputModel


def definition(**fields: object) -> DefinitionInputModel:
    return DefinitionInputModel.model_validate({"key": "attach", "name": "Attach", "kind": "FUNCTION", "args": [], "returns": [], **fields})


def test_an_action_with_protocol_hints_is_read() -> None:
    assert definition(protocols=["on_scene_init"]).protocols == ["on_scene_init"]


def test_an_action_without_hints_has_none() -> None:
    assert definition().protocols == []


def test_a_hint_given_twice_is_refused() -> None:
    with pytest.raises(ValidationError, match="given twice"):
        definition(protocols=["on_scene_init", "on_scene_init"])
