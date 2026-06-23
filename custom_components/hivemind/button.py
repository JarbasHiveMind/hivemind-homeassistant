"""HiveMind buttons: reconnect, system reboot/shutdown, OVOS restart, listen, stop."""

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from ovos_bus_client.message import Message

from .entity import HiveMindEntity

_LOGGER = logging.getLogger(__name__)


class HiveMindConnectionButton(HiveMindEntity, ButtonEntity):
    """Reconnect to the HiveMind hub."""

    @property
    def available(self) -> bool:
        # Stay pressable while disconnected — this is how you reconnect.
        return True

    @property
    def name(self):
        return f"Reconnect to HiveMind ({self._name})"

    @property
    def unique_id(self) -> str | None:
        return self._uid("reconnect-button")

    async def async_press(self) -> None:
        """Reconnect to HiveMind off the event loop (socket I/O is blocking)."""
        connected = self.bus.handshake_event.is_set()
        _LOGGER.info(
            "HiveMind Reconnection Button pressed: %s",
            "Connected" if connected else "Disconnected",
        )
        await self.hass.async_add_executor_job(self._reconnect)

    def _reconnect(self) -> None:
        self.bus.close()
        # close() does not reset these on older hivemind-bus-client versions
        self.bus.handshake_event.clear()
        self.bus.connected_event.clear()
        self.bus.protocol = None
        self.bus.crypto_key = None
        self.bus.connect(site_id=self.bus.site_id)

    @property
    def icon(self) -> str | None:
        return "mdi:dots-hexagon"


class HiveMindSystemRebootButton(HiveMindEntity, ButtonEntity):
    """Reboot the device via ovos-PHAL-plugin-system."""

    @property
    def name(self):
        return f"Reboot Device ({self._name})"

    @property
    def unique_id(self) -> str | None:
        return self._uid("reboot-button")

    def press(self) -> None:
        self.bus.emit_mycroft(Message("system.reboot"))
        _LOGGER.info("HiveMind Reboot Button pressed!")

    @property
    def icon(self) -> str | None:
        return "mdi:restart-alert"


class HiveMindSystemShutdownButton(HiveMindEntity, ButtonEntity):
    """Shut down the device via ovos-PHAL-plugin-system."""

    @property
    def name(self):
        return f"Shutdown Device ({self._name})"

    @property
    def unique_id(self) -> str | None:
        return self._uid("shutdown-button")

    def press(self) -> None:
        self.bus.emit_mycroft(Message("system.shutdown"))
        _LOGGER.info("HiveMind Shutdown Button pressed!")

    @property
    def icon(self) -> str | None:
        return "mdi:power"


class HiveMindRestartButton(HiveMindEntity, ButtonEntity):
    """Restart OVOS via ovos-PHAL-plugin-system."""

    @property
    def name(self):
        return f"Restart OVOS ({self._name})"

    @property
    def unique_id(self) -> str | None:
        return self._uid("restart-button")

    def press(self) -> None:
        self.bus.emit_mycroft(Message("system.mycroft.service.restart"))
        _LOGGER.info("HiveMind OVOS Restart Button pressed!")

    @property
    def icon(self) -> str | None:
        return "mdi:restart"


class HiveMindMicListenButton(HiveMindEntity, ButtonEntity):
    """Trigger microphone listening on the device."""

    @property
    def name(self):
        return f"Start Listening ({self._name})"

    @property
    def unique_id(self) -> str | None:
        return self._uid("listen-button")

    def press(self) -> None:
        _LOGGER.info("HiveMind Listen Button pressed")
        self.bus.emit_mycroft(Message("mycroft.mic.listen"))

    @property
    def icon(self) -> str | None:
        return "mdi:microphone"


class HiveMindStopButton(HiveMindEntity, ButtonEntity):
    """Send a stop signal to the device."""

    @property
    def name(self):
        return f"Stop ({self._name})"

    @property
    def unique_id(self) -> str | None:
        return self._uid("stop-button")

    def press(self) -> None:
        _LOGGER.info("HiveMind Stop Button pressed")
        self.bus.emit_mycroft(Message("mycroft.stop"))

    @property
    def icon(self) -> str | None:
        return "mdi:stop-circle"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
):
    """Set up the buttons from a config entry."""
    name = entry.data.get("name", "unnamed device")
    site_id = entry.data.get("site_id", "unknown")
    device_type = entry.data.get("device_type", "voice_assistant")

    buttons = [
        HiveMindConnectionButton(bus=entry.hm_bus, name=name, site_id=site_id),
        HiveMindStopButton(bus=entry.hm_bus, name=name, site_id=site_id),
        HiveMindSystemRebootButton(bus=entry.hm_bus, name=name, site_id=site_id),
        HiveMindRestartButton(bus=entry.hm_bus, name=name, site_id=site_id),
        HiveMindSystemShutdownButton(bus=entry.hm_bus, name=name, site_id=site_id),
    ]

    if device_type == "voice_assistant":
        buttons.append(
            HiveMindMicListenButton(bus=entry.hm_bus, name=name, site_id=site_id)
        )

    async_add_entities(buttons)
