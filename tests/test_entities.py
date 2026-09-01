"""Entity state-handler logic and regressions for the fixed bugs."""

import asyncio
from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components import hivemind
from custom_components.hivemind.button import HiveMindConnectionButton

from .fake_bus import FakeHiveBus

DATA = {
    "device_type": "voice_assistant",
    "name": "Living Room",
    "host": "ws://127.0.0.1",
    "access_key": "key",
    "password": "pw",
    "port": 5678,
    "legacy_audio": False,
    "site_id": "test",
    "allow_self_signed": False,
}


async def _setup(hass, fake):
    entry = MockConfigEntry(domain="hivemind", data=DATA, entry_id="ent")
    entry.add_to_hass(hass)
    with patch.object(hivemind, "_build_bus", return_value=fake):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


def _one(hass, platform):
    ids = hass.states.async_entity_ids(platform)
    assert ids, f"no {platform} entity"
    return ids[0]


async def test_track_info_keeps_artist_and_album_separate(hass):
    """Regression: album used to overwrite the artist field."""
    fake = FakeHiveBus()
    await _setup(hass, fake)
    mp = _one(hass, "media_player")

    fake.inject(
        "ovos.common_play.track_info.response",
        {"title": "Song", "artist": "The Artist", "album": "The Album"},
    )
    await hass.async_block_till_done()

    attrs = hass.states.get(mp).attributes
    assert attrs.get("media_artist") == "The Artist"
    assert attrs.get("media_album_name") == "The Album"


async def test_player_state_maps_to_media_state(hass):
    fake = FakeHiveBus()
    await _setup(hass, fake)
    mp = _one(hass, "media_player")

    from ovos_utils.ocp import PlayerState

    fake.inject("ovos.common_play.player.state", {"state": PlayerState.PLAYING})
    await hass.async_block_till_done()
    assert hass.states.get(mp).state == "playing"


async def test_malformed_ocp_status_does_not_raise(hass):
    """Regression: handlers used message.data[...] and raised KeyError."""
    fake = FakeHiveBus()
    await _setup(hass, fake)
    # empty payloads must not blow up any handler
    for event in (
        "ovos.common_play.player.status.response",
        "ovos.common_play.media.state",
        "ovos.common_play.get_track_length.response",
        "mycroft.volume.get.response",
    ):
        fake.inject(event, {})
    await hass.async_block_till_done()


async def test_listener_sensor_has_no_state_class_and_updates(hass):
    """Regression: an enum sensor must not carry a MEASUREMENT state_class."""
    fake = FakeHiveBus()
    await _setup(hass, fake)
    sensor = _one(hass, "sensor")

    state = hass.states.get(sensor)
    assert state.attributes.get("state_class") is None
    assert state.attributes.get("device_class") == "enum"

    fake.inject("recognizer_loop:state", {"state": "continuous"})
    await hass.async_block_till_done()
    assert hass.states.get(sensor).state == "continuous"


async def test_alive_sensor_reflects_status(hass):
    fake = FakeHiveBus()
    await _setup(hass, fake)

    skills_alive = [
        e for e in hass.states.async_entity_ids("binary_sensor")
        if "ovos_core_alive" in e or "alive" in e
    ]
    assert skills_alive
    # fire an is_alive response for every alive sensor's service
    for event in list(fake.handlers):
        if event.endswith("is_alive.response"):
            fake.inject(event, {"status": True})
    await hass.async_block_till_done()
    assert any(hass.states.get(e).state == "on" for e in skills_alive)


async def test_connection_sensor_available_even_when_disconnected(hass):
    fake = FakeHiveBus(connected=False)
    await _setup(hass, fake)
    conn = [
        e for e in hass.states.async_entity_ids("binary_sensor")
        if "connection" in e
    ]
    assert conn
    # not "unavailable": the connectivity sensor stays visible, just off
    assert hass.states.get(conn[0]).state == "off"


def test_reconnect_button_is_async():
    """Regression: the reconnect press ran blocking I/O on the event loop."""
    assert asyncio.iscoroutinefunction(HiveMindConnectionButton.async_press)
