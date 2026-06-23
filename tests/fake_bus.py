"""A fake HiveMessageBusClient for tests that need no real hub.

It records emitted messages and lets a test fire bus events into the handlers
the entities registered, so entity state logic can be exercised deterministically.
"""

import threading

from ovos_bus_client.message import Message


class FakeHiveBus:
    """Drop-in stand-in for HiveMessageBusClient (the bits the integration uses)."""

    def __init__(self, *, connected: bool = True) -> None:
        self.handshake_event = threading.Event()
        self.connected_event = threading.Event()
        # whether a later connect() call is allowed to complete the handshake
        self._connectable = connected
        if connected:
            self.handshake_event.set()
            self.connected_event.set()
        self._host = "ws://testhub"
        self.site_id = "test"
        self.protocol = object()
        self.crypto_key = b"k"
        self.handlers: dict[str, list] = {}
        self.emitted: list = []

    # -- registration ---------------------------------------------------------
    def on_mycroft(self, event: str, handler) -> None:
        self.handlers.setdefault(event, []).append(handler)

    def remove(self, event: str, handler) -> None:
        if handler in self.handlers.get(event, []):
            self.handlers[event].remove(handler)

    # -- emission -------------------------------------------------------------
    def emit_mycroft(self, message) -> None:
        self.emitted.append(message)

    def emit(self, message) -> None:
        self.emitted.append(message)

    # -- lifecycle ------------------------------------------------------------
    def connect(self, *args, **kwargs) -> None:
        if self._connectable:
            self.handshake_event.set()
            self.connected_event.set()

    def close(self) -> None:
        self.handshake_event.clear()
        self.connected_event.clear()

    def wait_for_handshake(self, timeout: float = 0) -> bool:
        return self.handshake_event.is_set()

    # -- test helpers ---------------------------------------------------------
    def inject(self, event: str, data: dict | None = None) -> None:
        """Fire a bus event into every handler registered for it."""
        for handler in list(self.handlers.get(event, [])):
            handler(Message(event, data or {}))

    def handler_count(self, event: str) -> int:
        return len(self.handlers.get(event, []))
