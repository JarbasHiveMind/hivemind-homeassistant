"""Send notifications to HiveMind devices"""

import os

from hivemind_bus_client.client import HiveMessageBusClient
from hivemind_bus_client.identity import NodeIdentity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from json_database import JsonStorage
from ovos_utils.fakebus import FakeBus
from ovos_utils.log import LOG, init_service_logger
from .const import DOMAIN


async def get_bus(entry) -> HiveMessageBusClient:
    # Get config values
    key = entry.data["access_key"]
    password = entry.data["password"]
    host = entry.data["host"]
    port = entry.data.get("port", 5678)
    self_signed = entry.data.get("allow_self_signed", False)
    ovos_bus = FakeBus() # explicitly passed so we use "default" session, otherwise HM assigns random session_id
    ovos_bus.session_id = entry.data.get("session_id", "default")
    identity_file = JsonStorage(f"{os.path.dirname(__file__)}/_identity.json")
    return HiveMessageBusClient(key=key,
                                password=password,
                                port=port,
                                host=host,
                                useragent="HomeAssistantV0.0.2",
                                self_signed=self_signed,
                                internal_bus=ovos_bus,
                                identity=NodeIdentity(identity_file))


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    init_service_logger("hivemind-homeassistant")
    # Store config entry for this domain
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry

    entry.hm_bus = await get_bus(entry)

    entry.hm_bus.connect(site_id=entry.data.get("site_id", "unknown"))
    await hass.config_entries.async_forward_entry_setups(entry, ["notify", "sensor", "button", "media_player"])
    return True
