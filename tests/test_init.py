"""Setup/unload/reload behaviour of the integration."""

from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components import hivemind

from .fake_bus import FakeHiveBus

BASE_DATA = {
    "name": "Living Room",
    "host": "ws://127.0.0.1",
    "access_key": "key",
    "password": "pw",
    "port": 5678,
    "site_id": "test",
    "allow_self_signed": False,
}


async def _setup(hass, fake, device_type):
    entry = MockConfigEntry(
        domain="hivemind",
        data={**BASE_DATA, "device_type": device_type},
        entry_id=f"e-{device_type}",
    )
    entry.add_to_hass(hass)
    with patch.object(hivemind, "_build_bus", return_value=fake):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


@pytest.mark.parametrize(
    ("device_type", "expected", "absent"),
    [
        ("agent", {"binary_sensor", "button", "switch"},
         {"media_player", "notify", "select", "sensor"}),
        ("media_player", {"binary_sensor", "button", "switch", "media_player"},
         {"select", "sensor"}),
        ("voice_assistant",
         {"binary_sensor", "button", "switch", "media_player", "sensor", "select"},
         set()),
    ],
)
async def test_platforms_per_device_type(hass, device_type, expected, absent):
    fake = FakeHiveBus()
    await _setup(hass, fake, device_type)
    for platform in expected:
        assert hass.states.async_entity_ids(platform), f"missing {platform}"
    for platform in absent:
        assert not hass.states.async_entity_ids(platform), f"unexpected {platform}"


async def test_stale_legacy_audio_key_is_ignored(hass):
    """Regression: a config entry saved before legacy_audio was retired must
    still set up cleanly, the stored key is simply never read."""
    fake = FakeHiveBus()
    entry = MockConfigEntry(
        domain="hivemind",
        data={**BASE_DATA, "device_type": "media_player", "legacy_audio": True},
        entry_id="e-stale-legacy-audio",
    )
    entry.add_to_hass(hass)
    with patch.object(hivemind, "_build_bus", return_value=fake):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert hass.states.async_entity_ids("media_player")


async def test_unload_closes_bus_and_clears_data(hass):
    fake = FakeHiveBus()
    entry = await _setup(hass, fake, "agent")
    assert hass.data["hivemind"].get(entry.entry_id) is not None

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED
    assert not fake.handshake_event.is_set()  # close() was called
    assert hass.data["hivemind"].get(entry.entry_id) is None


async def test_reload_does_not_duplicate_handlers(hass):
    fake = FakeHiveBus()
    entry = await _setup(hass, fake, "voice_assistant")
    before = fake.handler_count("recognizer_loop:state")
    assert before >= 1

    with patch.object(hivemind, "_build_bus", return_value=fake):
        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

    # handlers removed on unload then re-added once — not stacked
    assert fake.handler_count("recognizer_loop:state") == before
