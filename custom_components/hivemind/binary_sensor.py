"""HiveMind binary sensors: connection, speaking, and per-service alive/ready."""

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from ovos_bus_client.message import Message

from .entity import HiveMindEntity

_LOGGER = logging.getLogger(__name__)

# OVOS process name -> friendly label shown in the entity name
_PROC_LABELS = {
    "skills": "ovos-core",
    "audio": "ovos-audio",
    "voice": "ovos-listener",
    "gui_service": "ovos-gui",
    "PHAL": "ovos-PHAL",
}


class HiveMindConnectionSensor(HiveMindEntity, BinarySensorEntity):
    """Whether the satellite is connected to the hub (handshake complete)."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    @property
    def available(self) -> bool:
        # Always available: this sensor *reports* the connection, so it must
        # stay visible (on/off) rather than going unavailable when disconnected.
        return True

    @property
    def name(self):
        return f"Connection Status ({self._name})"

    @property
    def unique_id(self) -> str | None:
        return self._uid("connection-status")

    @property
    def is_on(self) -> bool:
        return self.bus.handshake_event.is_set()

    @property
    def icon(self) -> str | None:
        return "mdi:lan-connect" if self.is_on else "mdi:lan-disconnect"


class HiveMindSpeakingSensor(HiveMindEntity, BinarySensorEntity):
    """Whether the device is currently speaking (TTS playing)."""

    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, bus, site_id: str, name: str, **kwargs) -> None:
        super().__init__(bus, site_id, name, **kwargs)
        self._is_speaking = False

    def _subscribe(self) -> None:
        self._register("mycroft.audio.is_speaking", self.handle_update)

    def handle_update(self, message: Message):
        self._is_speaking = message.data.get("speaking", False)
        self.schedule_update_ha_state()

    async def async_update(self):
        if self.available:
            self.bus.emit_mycroft(Message("mycroft.audio.speak.status"))

    @property
    def name(self):
        return f"Speaking ({self._name})"

    @property
    def unique_id(self) -> str | None:
        return self._uid("speaking-status")

    @property
    def is_on(self) -> bool:
        return self._is_speaking

    @property
    def icon(self) -> str | None:
        return "mdi:account-voice" if self.is_on else "mdi:account-voice-off"


class _HiveMindServiceSensor(HiveMindEntity, BinarySensorEntity):
    """Base for the per-OVOS-service alive/ready probes."""

    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _kind = ""  # "alive" or "ready"
    _request = ""  # message emitted to poll status
    _response = ""  # message listened to for the answer

    def __init__(self, bus, site_id: str, name: str, proc_name: str, **kwargs) -> None:
        super().__init__(bus, site_id, name, **kwargs)
        self._proc_name = proc_name
        self._on = False

    def _subscribe(self) -> None:
        self._register(f"mycroft.{self._proc_name}.{self._response}", self.handle_update)

    def handle_update(self, message: Message):
        self._on = message.data.get("status", False)
        self.schedule_update_ha_state()

    async def async_update(self):
        if self.available:
            self.bus.emit_mycroft(Message(f"mycroft.{self._proc_name}.{self._request}"))

    @property
    def name(self):
        label = _PROC_LABELS.get(self._proc_name, self._proc_name)
        return f"{label} {self._kind.capitalize()} ({self._name})"

    @property
    def unique_id(self) -> str | None:
        return self._uid(f"{self._kind}-sensor-{self._proc_name}")

    @property
    def is_on(self) -> bool:
        return self._on

    @property
    def icon(self) -> str | None:
        return "mdi:check-circle" if self.is_on else "mdi:alert-circle"


class HiveMindAliveSensor(_HiveMindServiceSensor):
    """Whether an OVOS service process is alive."""

    _kind = "alive"
    _request = "is_alive"
    _response = "is_alive.response"


class HiveMindReadySensor(_HiveMindServiceSensor):
    """Whether an OVOS service process is ready."""

    _kind = "ready"
    _request = "is_ready"
    _response = "is_ready.response"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
):
    """Set up the binary sensors from a config entry."""
    name = entry.data.get("name", "unnamed device")
    site_id = entry.data.get("site_id", "unknown")
    device_type = entry.data.get("device_type", "voice_assistant")

    sensors = [HiveMindConnectionSensor(bus=entry.hm_bus, name=name, site_id=site_id)]
    services = ["PHAL"]

    if device_type in ["voice_assistant", "media_player"]:
        services += ["audio"]
        sensors.append(
            HiveMindSpeakingSensor(bus=entry.hm_bus, name=name, site_id=site_id)
        )

    if device_type == "voice_assistant":
        services += ["skills", "voice", "gui_service"]

    for proc in services:
        sensors.append(
            HiveMindAliveSensor(bus=entry.hm_bus, name=name, proc_name=proc, site_id=site_id)
        )
        sensors.append(
            HiveMindReadySensor(bus=entry.hm_bus, name=name, proc_name=proc, site_id=site_id)
        )

    async_add_entities(sensors)
