"""HiveMind notification platform."""
import logging

from ovos_bus_client.message import Message
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
        return f"Connection Status ({self._name})"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID for this entity."""
        return f"hm-connection-status-{self._name}-{self.site_id}".replace(" ", "")

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


class HiveMindSpeakingSensor(BinarySensorEntity):
    """Binary Sensor for HiveMind connection status."""

    def __init__(self, bus: HiveMessageBusClient, site_id: str, name: str, **kwargs) -> None:
        """Initialize the service."""
        self._name = name.replace(" ", "-")
        self.site_id = site_id
        self.bus = bus
        self._is_speaking = False
        self.bus.on_mycroft("mycroft.audio.is_speaking", self.handle_update)

    def handle_update(self, message: Message):
        self._is_speaking = message.data.get("speaking", False)
        self.schedule_update_ha_state()

    async def async_update(self):
        self.bus.emit_mycroft(Message("mycroft.audio.speak.status"))

    @property
    def name(self):
        """Name of the entity."""
        return f"Speaking ({self._name})"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID for this entity."""
        return f"hm-speaking-status-{self._name}-{self.site_id}".replace(" ", "")

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
        """Return the status of the binary sensor (True if TTS executing)."""
        return self._is_speaking

    @property
    def device_class(self) -> BinarySensorDeviceClass:
        return BinarySensorDeviceClass.RUNNING

    @property
    def icon(self) -> str | None:
        """Return the icon for the binary sensor."""
        if self.is_on:
            return "mdi:account-voice"
        return "mdi:account-voice-off"


class HiveMindAliveSensor(HiveMindConnectionSensor):
    """Binary Sensor for process ALIVE status."""
    def __init__(self, bus: HiveMessageBusClient, site_id: str, name: str, proc_name: str, **kwargs) -> None:
        super().__init__(bus, site_id, name, **kwargs)
        self._proc_name = proc_name
        self._alive = False
        self.bus.on_mycroft(f"mycroft.{self._proc_name}.is_alive.response", self.handle_update)

    def handle_update(self, message: Message):
        self._alive = message.data.get("status", False)
        self.schedule_update_ha_state()

    async def async_update(self):
        self.bus.emit_mycroft(Message(f"mycroft.{self._proc_name}.is_alive"))

    @property
    def name(self):
        """Name of the entity."""
        if self._proc_name == "skills":
            n = "ovos-core"
        elif self._proc_name == "audio":
            n = "ovos-audio"
        elif self._proc_name == "voice":
            n = "ovos-listener"
        elif self._proc_name == "gui_service":
            n = "ovos-gui"
        elif self._proc_name == "PHAL":
            n = "ovos-PHAL"
        else:
            n = self._proc_name
        return f"{n} Alive ({self._name})"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID for this entity."""
        return f"hm-alive-sensor-{self._name}-{self._proc_name}-{self.site_id}".replace(" ", "")

    @property
    def available(self) -> bool:
        return self.bus.handshake_event.is_set()

    @property
    def is_on(self) -> bool:
        """Return the status of the binary sensor (True if service alive)."""
        return self._alive

    @property
    def device_class(self) -> BinarySensorDeviceClass:
        return BinarySensorDeviceClass.RUNNING

    @property
    def icon(self) -> str | None:
        """Return the icon for the binary sensor."""
        if self.is_on:
            return "mdi:check-circle"
        return "mdi:alert-circle"


class HiveMindReadySensor(HiveMindConnectionSensor):
    """Binary Sensor for process READY status."""
    def __init__(self, bus: HiveMessageBusClient, site_id: str, name: str, proc_name: str, **kwargs) -> None:
        super().__init__(bus, site_id, name, **kwargs)
        self._proc_name = proc_name
        self._ready = False
        self.bus.on_mycroft(f"mycroft.{self._proc_name}.is_ready.response", self.handle_update)

    def handle_update(self, message: Message):
        self._ready = message.data.get("status", False)
        self.schedule_update_ha_state()

    async def async_update(self):
        self.bus.emit_mycroft(Message(f"mycroft.{self._proc_name}.is_ready"))

    @property
    def name(self):
        """Name of the entity."""
        if self._proc_name == "skills":
            n = "ovos-core"
        elif self._proc_name == "audio":
            n = "ovos-audio"
        elif self._proc_name == "voice":
            n = "ovos-listener"
        elif self._proc_name == "gui_service":
            n = "ovos-gui"
        elif self._proc_name == "PHAL":
            n = "ovos-PHAL"
        else:
            n = self._proc_name
        return f"{n} Ready ({self._name})"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID for this entity."""
        return f"hm-ready-sensor-{self._name}-{self._proc_name}-{self.site_id}".replace(" ", "")

    @property
    def available(self) -> bool:
        return self.bus.handshake_event.is_set()

    @property
    def is_on(self) -> bool:
        """Return the status of the binary sensor (True if service ready)."""
        return self._ready

    @property
    def device_class(self) -> BinarySensorDeviceClass:
        return BinarySensorDeviceClass.RUNNING

    @property
    def icon(self) -> str | None:
        """Return the icon for the binary sensor."""
        if self.is_on:
            return "mdi:check-circle"
        return "mdi:alert-circle"


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
    spk = HiveMindSpeakingSensor(
        bus=entry.hm_bus,
        name=name,
        site_id=site_id
    )
    sensors = [connection_sensor, spk]
    for proc in ["skills", "audio", "voice", "PHAL", "gui_service"]:
        alive_sensor = HiveMindAliveSensor(
            bus=entry.hm_bus,
            name=name,
            proc_name=proc,
            site_id=site_id
        )
        sensors.append(alive_sensor)
        ready_sensor = HiveMindReadySensor(
            bus=entry.hm_bus,
            name=name,
            proc_name=proc,
            site_id=site_id
        )
        sensors.append(ready_sensor)

    # Add it to Home Assistant
    async_add_entities(sensors)
