"""HiveMind notification platform."""
import logging

from hivemind_bus_client.client import HiveMessageBusClient
from hivemind_bus_client.message import HiveMessageType, HiveMessage
from homeassistant.components.notify import NotifyEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from ovos_bus_client import Message

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class HiveMindNotifier(NotifyEntity):
    _attr_has_entity_name = True

    def __init__(self, bus: HiveMessageBusClient, site_id: str, name: str, **kwargs) -> None:
        """Initialize the service."""
        self._name = name.replace(" ", "-")
        self.site_id = site_id
        self.bus = bus

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
    def icon(self) -> str | None:
        """Icon of the entity."""
        return "mdi:robot-outline"

    @property
    def name(self):
        """Name of the entity."""
        return f"hm-notify-{self._name}"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID for this entity."""
        return f"{self.name}-{self.site_id}".replace(" ", "")

    def speak(self, utterance: str):
        payload = HiveMessage(HiveMessageType.BUS, Message("speak", {"utterance": utterance}))
        try:
            _LOGGER.log(level=3, msg=f"HiveMind Message: {payload.serialize()}")
            self.bus.emit(payload)
        except:
            _LOGGER.log(level=1, msg="Error from HiveMind messagebus", exc_info=True)

    def send_message(self, message: str, title: str | None = None) -> None:
        """Send a message."""
        if title:
            self.speak(title)
        self.speak(message)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities
):
    """Set up notify service from a config entry."""
    # Get config values
    name = entry.data.get("name", "unnamed device")
    site_id = entry.data.get("site_id", "unknown")

    # Create the notifier entity
    notifier = HiveMindNotifier(
        bus=entry.hm_bus,
        name=name,
        site_id=site_id
    )

    # Add it to Home Assistant
    async_add_entities([notifier])
