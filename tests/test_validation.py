"""Config-flow validation defects surfaced by a live Home Assistant e2e run.

Covers three things the throwaway-connection validation used to get wrong:

* a wrong password must fail fast (bounded handshake retries) instead of
  reconnecting forever and hanging the flow, and the client must be torn down;
* validation must reuse the persistent per-access-key identity, so the Noise
  static key it pins is the one the runtime connection uses;
* a single ``on_mycroft`` registration must dispatch each inbound reply once.
"""

from unittest.mock import patch

from hivemind_bus_client.client import HiveMessageBusClient
from hivemind_bus_client.message import HiveMessage, HiveMessageType
from ovos_bus_client.message import Message

from custom_components import hivemind
from custom_components.hivemind import _build_bus, _connect, _identity_path, config_flow

DATA = {
    "device_type": "voice_assistant",
    "name": "Living Room",
    "host": "ws://127.0.0.1",
    "access_key": "0123456789abcdef",
    "password": "wrong-password",
    "port": 5678,
    "legacy_audio": False,
    "site_id": "test",
    "allow_self_signed": False,
}


def test_wrong_password_bounds_handshake_and_closes(hass):
    """A never-completing handshake returns False promptly and closes the bus.

    On v3 Noise a wrong password makes the hub close the socket cleanly, so the
    client never trips ``_auth_rejected`` and an unbounded wait would reconnect
    forever. ``_try_handshake`` must pass a bounded ``max_retries`` through
    ``connect()`` and tear the client down.
    """
    seen = {}

    def _fake_wait(self, timeout=5, max_retries=None):
        seen["max_retries"] = max_retries
        # simulate the bounded loop giving up (never handshakes)
        raise RuntimeError("timed out waiting for handshake")

    with (
        patch.object(HiveMessageBusClient, "run_in_thread", lambda self: None),
        patch.object(HiveMessageBusClient, "wait_for_handshake", _fake_wait),
        patch.object(HiveMessageBusClient, "close") as close,
    ):
        path = _identity_path(hass, DATA["access_key"])
        ok = config_flow._try_handshake(DATA, path)

    assert ok is False
    assert seen["max_retries"] == 1, "handshake wait must be bounded, not infinite"
    assert close.called, "the validation client must be closed on failure"


async def test_validation_uses_persistent_identity_not_throwaway(hass):
    """Validation must build its client with the entry's persistent identity."""
    captured = {}

    def _spy_build(identity_file, data):
        captured["identity_file"] = identity_file
        return _build_bus(identity_file, data)

    with (
        patch.object(hivemind, "_build_bus", side_effect=_spy_build),
        patch.object(config_flow, "_build_bus", side_effect=_spy_build),
        patch.object(HiveMessageBusClient, "run_in_thread", lambda self: None),
        patch.object(
            HiveMessageBusClient, "wait_for_handshake", lambda self, *a, **k: True
        ),
        patch.object(HiveMessageBusClient, "close", lambda self: None),
    ):
        await config_flow.validate_connection(hass, DATA)

    # the identity used to validate is the persistent per-access-key path the
    # runtime connection will reuse, not a throwaway tempdir
    expected = _identity_path(hass, DATA["access_key"])
    assert captured["identity_file"] == expected


def test_single_registration_dispatches_inbound_once(monkeypatch, tmp_path):
    """One ``on_mycroft`` registration handles each inbound BUS reply exactly once."""
    monkeypatch.setattr(HiveMessageBusClient, "run_in_thread", lambda self: None)
    monkeypatch.setattr(
        HiveMessageBusClient, "wait_for_handshake", lambda self, *a, **k: True
    )

    bus = _build_bus(str(tmp_path / "_identity.json"), DATA)
    calls = []
    bus.on_mycroft("recognizer_loop:state", calls.append)

    _connect(bus)

    bus.protocol.handle_bus(
        HiveMessage(HiveMessageType.BUS, Message("recognizer_loop:state", {"mode": 1}))
    )

    assert len(calls) == 1, f"inbound reply dispatched {len(calls)} times, expected 1"
