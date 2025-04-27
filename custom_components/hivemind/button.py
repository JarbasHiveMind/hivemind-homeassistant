"""HiveMind notification platform."""
import logging
from ovos_bus_client.message import Message
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
        return f"Reconnect to HiveMind ({self._name})"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID for this entity."""
        return f"hm-reconnect-button-{self._name}-{self.site_id}".replace(" ", "")

    def press(self) -> None:
        """Press the button to connect or disconnect."""
        connected = self.bus.handshake_event.is_set()
        _LOGGER.info(f"HiveMind Reconnection Button pressed: {'Connected' if connected else 'Disconnected'}")
        self.bus.close()
        # TODO - below not done in bus.close() in older versions of hivemind-bus-client
        self.bus.handshake_event.clear()
        self.bus.connected_event.clear()
        self.bus.protocol = None
        self.bus.crypto_key = None
        self.bus.connect(site_id=self.bus.site_id)

    @property
    def icon(self) -> str | None:
        return "mdi:dots-hexagon"

class HiveMindSystemRebootButton(ButtonEntity):
    """Button for rebooting the device via ovos-PHAL-plugin-system"""

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
    def name(self):
        """Name of the entity."""
        return f"Reboot Device ({self._name})"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID for this entity."""
        return f"hm-reboot-button-{self._name}-{self.site_id}".replace(" ", "")

    def press(self) -> None:
        """Press the button to connect or disconnect."""
        self.bus.emit_mycroft(Message("system.reboot"))
        _LOGGER.info(f"HiveMind Reboot Button pressed!")

    @property
    def icon(self) -> str | None:
        return "mdi:restart-alert"

class HiveMindSystemShutdownButton(ButtonEntity):
    """Button for shutting down the device via ovos-PHAL-plugin-system"""

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
    def name(self):
        """Name of the entity."""
        return f"Shutdown Device ({self._name})"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID for this entity."""
        return f"hm-shutdown-button-{self._name}-{self.site_id}".replace(" ", "")

    def press(self) -> None:
        """Press the button to connect or disconnect."""
        self.bus.emit_mycroft(Message("system.shutdown"))
        _LOGGER.info(f"HiveMind Shutdown Button pressed!")

    @property
    def icon(self) -> str | None:
        return "mdi:power"

class HiveMindRestartButton(ButtonEntity):
    """Button for restarting OVOS via ovos-PHAL-plugin-system"""

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
    def name(self):
        """Name of the entity."""
        return f"Restart OVOS ({self._name})"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID for this entity."""
        return f"hm-restart-button-{self._name}-{self.site_id}".replace(" ", "")

    def press(self) -> None:
        """Press the button to connect or disconnect."""
        self.bus.emit_mycroft(Message("system.mycroft.service.restart"))
        _LOGGER.info(f"HiveMind OVOS Restart Button pressed!")


    @property
    def icon(self) -> str | None:
        return "mdi:restart"

class HiveMindMicListenButton(ButtonEntity):
    """Button for triggering microphone listening in HiveMind device."""

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
        return f"Start Listening ({self._name})"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID for this entity."""
        return f"hm-listen-button-{self._name}-{self.site_id}".replace(" ", "")

    def press(self) -> None:
        """Press the button to connect or disconnect."""
        _LOGGER.info(f"HiveMind Listen Button pressed")
        self.bus.emit_mycroft(Message("mycroft.mic.listen"))

    @property
    def icon(self) -> str | None:
        return "mdi:microphone"



class HiveMindStopButton(ButtonEntity):
    """Button for sending a stop signal to HiveMind device."""

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
        return f"Stop ({self._name})"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID for this entity."""
        return f"hm-stop-button-{self._name}-{self.site_id}".replace(" ", "")

    def press(self) -> None:
        """Press the button to connect or disconnect."""
        _LOGGER.info(f"HiveMind Stop Button pressed")
        self.bus.emit_mycroft(Message("mycroft.stop"))

    @property
    def icon(self) -> str | None:
        return "mdi:stop-circle"

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
    reboot_button = HiveMindSystemRebootButton(
        bus=entry.hm_bus,
        name=name,
        site_id=site_id
    )
    restart_button = HiveMindRestartButton(
        bus=entry.hm_bus,
        name=name,
        site_id=site_id
    )
    shutdown_button = HiveMindSystemShutdownButton(
        bus=entry.hm_bus,
        name=name,
        site_id=site_id
    )
    listen_button = HiveMindMicListenButton(
        bus=entry.hm_bus,
        name=name,
        site_id=site_id
    )
    stop_button = HiveMindStopButton(
        bus=entry.hm_bus,
        name=name,
        site_id=site_id
    )

    # Add it to Home Assistant
    async_add_entities([connection_button, listen_button, reboot_button, shutdown_button, restart_button, stop_button])
