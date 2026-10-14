"""What fluss's objects say about themselves: the describers ``fluss_server.service`` binds.

Each is stored on the row whenever it is saved (``stored_descriptors``), so a port's ``requires``
is answered by one indexed query and a signal carries what a picker filters on. Everything here
is read off the row itself: a flow's validated graph, a Python flow's derived ports and manifest.
"""

from collections.abc import Mapping, Sequence

from reaktion import enums, models
from rekuest_core.enums import Effects

#: From least to most consequential: a Python flow is as consequential as its worst call.
EFFECT_ORDER = [Effects.NONE.value, Effects.REPEATABLE.value, Effects.UNKNOWN.value, Effects.IRREVERSIBLE.value]

Descriptors = dict[str, int | str | bool | list[str]]
GraphNode = Mapping[str, object]


def _nodes_of(graph: Mapping[str, object] | None, kind: enums.GraphNodeKind) -> list[GraphNode]:
    nodes = (graph or {}).get("nodes") or []
    return [node for node in nodes if isinstance(node, Mapping) and node.get("kind") == kind.value]


def _first_stream(streams: object) -> Sequence[object]:
    """The ports of a node's first stream: what an ARGS node hands on, what a RETURNS node takes."""
    if isinstance(streams, Sequence) and streams and isinstance(streams[0], Sequence):
        return streams[0]
    return []


def flow_descriptors(flow: models.Flow) -> Descriptors:
    """A flow's descriptors, from its validated graph: its size, the kinds of node it runs, and the ports it is called with."""
    graph = flow.graph or {}
    nodes = graph.get("nodes") or []
    args = _nodes_of(graph, enums.GraphNodeKind.ARGS)
    returns = _nodes_of(graph, enums.GraphNodeKind.RETURNS)
    return {
        "@fluss/n_nodes": len(nodes),
        "@fluss/n_edges": len(graph.get("edges") or []),
        "@fluss/n_globals": len(graph.get("globals") or []),
        "@fluss/node_kinds": sorted({str(node["kind"]) for node in nodes if isinstance(node, Mapping) and node.get("kind")}),
        "@fluss/n_args": len(_first_stream(args[0].get("outs"))) if args else 0,
        "@fluss/n_returns": len(_first_stream(returns[0].get("ins"))) if returns else 0,
    }


def python_flow_descriptors(flow: models.PythonFlow) -> Descriptors:
    """A Python flow's descriptors: its lifecycle, the worst effect its manifest allows, and the ports its entrypoint takes and gives."""
    effects = [str(entry.get("effect") or Effects.UNKNOWN.value) for entry in flow.manifest or []]
    worst = max(effects, key=EFFECT_ORDER.index) if effects else Effects.NONE.value
    return {
        "@fluss/status": str(flow.status),
        "@fluss/physical": flow.is_physical,
        "@fluss/effect": worst,
        "@fluss/runtime": flow.runtime,
        "@fluss/n_args": len(flow.args or []),
        "@fluss/n_returns": len(flow.returns or []),
    }


def run_descriptors(run: models.Run | models.PythonRun) -> Descriptors:
    """A run's descriptors: where it stands."""
    return {"@fluss/status": str(run.status)}
