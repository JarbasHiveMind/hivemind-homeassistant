"""Config-flow tests: connection validation, errors, and duplicate guard."""

from unittest.mock import patch

from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components import hivemind
from custom_components.hivemind import config_flow

from .fake_bus import FakeHiveBus

USER_INPUT = {
    "device_type": "voice_assistant",
    "name": "Living Room",
    "host": "ws://127.0.0.1",
    "access_key": "key",
    "password": "pw",
    "port": 5678,
    "site_id": "test",
    "allow_self_signed": False,
}


async def _submit(hass, *, handshake_ok=True, raises=False, user_input=None, seen=None):
    def _fake_validate(data, identity_file):
        if seen is not None:
            seen.append(data)
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
            result["flow_id"], USER_INPUT if user_input is None else user_input
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


async def test_error_preserves_entered_values_except_password(hass):
    result = await _submit(hass, handshake_ok=False)
    assert result["type"] is FlowResultType.FORM

    schema = result["data_schema"].schema
    suggested = {
        key: key.description["suggested_value"]
        for key in schema
        if hasattr(key, "description") and key.description
    }
    for field in ("device_type", "name", "host", "access_key", "port", "site_id"):
        assert suggested.get(field) == USER_INPUT[field]
    assert "password" not in suggested


async def test_duplicate_hub_is_aborted(hass):
    MockConfigEntry(
        domain="hivemind",
        data=USER_INPUT,
        unique_id="ws://127.0.0.1-key",
    ).add_to_hass(hass)

    result = await _submit(hass, handshake_ok=True)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


PADDED_INPUT = {
    **USER_INPUT,
    "name": " Living Room ",
    "host": " ws://127.0.0.1\n",
    "access_key": "  key\n",
    "password": " pw ",
    "site_id": "test ",
}


async def test_pasted_fields_are_trimmed_before_they_are_stored(hass):
    """A key pasted with a trailing newline is stored as the hub holds it.

    hivemind-core compares access keys byte for byte, so an untrimmed paste is
    refused as an invalid api key while `list-clients` still prints it.
    """
    seen = []
    result = await _submit(hass, user_input=PADDED_INPUT, seen=seen)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["access_key"] == "key"
    assert result["data"]["host"] == "ws://127.0.0.1"
    assert result["data"]["site_id"] == "test"
    assert result["data"]["name"] == "Living Room"
    assert result["title"] == "Living Room"
    # validation sees the trimmed key, so the identity file and the connection
    # it validates are the ones the entry will use
    assert seen and seen[0]["access_key"] == "key"


async def test_password_is_not_trimmed(hass):
    """A password may legitimately end in a space; changing it is not ours to do."""
    result = await _submit(hass, user_input=PADDED_INPUT)
    assert result["data"]["password"] == " pw "


async def test_padded_key_hits_the_duplicate_guard(hass):
    """The unique id is built from trimmed values, so a padded re-entry aborts."""
    MockConfigEntry(
        domain="hivemind",
        data=USER_INPUT,
        unique_id="ws://127.0.0.1-key",
    ).add_to_hass(hass)

    result = await _submit(hass, user_input=PADDED_INPUT)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
