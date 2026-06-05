# HiveMind for Home Assistant

A manual-install Home Assistant integration that connects HA to an OpenVoiceOS
instance over HiveMind and exposes OVOS as Home Assistant entities — media player,
notify, sensors, switches, buttons, and a listening-mode select.

- [Setup](setup.md)
- [Configuration](configuration.md)
- [Entities](entities.md)
- [Permissions](permissions.md)

## Where it sits

Home Assistant acts as a HiveMind **client** connecting to a
[hivemind-core](https://github.com/JarbasHiveMind/HiveMind-core) hub that runs
alongside an OVOS instance. Unlike a voice satellite, this integration injects
low-level OVOS bus messages, so its client key must be admin-privileged with the
right message-type allowlist (see [permissions](permissions.md)).

## How it connects

On setup the integration builds a `HiveMessageBusClient` from the configured host,
port, access key, and password, and connects in a background task with its own
retry/backoff. An initial connection failure is logged as a warning rather than
being fatal, so Home Assistant keeps the device and reconnects when the hub is
reachable.
