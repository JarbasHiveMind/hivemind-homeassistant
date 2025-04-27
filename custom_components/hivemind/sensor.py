"""HiveMind notification platform."""
import logging
from typing import List
from ovos_bus_client.message import Message
from hivemind_bus_client.client import HiveMessageBusClient
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class HiveMindListenerStateSensor(SensorEntity):
    """Sensor for HiveMind listener state"""

    def __init__(self, bus: HiveMessageBusClient, site_id: str, name: str, **kwargs) -> None:
        """Initialize the service."""
        self._name = name.replace(" ", "-")
        self.site_id = site_id
        self.bus = bus
        self._mode = "wakeword"

        self.bus.on_mycroft("recognizer_loop:state", self.handle_loop_status)
        self.bus.on_mycroft("recognizer_loop:sleep", self.handle_sleep_enabled)
        self.bus.on_mycroft("recognizer_loop:awoken", self.handle_sleep_disabled)

    @property
    def name(self):
        """Name of the entity."""
        return f"Listen State ({self._name})"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID for this entity."""
        return f"hm-listen-state-{self._name}-{self.site_id}".replace(" ", "")

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
    def device_class(self) -> SensorDeviceClass:
        return SensorDeviceClass.ENUM

    @property
    def state_class(self) -> SensorStateClass :
        return SensorStateClass.MEASUREMENT

    @property
    def options(self) -> List[str]:
        """Return the current listener state"""
        return ["wakeword", "continuous", "recording",
                "sleeping", "wake_up", "confirmation",
                "before_cmd", "in_cmd", "after_cmd"]

    async def async_update(self):
        self.bus.emit_mycroft(Message(f"recognizer_loop:state.get"))

    def handle_loop_status(self, message: Message):
        self._mode = message.data.get("state", "wakeword")
        self.schedule_update_ha_state()

    def handle_sleep_enabled(self, message: Message):
        self._mode = "sleeping"
        self.schedule_update_ha_state()

    def handle_sleep_disabled(self, message: Message):
        self._mode = "wake_up"
        self.schedule_update_ha_state()

    @property
    def native_value(self) -> str | None:
        return self._mode

    @property
    def icon(self) -> str | None:
        if self._mode == "continuous":
            return "mdi:microphone-settings"
        elif self._mode == "sleeping":
            return "mdi:sleep"
        elif self._mode == "wakeword":
            return "mdi:microphone-message"
        elif self._mode == "recording":
            return "mdi:record-rec"
        elif self._mode == "before_cmd":
            return "mdi:chat-sleep"
        elif self._mode == "in_cmd":
            return "mdi:chat-processing"
        elif self._mode == "after_cmd":
            return "mdi:chat"
        elif self._mode == "wake_up":
            return "mdi:chat-alert"
        # elif self._mode == "confirmation"
        return "mdi:music-box"


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
    listener_sensor = HiveMindListenerStateSensor(
        bus=entry.hm_bus,
        name=name,
        site_id=site_id
    )

    # Add it to Home Assistant
    async_add_entities([listener_sensor])
