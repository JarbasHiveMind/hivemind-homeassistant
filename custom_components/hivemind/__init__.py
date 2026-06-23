"""The HiveMind integration."""

import logging
import os
from dataclasses import dataclass

from hivemind_bus_client.client import HiveMessageBusClient
from hivemind_bus_client.identity import NodeIdentity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from json_database import JsonStorage
from ovos_utils.fakebus import FakeBus

from .const import DOMAIN, USER_AGENT

_LOGGER = logging.getLogger(__name__)


@dataclass
class HiveMindData:
    """Runtime data stored on the config entry."""

    bus: HiveMessageBusClient


type HiveMindConfigEntry = ConfigEntry[HiveMindData]


def _platforms(device_type: str) -> list[str]:
    """Platforms to set up for a given device type."""
    domains = ["binary_sensor", "button", "switch"]
    if device_type in ("voice_assistant", "media_player"):
        domains += ["notify", "media_player"]
        if device_type == "voice_assistant":
            domains += ["select", "sensor"]
    return domains


def _identity_path(hass: HomeAssistant, entry: ConfigEntry) -> str:
    """Per-entry identity file, stored under Home Assistant's config dir.

    The node identity (and the RSA key written alongside it) must live in a
    writable, persistent location that is *not* the integration's install
    directory — that directory can be read-only and is wiped on upgrade.
    """
    return hass.config.path(DOMAIN, entry.entry_id, "_identity.json")


def _build_bus(identity_file: str, data: dict) -> HiveMessageBusClient:
    """Construct the HiveMind bus client.

    Runs in an executor thread: ``JsonStorage`` and ``HiveMessageBusClient``
    both touch the filesystem (reading the identity, generating the RSA key),
    which must never happen on the event loop.
    """
    os.makedirs(os.path.dirname(identity_file), exist_ok=True)

    key = data["access_key"]
    password = data["password"]
    host = data["host"]
    port = data.get("port", 5678)
    self_signed = data.get("allow_self_signed", False)

    # explicitly pass a FakeBus so we keep a stable "default" session instead of
    # letting HiveMind assign a random session_id per (re)connection
    ovos_bus = FakeBus()
    ovos_bus.session_id = data.get("session_id", "default")

    # one identity, fully configured, then handed to the client — previously a
    # second, unconfigured NodeIdentity was passed, discarding site_id et al.
    identity = NodeIdentity(JsonStorage(identity_file))
    identity.access_key = key
    identity.password = password
    identity.site_id = data.get("site_id", "unknown")
    identity.name = data.get("name", "Home Assistant")

    return HiveMessageBusClient(
        key=key,
        password=password,
        port=port,
        host=host,
        useragent=USER_AGENT,
        self_signed=self_signed,
        internal_bus=ovos_bus,
        identity=identity,
    )


async def get_bus(hass: HomeAssistant, entry: ConfigEntry) -> HiveMessageBusClient:
    """Build the bus client off the event loop."""
    return await hass.async_add_executor_job(
        _build_bus, _identity_path(hass, entry), dict(entry.data)
    )


async def async_setup_entry(hass: HomeAssistant, entry: HiveMindConfigEntry) -> bool:
    """Set up HiveMind from a config entry."""
    bus = await get_bus(hass, entry)
    entry.runtime_data = HiveMindData(bus=bus)
    # kept for backwards compatibility with platform setup code
    entry.hm_bus = bus
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry

    async def _connect_later() -> None:
        try:
            await hass.async_add_executor_job(bus.connect)
            _LOGGER.info("Connected to HiveMind bus")
        except Exception as err:  # noqa: BLE001 - connect() retries internally
            _LOGGER.warning(
                "Initial HiveMind connection failed, will retry in background: %s",
                err,
            )

    hass.loop.create_task(_connect_later())

    await hass.config_entries.async_forward_entry_setups(
        entry, _platforms(entry.data.get("device_type", "voice_assistant"))
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HiveMindConfigEntry) -> bool:
    """Tear down the entry: unload platforms and close the bus connection."""
    platforms = _platforms(entry.data.get("device_type", "voice_assistant"))
    unloaded = await hass.config_entries.async_unload_platforms(entry, platforms)
    if unloaded:
        bus = entry.runtime_data.bus
        await hass.async_add_executor_job(bus.close)
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unloaded
