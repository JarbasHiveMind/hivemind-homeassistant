"""HiveMind notification platform."""
import logging

from hivemind_bus_client.client import HiveMessageBusClient
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class HiveMindConnectionButton(ButtonEntity):
    """Button for reconnecting to HiveMind."""

    def __init__(self, bus: HiveMessageBusClient, site_id: str, name: str, **kwargs) -> None:
        """Initialize the service."""
        self._name = name.replace(" ", "-")
        self.site_id = site_id
        self.bus = bus

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
        return f"hm-reconnect-button-{self._name}"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID for this entity."""
        return f"{self.name}-{self.site_id}".replace(" ", "")

    def press(self) -> None:
        """Press the button to connect or disconnect."""
        connected = self.bus.handshake_event.is_set()
        _LOGGER.info(f"HiveMind Reconnection Button pressed: {'Connected' if connected else 'Disconnected'}")
        self.bus.close()
        self.bus.handshake_event.clear()
        self.bus.connected_event.clear()
        self.bus.protocol = None # force key renegotiation
        self.bus.connect(site_id=self.bus.site_id)


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
    connection_button = HiveMindConnectionButton(
        bus=entry.hm_bus,
        name=name,
        site_id=site_id
    )

    # Add it to Home Assistant
    async_add_entities([connection_button])
