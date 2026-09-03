"""Smoke test: the integration sets up, exposes entities, and unloads cleanly."""

from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components import hivemind

from .fake_bus import FakeHiveBus

ENTRY_DATA = {
    "device_type": "voice_assistant",
    "name": "Living Room",
    "host": "ws://127.0.0.1",
    "access_key": "key",
    "password": "pw",
    "port": 5678,
    "site_id": "test",
    "allow_self_signed": False,
}


async def _setup(hass, fake):
    entry = MockConfigEntry(domain="hivemind", data=ENTRY_DATA, entry_id="t1")
    entry.add_to_hass(hass)
    with patch.object(hivemind, "_build_bus", return_value=fake):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


async def test_setup_creates_entities_and_unloads(hass):
    fake = FakeHiveBus(connected=True)
    entry = await _setup(hass, fake)

    assert entry.state is ConfigEntryState.LOADED
    # entities across the expected platforms exist
    assert hass.states.async_entity_ids("binary_sensor")
    assert hass.states.async_entity_ids("media_player")
    assert hass.states.async_entity_ids("switch")
    assert hass.states.async_entity_ids("button")
    assert hass.states.async_entity_ids("sensor")
    assert hass.states.async_entity_ids("select")

    # the connection sensor reports connected
    conn = [
        s for s in hass.states.async_all("binary_sensor")
        if "connection" in s.entity_id
    ]
    assert conn and conn[0].state == "on"

    # handlers were registered on the bus
    assert fake.handler_count("ovos.common_play.player.state") >= 1

    # unload removes the entry and every bus handler it registered
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert all(len(v) == 0 for v in fake.handlers.values())
