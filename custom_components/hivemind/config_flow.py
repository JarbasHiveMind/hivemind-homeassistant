"""Config flow for the HiveMind integration."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from . import _build_bus, _connect, _identity_path
from .const import DEVICE_TYPES, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Specify items in the order they are to be displayed in the UI
HIVEMIND_SCHEMA = {
    vol.Required("device_type", default="voice_assistant"): vol.In(DEVICE_TYPES),
    vol.Required("name"): str,
    vol.Required("host"): str,
    vol.Required("port", default=5678): int,
    vol.Required("access_key"): str,
    vol.Required("password"): str,
    vol.Optional("site_id"): str,
    vol.Required("allow_self_signed", default=False): bool,
}


# Fields that are pasted, never typed from memory, and whose stored value must
# match a hub record byte for byte. The password is deliberately absent: a
# password may legitimately end in a space, and silently changing a credential
# is worse than a refused connection the operator can see.
_TRIMMED_FIELDS = ("access_key", "host", "site_id", "name")


def _trim_pasted_fields(user_input: dict[str, Any]) -> dict[str, Any]:
    """Strip surrounding whitespace from the pasted fields.

    hivemind-core looks an access key up byte for byte
    (``db.get_client_by_api_key``). A key copied out of ``hivemind-core
    list-clients`` and pasted into this form often carries a trailing space or
    a newline, and the hub then answers "Client provided an invalid api key"
    for a key the same ``list-clients`` still prints — the operator has no way
    to see the difference. Trimming at the point of entry is what keeps the
    stored key the one the hub holds.

    It runs before the unique id is built and before validation, so the
    duplicate guard and the identity file (which is keyed by the access key)
    both see the trimmed value.
    """
    trimmed = dict(user_input)
    for field in _TRIMMED_FIELDS:
        value = trimmed.get(field)
        if isinstance(value, str):
            trimmed[field] = value.strip()
    return trimmed


def _try_handshake(data: dict, identity_file: str) -> bool:
    """Open a validation connection to the hub and report whether it handshakes.

    Runs in an executor (socket + file I/O). It uses the *same* persistent
    identity the entry will use at runtime, so the Noise static key validated
    here is the one that actually runs — a throwaway key would be pinned by the
    hub and lock the real connection out. Returns True on a completed handshake,
    False if the hub answered but the handshake never completed within a bounded
    number of retries (typically a wrong access key / password).

    The handshake wait is bounded (``handshake_max_retries=1``): a wrong
    password on v3 Noise makes the hub close the socket cleanly (ws 1000)
    without ever tripping ``_auth_rejected``, so an unbounded wait would
    reconnect forever and hang the config flow. The client is always closed in
    ``finally`` so no reconnect thread outlives the aborted validation.
    """
    bus = _build_bus(identity_file, data)
    try:
        try:
            _connect(bus, handshake_max_retries=1)
        except RuntimeError:
            # hub answered but the bounded handshake never completed: bad key / password
            return False
        return bool(bus.handshake_event.is_set())
    finally:
        try:
            bus.close()
        except Exception:
            _LOGGER.debug("Error closing HiveMind validation connection", exc_info=True)


async def validate_connection(hass: HomeAssistant, data: dict) -> str | None:
    """Validate the hub connection. Returns an error key, or None on success."""
    identity_file = _identity_path(hass, data["access_key"])
    try:
        ok = await hass.async_add_executor_job(_try_handshake, data, identity_file)
    except Exception as err:  # noqa: BLE001 - surface as cannot_connect
        _LOGGER.warning("HiveMind connection validation failed: %s", err)
        return "cannot_connect"
    return None if ok else "invalid_auth"


class HiveMindConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """HiveMind config flow."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input = _trim_pasted_fields(user_input)
            await self.async_set_unique_id(
                f"{user_input['host']}-{user_input['access_key']}"
            )
            self._abort_if_unique_id_configured()

            error = await validate_connection(self.hass, user_input)
            if error is None:
                return self.async_create_entry(
                    title=user_input.get("name", "HiveMind"), data=user_input
                )
            errors["base"] = error

        suggested_values = {k: v for k, v in (user_input or {}).items() if k != "password"}
        data_schema = self.add_suggested_values_to_schema(
            vol.Schema(HIVEMIND_SCHEMA), suggested_values
        )
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
