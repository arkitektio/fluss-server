# fluss-server

The workflow service of an [Arkitekt](https://arkitekt.live) hub. It stores workflows built
over the hub's actions, and the record of their runs. It does not execute anything: a flow
runs in an agent, as a rekuest task, and that agent reports each step back here. It is
registered as `live.arkitekt.fluss` and has a python client,
[`fluss`](https://github.com/arkitektio/fluss).

## What it stores

| Concept | What it is |
| --- | --- |
| `Workspace` | The container users edit one flow in. |
| `Flow` | One version of a workspace's graph: nodes and edges over actions. |
| `ReactiveTemplate` | The shared catalog of reactive operators a graph can use. |
| `Run`, `RunEvent`, `Snapshot` | One execution of a flow for a rekuest task, each value, error and completion it produced, and its state at a logical time. |
| `PythonFlow` | One immutable version of a flow written as Python source. Versions share a lineage and go through DRAFT, PUBLISHED and ARCHIVED. |
| `PythonRun` | One execution of a published Python flow. Its step-by-step history is the rekuest task tree, not a table here. |

Everything but the reactive templates (one shared catalog) belongs to an organization, and
every read and write is scoped to the caller's.
Workspaces, flows and Python flows are embedded (title and description) for semantic search.

## API

GraphQL is served at `/graphql` (HTTP and WebSocket), with the SDL at `/schema`.

| Operations | What they do |
| --- | --- |
| `createWorkspace`, `updateWorkspace` | Create a workspace with its first flow; save a graph, which upserts the flow for it. |
| `createRun`, `track`, `snapshot`, `closeRun`, `deleteRun` | The lifecycle an executing agent drives: start (or reuse) the run for a task, record each event, capture state, finish. |
| `createPythonFlow`, `updatePythonFlow`, `publishPythonFlow`, `archivePythonFlow`, `deletePythonFlow` | Version a Python flow. Publishing registers it as an action; only drafts can be deleted. |
| `createPythonRun`, `closePythonRun` | Start and finish the run of a published Python flow. |
| `workspaces`, `flow`, `run`, `runForTask`, `pythonFlows`, `pythonRuns`, `reactiveTemplates` | The stored rows. |
| `eventsBetween` | A run's events between two logical times, seeded from the latest snapshot before the lower bound. |
| `events` (subscription) | The live event stream of a run. |

## Hub integration

Declared in [`fluss_server/contract.py`](fluss_server/contract.py):

- **Scopes**: `fluss_read`, `fluss_write`, `fluss_execute`, `read`, `write`.
- **Roles**: `admin`, `user`, `designer`, `viewer`.
- **Needs**: rekuest 6 or newer, an instance key, tokens issued by lok.

fluss is known to the hub's rekuest in two separate ways:

- as a **service** (`_rekuest/service`): it hosts the structures `@fluss/workspace`,
  `@fluss/flow`, `@fluss/run`, `@fluss/pythonflow` and `@fluss/pythonrun`, and announces
  saves and deletes as signals
  ([`fluss_server/service.py`](fluss_server/service.py));
- as a **hook agent** (`_rekuest/hook`): it offers one action, `reembed_stale`
  ([`fluss_server/hook_agent.py`](fluss_server/hook_agent.py)).

The action is only offered. Nothing in this service loops or schedules; whether and when it
runs is the organization's own automation in rekuest.

## Running

The image is `jhnnsrs/fluss`. It has no default command, and starting it takes two steps:

```sh
arkitekt-service run migrate   # wait for the database, apply migrations
arkitekt-service serve                          # serve on :80 (daphne), and nothing else
```

`arkitekt-service debug` does both in one go with Django's autoreloading server, for development.

It needs Postgres with pgvector ([`jhnnsrs/daten`](https://github.com/arkitektio/daten-server))
and Redis. The embedding model is baked into the image.

## Configuration

The service reads `config.yaml`, or the file named by `ARKITEKT_CONFIG_FILE`; any value can
be overridden by an environment variable (`POSTGRES__HOST`). `python manage.py
validate_settings` prints the configuration as the service reads it, with secrets redacted.

See [CONFIG.md](CONFIG.md) for every value.

## Development

```sh
uv sync
uv run pytest
```

The suite runs against a real stack, brought up by [dokker](https://github.com/jhnnsrs/dokker)
from `tests/integration/docker-compose.yaml`: Postgres (`jhnnsrs/daten:next`, override with
`DATEN_IMAGE`) and Redis, on ports Docker picks. It needs a running Docker daemon.

## Releases

Releases are tags: a push to `main` cuts a stable version, a push to `next` a release
candidate. Each one publishes `jhnnsrs/fluss` under its version (`X.Y.Z`, `X.Y`, `X`), plus
`latest` from `main` and `next` from `next`. The `version` in `pyproject.toml` is a
placeholder. Release notes are on
[GitHub Releases](https://github.com/arkitektio/fluss-server/releases); `CHANGELOG.md` is
frozen.
