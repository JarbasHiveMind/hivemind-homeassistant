"""HiveMind sensor: listener state (via ovos-dinkum-listener)."""

import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from ovos_bus_client.message import Message

from .entity import HiveMindEntity

_LOGGER = logging.getLogger(__name__)


class HiveMindListenerStateSensor(HiveMindEntity, SensorEntity):
    """Reports the listener's current runtime state."""

    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(self, bus, site_id: str, name: str, **kwargs) -> None:
        super().__init__(bus, site_id, name, **kwargs)
        self._mode = "wakeword"

    def _subscribe(self) -> None:
        self._register("recognizer_loop:state", self.handle_loop_status)
        self._register("recognizer_loop:sleep", self.handle_sleep_enabled)
        self._register("recognizer_loop:awoken", self.handle_sleep_disabled)

    @property
    def name(self):
        return f"Listen State ({self._name})"

    @property
    def unique_id(self) -> str | None:
        return self._uid("listen-state")

    @property
    def options(self) -> list[str]:
        return [
            "wakeword", "continuous", "recording", "sleeping", "wake_up",
            "confirmation", "before_cmd", "in_cmd", "after_cmd",
        ]

    async def async_update(self):
        if self.available:
            self.bus.emit_mycroft(Message("recognizer_loop:state.get"))

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
        return {
            "continuous": "mdi:microphone-settings",
            "sleeping": "mdi:sleep",
            "wakeword": "mdi:microphone-message",
            "recording": "mdi:record-rec",
            "before_cmd": "mdi:chat-sleep",
            "in_cmd": "mdi:chat-processing",
            "after_cmd": "mdi:chat",
            "wake_up": "mdi:chat-alert",
        }.get(self._mode, "mdi:music-box")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
):
    """Set up the listener-state sensor from a config entry."""
    name = entry.data.get("name", "unnamed device")
    site_id = entry.data.get("site_id", "unknown")
    async_add_entities(
        [HiveMindListenerStateSensor(bus=entry.hm_bus, name=name, site_id=site_id)]
    )
