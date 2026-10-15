from kante.types import Info

from reaktion import inputs, python_flows, types


def validate_python_flow(info: Info, input: inputs.PythonFlowSourceInput) -> types.PythonFlowValidation:
    """Check a source against the actions it may call, as createPythonFlow would; nothing is stored."""
    report = python_flows.validate(input.to_pydantic())
    return types.PythonFlowValidation(
        ok=report.ok,
        diagnostics=[types.PythonFlowDiagnostic(message=d.message, line=d.line) for d in report.diagnostics],
        stubs=report.stubs,
        runtime=report.runtime,
        stored_args=python_flows.arg_ports(report.args),
        stored_returns=python_flows.return_ports(report.returns),
    )
