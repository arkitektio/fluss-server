"""fluss's model signals: what it declares to the hub's rekuest, and that a save reaches it signed.

The save goes to a real local HTTP server standing in for rekuest's signal intake, and is
checked the way rekuest checks it (the instance-key JWT, the body).
"""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from joserfc.jwk import OKPKey

from arkitekt_service import trust
from fluss_server.service import service

EXPECTED = {
    "@fluss/flow": [
        "CREATED"
    ],
    "@fluss/pythonflow": [
        "CREATED",
        "UPDATED",
        "DELETED"
    ],
    "@fluss/pythonrun": [
        "CREATED",
        "UPDATED",
        "DELETED"
    ],
    "@fluss/run": [
        "CREATED",
        "UPDATED",
        "DELETED"
    ],
    "@fluss/workspace": [
        "CREATED",
        "UPDATED",
        "DELETED"
    ]
}

KEY = OKPKey.generate_key("Ed25519")


class _Intake:
    def __init__(self) -> None:
        self.received: list[dict] = []
        intake = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                body = self.rfile.read(int(self.headers["Content-Length"]))
                intake.received.append({"path": self.path, "headers": dict(self.headers), "body": body, "json": json.loads(body)})
                self.send_response(202)
                self.end_headers()

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"

    def of(self, identifier: str, count: int = 1, timeout: float = 10) -> list[dict]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            found = [r for r in self.received if r["json"]["identifier"] == identifier]
            if len(found) >= count:
                return found
            time.sleep(0.05)
        return [r for r in self.received if r["json"]["identifier"] == identifier]


@pytest.fixture
def intake(settings):
    server = _Intake()
    settings.REKUEST_SERVICE = {"REKUEST_URL": server.url, "SERVICE": "fluss"}
    settings.INSTANCE = {
        "PRIVATE_KEY": KEY.as_pem(private=True).decode(),
        "TRUST_JWKS": {"keys": [{**trust.public_jwk(KEY), "service": "live.arkitekt.fluss"}]},
    }
    yield server
    server.server.shutdown()


def _organization():
    from authentikate.models import Organization

    return Organization.objects.get_or_create(slug="signals-test-org")[0]


def test_the_manifest_declares_every_model_signal():
    assert {s["identifier"]: s["kinds"] for s in service.manifest()["signals"]} == EXPECTED


def test_the_manifest_lists_what_fluss_hosts_with_its_descriptors():
    hosted = {s["identifier"]: s for s in service.manifest()["structures"]}
    # Everything fluss hosts is signalled.
    assert set(hosted) == set(EXPECTED)
    assert hosted["@fluss/workspace"]["label"] == "Workspace"
    assert hosted["@fluss/workspace"]["descriptors"] == []
    assert [(d["key"], d["type"]) for d in hosted["@fluss/flow"]["descriptors"]] == [
        ("@fluss/version", "STRING"),
        ("@fluss/n_nodes", "INT"),
        ("@fluss/n_edges", "INT"),
        ("@fluss/brittle", "BOOL"),
    ]
    assert {"key": "@fluss/physical", "type": "BOOL", "description": "Whether its source may call an action with a PHYSICAL effect"} in hosted["@fluss/pythonflow"]["descriptors"]
    # A signal carries exactly the keys its structure declares.
    signalled = {s["identifier"]: s["descriptors"] for s in service.manifest()["signals"]}
    assert signalled == {identifier: [d["key"] for d in s["descriptors"]] for identifier, s in hosted.items()}


@pytest.mark.django_db(transaction=True)
def test_a_save_is_signalled_signed_by_this_instance(intake):
    from reaktion.models import Workspace

    org = _organization()
    obj = Workspace.objects.create(title='signalled', organization=org)

    (received,) = intake.of("@fluss/workspace")
    assert (received["json"]["kind"], received["json"]["object"], received["json"]["organization"]) == ("CREATED", str(obj.pk), org.slug)
    assert received["path"] == "/agi/signal/fluss"
    verified = trust.verify("POST", received["path"], received["body"], received["headers"]["Authorization"], audience="live.arkitekt.rekuest")
    assert verified.issuer == "live.arkitekt.fluss"


@pytest.mark.django_db(transaction=True)
def test_publishing_a_python_flow_is_signalled_with_its_status_and_effect(intake):
    from reaktion.models import PythonFlow

    org = _organization()
    flow = PythonFlow.objects.create(
        organization=org, title="moves", source="def main(): pass", runtime="monty-0.1", hash="h",
        manifest=[{"alias": "move_stage", "action_hash": "a", "effect": "PHYSICAL"}],
    )
    flow.status = "PUBLISHED"
    flow.save()

    created, updated = intake.of("@fluss/pythonflow", count=2)
    assert (created["json"]["kind"], created["json"]["object"]) == ("CREATED", str(flow.pk))
    assert updated["json"]["kind"] == "UPDATED"
    assert updated["json"]["descriptors"] == {"@fluss/status": "PUBLISHED", "@fluss/physical": True}
