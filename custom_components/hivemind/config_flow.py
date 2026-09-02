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
    vol.Required("access_key"): str,
    vol.Required("password"): str,
    vol.Required("port", default=5678): int,
    vol.Required("legacy_audio", default=False): bool,
    vol.Optional("site_id", default="unknown"): str,
    vol.Required("allow_self_signed", default=False): bool,
}


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
        except (RuntimeError, ConnectionRefusedError):
            # hub reachable but handshake never completed: bad key / password
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

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(HIVEMIND_SCHEMA),
            errors=errors,
        )
