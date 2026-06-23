"""Shared base entity for the HiveMind integration.

Every HiveMind entity talks to the same :class:`HiveMessageBusClient` and shares
the same identity (device name + site id), availability rule (connected once the
handshake is set), and device grouping. This base collapses that duplication and,
crucially, gives entities a single place to register bus handlers so they can be
**removed again** when the entity is unloaded — otherwise reloading the
integration stacks duplicate callbacks on the bus.
"""

import logging
from typing import Callable

from hivemind_bus_client.client import HiveMessageBusClient
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class HiveMindEntity(Entity):
    """Common behaviour for every entity backed by a HiveMind bus connection."""

    def __init__(
        self, bus: HiveMessageBusClient, site_id: str, name: str, **kwargs
    ) -> None:
        self._name = name.replace(" ", "-")
        self.site_id = site_id
        self.bus = bus
        self._bus_handlers: list[tuple[str, Callable]] = []

    # -- bus handler lifecycle -------------------------------------------------

    def _register(self, event: str, handler: Callable) -> None:
        """Subscribe to a bus message and remember it for cleanup.

        Call this from :meth:`_subscribe`, not ``__init__`` — handlers are only
        live while the entity is added to Home Assistant.
        """
        self._bus_handlers.append((event, handler))
        self.bus.on_mycroft(event, handler)

    def _subscribe(self) -> None:
        """Override to register bus handlers via :meth:`_register`."""

    async def async_added_to_hass(self) -> None:
        """Register bus handlers once the entity is live."""
        self._subscribe()

    async def async_will_remove_from_hass(self) -> None:
        """Remove every bus handler this entity registered."""
        for event, handler in self._bus_handlers:
            try:
                self.bus.remove(event, handler)
            except Exception:  # noqa: BLE001 - best-effort cleanup
                _LOGGER.debug("Could not remove bus handler for %s", event)
        self._bus_handlers.clear()

    # -- common entity attributes ---------------------------------------------

    @property
    def available(self) -> bool:
        """A HiveMind entity is usable once the encrypted handshake completes."""
        return self.bus.handshake_event.is_set()

    @property
    def device_info(self) -> DeviceInfo:
        """Group all of a hub's entities under one Home Assistant device."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._name}-{self.site_id}-{self.bus._host}")},
            name=self._name,
            manufacturer="JarbasAI",
            model="HiveMindBus",
        )

    def _uid(self, slug: str) -> str:
        """Build a stable unique_id from a per-entity slug."""
        return f"hm-{slug}-{self._name}-{self.site_id}".replace(" ", "")
