"""Python flows are validated here, with fluss-monty: what a version stores is derived, not told.

A client sends the source and the actions it may call, with their ports. The ports of the flow
(its entrypoint's signature), its runtime and its manifest are what the validation derives; a
source that does not check against those actions is refused.

The actions' own ports are the client's word: the server cannot read rekuest's actions. The
executor checks the source again against the real actions before every run, so a manifest
that lies about them fails its runs, never stores a flow that runs something else.
"""

from typing import Any

from fluss_monty import ManifestAction, Port, ValidationReport, validate_python_flow_sync

from reaktion import inputs
from rekuest_core.inputs import models as rimodels


def validate(model: inputs.PythonFlowSourceInputModel) -> ValidationReport:
    """The report of ``model``'s source against its manifest's actions."""
    actions = [ManifestAction(alias=entry.alias, action=entry, effect=entry.effect.value, app=entry.app, key=entry.key, version=entry.version) for entry in model.manifest]
    return validate_python_flow_sync(model.source, actions, entrypoint=model.entrypoint, structures=model.structures)


def refusal(report: ValidationReport) -> str:
    """Why a source is refused, one diagnostic per paragraph."""
    lines = [f"line {d.line}: {d.message}" if d.line else d.message for d in report.diagnostics]
    return "The Python flow does not validate:\n" + "\n\n".join(lines)


def arg_ports(ports: list[Port]) -> list[dict[str, Any]]:
    """Derived arg ports as they are stored (rekuest's arg port shape)."""
    return [rimodels.ArgPortInputModel.model_validate(port.model_dump(mode="json", exclude_defaults=True)).model_dump(mode="json") for port in ports]


def return_ports(ports: list[Port]) -> list[dict[str, Any]]:
    """Derived return ports as they are stored (rekuest's return port shape)."""
    return [rimodels.ReturnPortInputModel.model_validate(port.model_dump(mode="json", exclude_defaults=True, exclude={"default"})).model_dump(mode="json") for port in ports]


def manifest(report: ValidationReport) -> list[dict[str, Any]]:
    """The manifest as it is stored: each action by its hash, without the ports it was checked against."""
    return [entry.model_dump(mode="json") for entry in report.manifest]
