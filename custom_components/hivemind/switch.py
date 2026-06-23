"""HiveMind switches: SSH, volume mute, microphone mute, and sleep mode."""

import logging

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from ovos_bus_client.message import Message

from .entity import HiveMindEntity

_LOGGER = logging.getLogger(__name__)


class HiveMindSSHSwitch(HiveMindEntity, SwitchEntity):
    """Control SSH via ovos-PHAL-plugin-system."""

    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, bus, site_id: str, name: str, **kwargs) -> None:
        super().__init__(bus, site_id, name, **kwargs)
        self._enabled = False

    def _subscribe(self) -> None:
        self._register("system.ssh.status.response", self.handle_ssh_status)
        self._register("system.ssh.enabled", self.handle_ssh_enabled)
        self._register("system.ssh.disabled", self.handle_ssh_disabled)

    @property
    def name(self):
        return f"SSH Service ({self._name})"

    @property
    def unique_id(self) -> str | None:
        return self._uid("ssh-switch")

    async def async_update(self):
        if self.available:
            self.bus.emit_mycroft(Message("system.ssh.status"))

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
        return self._enabled

    async def async_turn_on(self, **kwargs):
        self.bus.emit_mycroft(Message("system.ssh.enable"))

    async def async_turn_off(self, **kwargs):
        self.bus.emit_mycroft(Message("system.ssh.disable"))

    @property
    def icon(self) -> str | None:
        return "mdi:remote-desktop"


class HiveMindVolumeMuteSwitch(HiveMindEntity, SwitchEntity):
    """Control volume mute via ovos-PHAL-plugin-alsa."""

    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, bus, site_id: str, name: str, **kwargs) -> None:
        super().__init__(bus, site_id, name, **kwargs)
        self._muted = False

    def _subscribe(self) -> None:
        self._register("mycroft.volume.get.response", self.handle_mute_status)
        self._register("mycroft.volume.mute", self.handle_mute_enabled)
        self._register("mycroft.volume.unmute", self.handle_mute_disabled)

    @property
    def name(self):
        return f"Volume Mute ({self._name})"

    @property
    def unique_id(self) -> str | None:
        return self._uid("volume-mute-switch")

    async def async_update(self):
        if self.available:
            self.bus.emit_mycroft(Message("mycroft.volume.get"))

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
        return self._muted

    async def async_turn_on(self, **kwargs):
        self.bus.emit_mycroft(Message("mycroft.volume.mute"))

    async def async_turn_off(self, **kwargs):
        self.bus.emit_mycroft(Message("mycroft.volume.unmute"))

    @property
    def icon(self) -> str | None:
        return "mdi:volume-mute" if self._muted else "mdi:volume-high"


class HiveMindMicMuteSwitch(HiveMindEntity, SwitchEntity):
    """Control microphone mute via ovos-dinkum-listener."""

    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, bus, site_id: str, name: str, **kwargs) -> None:
        super().__init__(bus, site_id, name, **kwargs)
        self._muted = False

    def _subscribe(self) -> None:
        self._register("mycroft.mic.get_status.response", self.handle_mute_status)

    @property
    def name(self):
        return f"Microphone Mute ({self._name})"

    @property
    def unique_id(self) -> str | None:
        return self._uid("mic-mute-switch")

    async def async_update(self):
        if self.available:
            self.bus.emit_mycroft(Message("mycroft.mic.get_status"))

    def handle_mute_status(self, message: Message):
        self._muted = message.data.get("muted", False)
        self.schedule_update_ha_state()

    @property
    def is_on(self) -> bool:
        return self._muted

    async def async_turn_on(self, **kwargs):
        self.bus.emit_mycroft(Message("mycroft.mic.mute"))

    async def async_turn_off(self, **kwargs):
        self.bus.emit_mycroft(Message("mycroft.mic.unmute"))

    @property
    def icon(self) -> str | None:
        return "mdi:microphone-off" if self._muted else "mdi:microphone"


class HiveMindSleepModeSwitch(HiveMindEntity, SwitchEntity):
    """Control sleep mode via ovos-dinkum-listener."""

    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, bus, site_id: str, name: str, **kwargs) -> None:
        super().__init__(bus, site_id, name, **kwargs)
        self._sleeping = False

    def _subscribe(self) -> None:
        self._register("recognizer_loop:state", self.handle_sleep_status)
        self._register("recognizer_loop:sleep", self.handle_sleep_enabled)
        self._register("recognizer_loop:awoken", self.handle_sleep_disabled)

    @property
    def name(self):
        return f"Sleep Mode ({self._name})"

    @property
    def unique_id(self) -> str | None:
        return self._uid("sleep-switch")

    async def async_update(self):
        if self.available:
            self.bus.emit_mycroft(Message("recognizer_loop:state.get"))

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
        return self._sleeping

    async def async_turn_on(self, **kwargs):
        self._sleeping = True
        self.bus.emit_mycroft(Message("recognizer_loop:sleep"))

    async def async_turn_off(self, **kwargs):
        self._sleeping = False
        self.bus.emit_mycroft(Message("recognizer_loop:wake_up"))

    @property
    def icon(self) -> str | None:
        return "mdi:sleep" if self._sleeping else "mdi:sleep-off"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
):
    """Set up the switches from a config entry."""
    name = entry.data.get("name", "unnamed device")
    site_id = entry.data.get("site_id", "unknown")
    device_type = entry.data.get("device_type", "voice_assistant")

    switches = [HiveMindSSHSwitch(bus=entry.hm_bus, name=name, site_id=site_id)]

    if device_type in ["voice_assistant", "media_player"]:
        switches.append(
            HiveMindVolumeMuteSwitch(bus=entry.hm_bus, name=name, site_id=site_id)
        )
        if device_type == "voice_assistant":
            switches += [
                HiveMindMicMuteSwitch(bus=entry.hm_bus, name=name, site_id=site_id),
                HiveMindSleepModeSwitch(bus=entry.hm_bus, name=name, site_id=site_id),
            ]

    async_add_entities(switches)
