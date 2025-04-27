"""HiveMind notification platform."""
import logging
from ovos_bus_client.message import Message
from hivemind_bus_client.client import HiveMessageBusClient
from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class HiveMindSSHSwitch(SwitchEntity):
    """control SSH via ovos-PHAL-plugin-system"""

    def __init__(self, bus: HiveMessageBusClient, site_id: str, name: str, **kwargs) -> None:
        """Initialize the service."""
        self._name = name.replace(" ", "-")
        self.site_id = site_id
        self.bus = bus
        self._enabled = False

        self.bus.on_mycroft("system.ssh.status.response", self.handle_ssh_status)
        self.bus.on_mycroft("system.ssh.enabled", self.handle_ssh_enabled)
        self.bus.on_mycroft("system.ssh.disabled", self.handle_ssh_disabled)

    @property
    def available(self) -> bool:
        return self.bus.handshake_event.is_set()

    def device_class(self) -> SwitchDeviceClass | None:
        return SwitchDeviceClass.SWITCH

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
        return f"SSH Service ({self._name})"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID for this entity."""
        return f"hm-ssh-switch-{self._name}-{self.site_id}".replace(" ", "")

    async def async_update(self):
        self.bus.emit_mycroft(Message(f"system.ssh.status"))

    def handle_ssh_status(self, message: Message):
        self._enabled = message.data.get("enabled", False)
        self.schedule_update_ha_state()

    def handle_ssh_enabled(self, message: Message):
        self._enabled = True
        self.schedule_update_ha_state()

    def handle_ssh_disabled(self, message: Message):
        self._enabled = False
        self.schedule_update_ha_state()

    @property
    def is_on(self) -> bool:
        """Return the status of the switch"""
        return self._enabled

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        self.bus.emit_mycroft(Message("system.ssh.enable"))

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        self.bus.emit_mycroft(Message("system.ssh.disable"))

    @property
    def icon(self) -> str | None:
        return "mdi:remote-desktop"


class HiveMindVolumeMuteSwitch(SwitchEntity):
    """control volume mute via ovos-PHAL-plugin-alsa"""

    def __init__(self, bus: HiveMessageBusClient, site_id: str, name: str, **kwargs) -> None:
        """Initialize the service."""
        self._name = name.replace(" ", "-")
        self.site_id = site_id
        self.bus = bus
        self._muted = False

        self.bus.on_mycroft("mycroft.volume.get.response", self.handle_mute_status)
        self.bus.on_mycroft("mycroft.volume.mute", self.handle_mute_enabled)
        self.bus.on_mycroft("mycroft.volume.unmute", self.handle_mute_disabled)

    @property
    def available(self) -> bool:
        return self.bus.handshake_event.is_set()

    def device_class(self) -> SwitchDeviceClass | None:
        return SwitchDeviceClass.SWITCH

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
        return f"Volume Mute ({self._name})"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID for this entity."""
        return f"hm-volume-mute-switch-{self._name}-{self.site_id}".replace(" ", "")

    async def async_update(self):
        self.bus.emit_mycroft(Message(f"mycroft.volume.get"))

    def handle_mute_status(self, message: Message):
        self._muted = message.data.get("muted", False)
        self.schedule_update_ha_state()

    def handle_mute_enabled(self, message: Message):
        self._muted = True
        self.schedule_update_ha_state()

    def handle_mute_disabled(self, message: Message):
        self._muted = False
        self.schedule_update_ha_state()

    @property
    def is_on(self) -> bool:
        """Return the status of the switch"""
        return self._muted

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        self.bus.emit_mycroft(Message("mycroft.volume.mute"))

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        self.bus.emit_mycroft(Message("mycroft.volume.unmute"))

    @property
    def icon(self) -> str | None:
        if self._muted:
            return "mdi:volume-mute"
        return "mdi:volume-high"


class HiveMindMicMuteSwitch(SwitchEntity):
    """control microphone mute via ovos-dinkum-listener"""

    def __init__(self, bus: HiveMessageBusClient, site_id: str, name: str, **kwargs) -> None:
        """Initialize the service."""
        self._name = name.replace(" ", "-")
        self.site_id = site_id
        self.bus = bus
        self._muted = False

        self.bus.on_mycroft("mycroft.mic.get_status.response", self.handle_mute_status)

    @property
    def available(self) -> bool:
        return self.bus.handshake_event.is_set()

    def device_class(self) -> SwitchDeviceClass | None:
        return SwitchDeviceClass.SWITCH

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
        return f"Microphone Mute ({self._name})"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID for this entity."""
        return f"hm-mic-mute-switch-{self._name}-{self.site_id}".replace(" ", "")

    async def async_update(self):
        self.bus.emit_mycroft(Message(f"mycroft.mic.get_status"))

    def handle_mute_status(self, message: Message):
        self._muted = message.data.get("muted", False)
        self.schedule_update_ha_state()

    @property
    def is_on(self) -> bool:
        """Return the status of the switch"""
        return self._muted

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        self.bus.emit_mycroft(Message("mycroft.mic.mute"))

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        self.bus.emit_mycroft(Message("mycroft.mic.unmute"))

    @property
    def icon(self) -> str | None:
        if self._muted:
            return "mdi:microphone-off"
        return "mdi:microphone"


class HiveMindSleepModeSwitch(SwitchEntity):
    """control sleep mode via ovos-dinkum-listener"""

    def __init__(self, bus: HiveMessageBusClient, site_id: str, name: str, **kwargs) -> None:
        """Initialize the service."""
        self._name = name.replace(" ", "-")
        self.site_id = site_id
        self.bus = bus
        self._sleeping = False

        self.bus.on_mycroft("recognizer_loop:state", self.handle_sleep_status)
        self.bus.on_mycroft("recognizer_loop:sleep", self.handle_sleep_enabled)
        self.bus.on_mycroft("recognizer_loop:awoken", self.handle_sleep_disabled)

    @property
    def available(self) -> bool:
        return self.bus.handshake_event.is_set()

    def device_class(self) -> SwitchDeviceClass | None:
        return SwitchDeviceClass.SWITCH

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
        return f"Sleep Mode ({self._name})"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID for this entity."""
        return f"hm-sleep-switch-{self._name}-{self.site_id}".replace(" ", "")

    async def async_update(self):
        self.bus.emit_mycroft(Message(f"recognizer_loop:state.get"))

    def handle_sleep_status(self, message: Message):
        self._sleeping = message.data.get("state", "wakeword") == "sleeping"
        self.schedule_update_ha_state()

    def handle_sleep_enabled(self, message: Message):
        self._sleeping = True
        self.schedule_update_ha_state()

    def handle_sleep_disabled(self, message: Message):
        self._sleeping = False
        self.schedule_update_ha_state()

    @property
    def is_on(self) -> bool:
        """Return the status of the switch"""
        return self._sleeping

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        self._sleeping = True
        self.bus.emit_mycroft(Message("recognizer_loop:sleep"))

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        self._sleeping = False
        self.bus.emit_mycroft(Message("recognizer_loop:wake_up"))

    @property
    def icon(self) -> str | None:
        if self._sleeping:
            return "mdi:sleep"
        return "mdi:sleep-off"


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
    ssh = HiveMindSSHSwitch(
        bus=entry.hm_bus,
        name=name,
        site_id=site_id
    )
    mute = HiveMindVolumeMuteSwitch(
        bus=entry.hm_bus,
        name=name,
        site_id=site_id
    )
    mic_mute = HiveMindMicMuteSwitch(
        bus=entry.hm_bus,
        name=name,
        site_id=site_id
    )
    sleep = HiveMindSleepModeSwitch(
        bus=entry.hm_bus,
        name=name,
        site_id=site_id
    )

    # Add it to Home Assistant
    async_add_entities([ssh, mute, mic_mute, sleep])
