"""Send notifications to HiveMind devices"""

import logging
import os

from hivemind_bus_client.client import HiveMessageBusClient
from hivemind_bus_client.identity import NodeIdentity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from json_database import JsonStorage
from ovos_utils.fakebus import FakeBus

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def get_bus(entry) -> HiveMessageBusClient:
    # Get config values
    key = entry.data["access_key"]
    password = entry.data["password"]
    host = entry.data["host"]
    port = entry.data.get("port", 5678)
    self_signed = entry.data.get("allow_self_signed", False)

    ovos_bus = FakeBus()  # explicitly passed so we use "default" session, otherwise HM assigns random session_id
    ovos_bus.session_id = entry.data.get("session_id", "default")

    identity_file = JsonStorage(f"{os.path.dirname(__file__)}/_identity.json")
    identity = NodeIdentity(identity_file)
    identity.site_id = entry.data.get("site_id", "unknown")
    return HiveMessageBusClient(key=key,
                                password=password,
                                port=port,
                                host=host,
                                useragent="HomeAssistantV0.0.2",
                                self_signed=self_signed,
                                internal_bus=ovos_bus,
                                identity=NodeIdentity(identity_file))


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    device_type = entry.data.get("device_type", "voice_assistant")

    # Store config entry for this domain
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry

    entry.hm_bus = await get_bus(entry)

    async def _connect_later():
        try:
            await hass.async_add_executor_job(entry.hm_bus.connect)
            _LOGGER.info("Connected to HiveMind bus")
        except Exception as e:
            _LOGGER.warning(f"Initial HiveMind connection failed, will retry in background: {e}")
            # hm_bus.connect() already has its own retry/backoff logic


    hass.loop.create_task(_connect_later())

    domains = ["binary_sensor", "button", "switch"]
    if device_type in ["voice_assistant", "media_player"]:
        domains.extend(["notify", "media_player"])
        if device_type == "voice_assistant":
            domains += ["select", "sensor"]
    await hass.config_entries.async_forward_entry_setups(entry, domains)
    return True
