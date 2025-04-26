from typing import Any

import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN

# Specify items in the order they are to be displayed in the UI
HIVEMIND_SCHEMA = {
    vol.Required("name"): str,
    vol.Required("access_key"): str,
    vol.Required("password"): str,
    vol.Required("site_id"): str,
    vol.Required("host"): str,
    vol.Required("port", default=5678): int,
    vol.Required("allow_self_signed", default=False): bool,
    vol.Required("legacy_audio", default=False): bool
}


class HiveMindConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """HiveMind config flow."""
    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 0
    MINOR_VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="HiveMind", data=user_input)

        return self.async_show_form(step_id="user", data_schema=vol.Schema(HIVEMIND_SCHEMA))
