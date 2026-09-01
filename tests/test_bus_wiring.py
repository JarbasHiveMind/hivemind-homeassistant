"""The connection must bind the client's own internal bus.

Entities register their handlers with ``on_mycroft``, which lands them on
``bus.internal_bus``. If ``connect()`` binds a different (default) internal bus,
inbound BUS replies are dispatched to a bus nobody listens to and every
status entity stays blind. This exercises the real ``hivemind_bus_client``
rather than the test double, since the defect lives in how the two buses are
wired together.
"""

from hivemind_bus_client.client import HiveMessageBusClient
from hivemind_bus_client.message import HiveMessage, HiveMessageType
from ovos_bus_client.message import Message

from custom_components.hivemind import _build_bus, _connect

CONFIG = {
    "access_key": "0123456789abcdef",
    "password": "pw",
    "host": "localhost",
    "port": 5678,
    "site_id": "test",
    "name": "Home Assistant",
}


def test_connect_routes_inbound_messages_to_registered_handlers(monkeypatch, tmp_path):
    # keep connect() off the network: no worker thread, handshake "succeeds"
    monkeypatch.setattr(HiveMessageBusClient, "run_in_thread", lambda self: None)
    monkeypatch.setattr(
        HiveMessageBusClient, "wait_for_handshake", lambda self, *a, **k: True
    )

    bus = _build_bus(str(tmp_path / "_identity.json"), CONFIG)
    received = []
    bus.on_mycroft("recognizer_loop:state", received.append)

    _connect(bus)

    bus.protocol.handle_bus(
        HiveMessage(HiveMessageType.BUS, Message("recognizer_loop:state", {"mode": 1}))
    )

    assert received, "on_mycroft handler never saw the injected bus message"
