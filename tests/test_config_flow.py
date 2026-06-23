"""Config-flow tests: connection validation, errors, and duplicate guard."""

from unittest.mock import patch

import custom_components.hivemind as hivemind
import custom_components.hivemind.config_flow as config_flow
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .fake_bus import FakeHiveBus

USER_INPUT = {
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


async def _submit(hass, *, handshake_ok=True, raises=False):
    def _fake_validate(data):
        if raises:
            raise ConnectionError("boom")
        return handshake_ok

    result = await hass.config_entries.flow.async_init(
        "hivemind", context={"source": "user"}
    )
    # a completed flow also *sets up* the entry, so stub the runtime bus too
    with (
        patch.object(config_flow, "_try_handshake", side_effect=_fake_validate),
        patch.object(hivemind, "_build_bus", return_value=FakeHiveBus()),
    ):
        out = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
        await hass.async_block_till_done()
    return out


async def test_happy_path_creates_entry(hass):
    result = await _submit(hass, handshake_ok=True)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Living Room"
    assert result["data"]["host"] == "ws://127.0.0.1"


async def test_bad_credentials_show_invalid_auth(hass):
    result = await _submit(hass, handshake_ok=False)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_unreachable_hub_shows_cannot_connect(hass):
    result = await _submit(hass, raises=True)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_duplicate_hub_is_aborted(hass):
    MockConfigEntry(
        domain="hivemind",
        data=USER_INPUT,
        unique_id="ws://127.0.0.1-key",
    ).add_to_hass(hass)

    result = await _submit(hass, handshake_ok=True)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
