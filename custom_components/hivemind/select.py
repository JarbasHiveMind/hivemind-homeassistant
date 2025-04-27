"""HiveMind notification platform."""
import logging
from typing import List
from ovos_bus_client.message import Message
from hivemind_bus_client.client import HiveMessageBusClient
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class HiveMindListeningMode(SelectEntity):
    """control listening mode via ovos-dinkum-listener"""

    def __init__(self, bus: HiveMessageBusClient, site_id: str, name: str, **kwargs) -> None:
        """Initialize the service."""
        self._name = name.replace(" ", "-")
        self.site_id = site_id
        self.bus = bus
        self._mode = "wakeword"

        self.bus.on_mycroft("recognizer_loop:state", self.handle_loop_status)

    @property
    def available(self) -> bool:
        return self.bus.handshake_event.is_set()

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, f"{self._name}-{self.site_id}-{self.bus._host}")
            },
            name=self._name,
            manufacturer="JarbasAI",
            model="HiveMindBus"
        )

    @property
    def name(self):
        """Name of the entity."""
        return f"Listening Mode ({self._name})"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID for this entity."""
        return f"hm-listen-mode-{self._name}-{self.site_id}".replace(" ", "")

    async def async_update(self):
        self.bus.emit_mycroft(Message(f"recognizer_loop:state.get"))

    def handle_loop_status(self, message: Message):
        mode = message.data.get("mode", "wakeword")
        if mode != "sleeping":
            self._mode = mode
            self.schedule_update_ha_state()

    @property
    def current_option(self) -> str:
        """Return the current listener mode"""
        return self._mode

    @property
    def options(self) -> List[str]:
        """Return the current listener mode"""
        return ["wakeword", "continuous", "hybrid"]

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        self.bus.emit_mycroft(Message("recognizer_loop:state.set",
                                      {"mode": option}))

    @property
    def icon(self) -> str | None:
        if self._mode == "hybrid":
            return "mdi:microphone-plus"
        elif self._mode == "continuous":
            return "mdi:microphone-settings"
        return "mdi:microphone-message"


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities
):
    """Set up notify service from a config entry."""
    # Get config values
    name = entry.data.get("name", "unnamed device")
    site_id = entry.data.get("site_id", "unknown")

    # Create the connection button entity
    listen_mode = HiveMindListeningMode(
        bus=entry.hm_bus,
        name=name,
        site_id=site_id
    )


    # Add it to Home Assistant
    async_add_entities([listen_mode])
