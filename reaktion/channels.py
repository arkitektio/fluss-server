"""The channels fluss broadcasts on, and the rooms they are keyed by.

``run_event_channel`` carries a run's events to the subscribers of that run (``run_{id}``).
``run_channel`` and ``python_run_channel`` carry the runs themselves: created, changed
(their status) or deleted. Each is broadcast to the organization's room and to the run's own
room, so a list follows every run of the organization and a run's page follows one run. Both
sides build the room names with the functions below, so a publisher and a listener cannot drift
apart.
"""

from kante.channel import CRUDSignal, build_channel

from reaktion.channel_signals import RunEventSignal

run_event_channel = build_channel(RunEventSignal)

run_channel = build_channel(CRUDSignal, name="fluss_run")
python_run_channel = build_channel(CRUDSignal, name="fluss_python_run")


# Room names are written here, not with ``Channel.org_group``: that one joins with ":", which a
# channel layer refuses in a group name (ASCII alphanumerics, hyphens, underscores, periods).


def run_org_group(organization_id: int) -> str:
    """The room of every run of one organization."""
    return f"fluss-run-org-{organization_id}"


def run_group(run_id: int) -> str:
    """The room of one run."""
    return f"fluss-run-{run_id}"


def run_groups(organization_id: int, run_id: int) -> list[str]:
    """The rooms a change of one run goes to: its organization's and its own."""
    return [run_org_group(organization_id), run_group(run_id)]


def python_run_org_group(organization_id: int) -> str:
    """The room of every Python run of one organization."""
    return f"fluss-pyrun-org-{organization_id}"


def python_run_group(run_id: int) -> str:
    """The room of one Python run."""
    return f"fluss-pyrun-{run_id}"


def python_run_groups(organization_id: int, run_id: int) -> list[str]:
    """The rooms a change of one Python run goes to: its organization's and its own."""
    return [python_run_org_group(organization_id), python_run_group(run_id)]
