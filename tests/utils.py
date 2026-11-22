import os
from collections.abc import Awaitable, Mapping
from typing import Any, Protocol

from kante.context import HttpContext
from strawberry.types import ExecutionResult

from reaktion.models import Flow, ReactiveTemplate, Run, Snapshot, Trace, Workspace


def build_relative_dir(path: str) -> str:
    """Build a relative directory from a path

    Parameters
    ----------
    path : str
        The path to build a relative directory from

    Returns
    -------
    str
        The relative directory
    """
    return os.path.join(os.path.dirname(__file__), path)


class AExecute(Protocol):
    """The ``aexecute`` fixture: a GraphQL document run against the schema."""

    def __call__(
        self,
        query: str,
        variables: Mapping[str, object] | None = None,
        context: HttpContext | None = None,
    ) -> Awaitable[ExecutionResult]: ...


class MakeWorkspace(Protocol):
    """The ``make_workspace`` fixture."""

    def __call__(
        self, context: HttpContext | None = None, title: str = "Workspace"
    ) -> Awaitable[Workspace]: ...


class MakeFlow(Protocol):
    """The ``make_flow`` fixture."""

    def __call__(
        self,
        context: HttpContext | None = None,
        workspace: Workspace | None = None,
        title: str = "Flow",
        graph: Mapping[str, object] | None = None,
    ) -> Awaitable[Flow]: ...


class MakeRun(Protocol):
    """The ``make_run`` fixture."""

    def __call__(
        self,
        context: HttpContext | None = None,
        flow: Flow | None = None,
        task_id: str | None = None,
    ) -> Awaitable[Run]: ...


class MakeSnapshot(Protocol):
    """The ``make_snapshot`` fixture."""

    def __call__(self, run: Run, t: int = 0) -> Awaitable[Snapshot]: ...


class MakeReactiveTemplate(Protocol):
    """The ``make_reactive_template`` fixture."""

    def __call__(
        self,
        title: str | None = None,
        description: str | None = None,
        implementation: str = "ZIP",
    ) -> Awaitable[ReactiveTemplate]: ...


class MakeTrace(Protocol):
    """The ``make_trace`` fixture."""

    def __call__(
        self,
        context: HttpContext | None = None,
        flow: Flow | None = None,
        provision: Mapping[str, object] | None = None,
    ) -> Awaitable[Trace]: ...


def data_of(result: ExecutionResult) -> dict[str, Any]:
    """``result.data``, asserted present (strawberry types it ``dict[str, Any] | None``)."""
    assert result.data is not None, result.errors
    return result.data
