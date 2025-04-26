"""HiveMind notification platform."""
import logging

from hivemind_bus_client.client import HiveMessageBusClient
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class HiveMindConnectionSensor(BinarySensorEntity):
    """Binary Sensor for HiveMind connection status."""

    def __init__(self, bus: HiveMessageBusClient, site_id: str, name: str, **kwargs) -> None:
        """Initialize the service."""
        self._name = name.replace(" ", "-")
        self.site_id = site_id
        self.bus = bus

    @property
    def name(self):
        """Name of the entity."""
        return f"hm-connection-status-{self._name}"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID for this entity."""
        return f"{self.name}-{self.site_id}".replace(" ", "")

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
    def is_on(self) -> bool:
        """Return the status of the binary sensor (True if connected)."""
        return self.bus.handshake_event.is_set()

    @property
    def device_class(self) -> BinarySensorDeviceClass:
        return BinarySensorDeviceClass.CONNECTIVITY

    @property
    def icon(self) -> str | None:
        """Return the icon for the binary sensor."""
        if self.is_on:
            return "mdi:lan-connect"
        return "mdi:lan-disconnect"


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities
):
    """Set up notify service from a config entry."""
    # Get config values
    name = entry.data.get("name", "unnamed device")
    site_id = entry.data.get("site_id", "unknown")

    # Create the connection sensor entity
    connection_sensor = HiveMindConnectionSensor(
        bus=entry.hm_bus,
        name=name,
        site_id=site_id
    )

    # Add it to Home Assistant
    async_add_entities([connection_sensor])
