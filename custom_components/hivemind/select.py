"""HiveMind select: listening mode (via ovos-dinkum-listener)."""

import logging
from typing import List

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from ovos_bus_client.message import Message

from .entity import HiveMindEntity

_LOGGER = logging.getLogger(__name__)


class HiveMindListeningMode(HiveMindEntity, SelectEntity):
    """Control the listening mode via ovos-dinkum-listener."""

    def __init__(self, bus, site_id: str, name: str, **kwargs) -> None:
        super().__init__(bus, site_id, name, **kwargs)
        self._mode = "wakeword"

    def _subscribe(self) -> None:
        self._register("recognizer_loop:state", self.handle_loop_status)

    @property
    def name(self):
        return f"Listening Mode ({self._name})"

    @property
    def unique_id(self) -> str | None:
        return self._uid("listen-mode")

    async def async_update(self):
        if self.available:
            self.bus.emit_mycroft(Message("recognizer_loop:state.get"))

    def handle_loop_status(self, message: Message):
        mode = message.data.get("mode", "wakeword")
        if mode != "sleeping":
            self._mode = mode
            self.schedule_update_ha_state()

    @property
    def current_option(self) -> str:
        return self._mode

    @property
    def options(self) -> List[str]:
        return ["wakeword", "continuous", "hybrid"]

    async def async_select_option(self, option: str) -> None:
        self.bus.emit_mycroft(Message("recognizer_loop:state.set", {"mode": option}))

    @property
    def icon(self) -> str | None:
        if self._mode == "hybrid":
            return "mdi:microphone-plus"
        if self._mode == "continuous":
            return "mdi:microphone-settings"
        return "mdi:microphone-message"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
):
    """Set up the listening-mode select from a config entry."""
    name = entry.data.get("name", "unnamed device")
    site_id = entry.data.get("site_id", "unknown")
    async_add_entities(
        [HiveMindListeningMode(bus=entry.hm_bus, name=name, site_id=site_id)]
    )
