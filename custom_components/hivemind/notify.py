"""HiveMind notify entity: speak text on the device via TTS."""

import logging

from hivemind_bus_client.message import HiveMessage, HiveMessageType
from homeassistant.components.notify import NotifyEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from ovos_bus_client import Message

from .entity import HiveMindEntity

_LOGGER = logging.getLogger(__name__)


class HiveMindNotifier(HiveMindEntity, NotifyEntity):
    """Speak a notification on the HiveMind device."""

    _attr_has_entity_name = True

    @property
    def name(self):
        return f"Speak ({self._name})"

    @property
    def unique_id(self) -> str | None:
        return self._uid("notify")

    @property
    def icon(self) -> str | None:
        return "mdi:robot-outline"

    def speak(self, utterance: str):
        payload = HiveMessage(HiveMessageType.BUS, Message("speak", {"utterance": utterance}))
        try:
            _LOGGER.debug("HiveMind Message: %s", payload.serialize())
            self.bus.emit(payload)
        except Exception:
            _LOGGER.exception("Error from HiveMind messagebus")

    def send_message(self, message: str, title: str | None = None) -> None:
        """Send a message."""
        if title:
            self.speak(title)
        self.speak(message)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
):
    """Set up the notify entity from a config entry."""
    name = entry.data.get("name", "unnamed device")
    site_id = entry.data.get("site_id", "unknown")
    async_add_entities(
        [HiveMindNotifier(bus=entry.hm_bus, name=name, site_id=site_id)]
    )
