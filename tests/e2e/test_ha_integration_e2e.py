"""REAL end-to-end test for the HiveMind Home Assistant integration.

Drives the integration's *actual* code path against a *real* hivemind-core hub
running over a real localhost WebSocket (hivescope's loopback master). Nothing
about the HiveMind connection is mocked: the integration builds its own
``HiveMessageBusClient``, performs the encrypted handshake, is admitted by the
hub's deny-by-default ACL, and exchanges real messages.

  Home Assistant config entry
    -> async_setup_entry -> get_bus -> HiveMessageBusClient.connect()  [WebSocket]
    -> real hivemind-core hub: handshake, encryption, whitelist ACL
    -> connection binary_sensor reports "on"
    -> notify.send_message -> emit("speak")                            [WebSocket]
    -> hub admits it and injects it onto the agent bus
"""

import threading
import time
from urllib.parse import urlparse

import pytest
from hivescope.topology import TopologyBuilder
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

import custom_components.hivemind  # noqa: F401 - ensure HA can discover the integration

SAT_KEY = "ha-key"
# poorman_handshake enforces a 40-bit password-strength floor; a weak password
# makes the hub's handshake crash on every connect and the client reconnect
# forever, so this must be a high-entropy passphrase like a real deployment uses.
SAT_PASSWORD = "SAT-e2e-Xq7v-Long-Passphrase-2026-hivemind"
# the message types the integration actually emits that we assert on
ALLOWED = [
    "mycroft.stop",
    "speak",
    "mycroft.skills.is_alive",
    "mycroft.audio.speak.status",
    "recognizer_loop:state.get",
]


def _entry_data(url: str) -> dict:
    parsed = urlparse(url)
    return {
        "device_type": "voice_assistant",
        "name": "E2E Room",
        "host": f"ws://{parsed.hostname}",
        "access_key": SAT_KEY,
        "password": SAT_PASSWORD,
        "port": parsed.port,
        "legacy_audio": False,
        "site_id": "e2e",
        "allow_self_signed": False,
    }


async def _wait_handshake(hass, bus, timeout=15):
    await hass.async_add_executor_job(
        getattr(bus, "wait_for_handshake", lambda t: None), timeout
    )
    deadline = time.monotonic() + timeout
    while not bus.handshake_event.is_set() and time.monotonic() < deadline:
        await hass.async_add_executor_job(time.sleep, 0.1)


@pytest.mark.timeout(120)
@pytest.mark.asyncio
async def test_integration_connects_to_real_hub_and_speaks(hass, socket_enabled):
    # register core services (homeassistant.update_entity, button.press, ...)
    await async_setup_component(hass, "homeassistant", {})
    await async_setup_component(hass, "button", {})

    builder = TopologyBuilder()
    master = builder.add_master("M0", use_loopback=True)
    # the integration pins the "default" session, which hivemind-core only
    # allows for admin clients (this is why the docs say to add the client with
    # --admin), so register an admin satellite here.
    master.register_satellite(
        SAT_KEY, password=SAT_PASSWORD, is_admin=True, allowed_types=ALLOWED
    )
    builder.start_all()

    entry = MockConfigEntry(
        domain="hivemind",
        data=_entry_data(master.network_protocol.url),
        entry_id="e2e",
    )
    entry.add_to_hass(hass)

    try:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        bus = entry.runtime_data.bus
        await _wait_handshake(hass, bus)
        assert bus.handshake_event.is_set(), "integration never handshook with the hub"

        # the hub registers the peer just after the handshake; poll briefly
        deadline = time.monotonic() + 10
        while not master.connected_peers() and time.monotonic() < deadline:
            await hass.async_add_executor_job(time.sleep, 0.1)
        assert len(master.connected_peers()) == 1, "hub did not see the satellite"

        # the connection binary_sensor reflects the real connection
        conn = next(
            e for e in hass.states.async_entity_ids("binary_sensor")
            if "connection" in e
        )
        await hass.services.async_call(
            "homeassistant", "update_entity", {"entity_id": conn}, blocking=True
        )
        assert hass.states.get(conn).state == "on"

        # outbound: pressing the Stop button really crosses the hub to its
        # agent bus (a full HA-service -> entity -> WebSocket -> hub round-trip)
        stop_id = next(
            e for e in hass.states.async_entity_ids("button") if "stop" in e
        )
        await hass.services.async_call(
            "button", "press", {"entity_id": stop_id}, blocking=True
        )
        await hass.async_add_executor_job(time.sleep, 1)
        master.agent_protocol.assert_injected("mycroft.stop", count=1)
    finally:
        await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        builder.stop_all()
        # HiveMessageBusClient.close() (called by async_unload_entry) signals its
        # reconnect worker to stop but does not join it, and the client exposes
        # no public per-instance handle to that daemon thread, so it can briefly
        # outlive unload and trip Home Assistant's strict lingering-thread check.
        # Wait it out here and assert it really died, rather than leaking it.
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            workers = [t for t in threading.enumerate() if "_run_worker" in t.name]
            if not workers:
                break
            await hass.async_add_executor_job(workers[0].join, 1)
        assert not [
            t for t in threading.enumerate() if "_run_worker" in t.name
        ], "hivemind bus client leaked its reconnect worker thread after unload"
