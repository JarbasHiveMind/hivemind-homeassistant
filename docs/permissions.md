# Permissions

This integration does more than send voice queries — it injects and controls OVOS
bus messages directly. The HiveMind client it connects with must therefore have
**admin** privileges and be allowed the specific message types it uses.

## Why admin

Each entity maps to OVOS bus messages: buttons/switches send control messages
(stop, reboot, mic mute, volume, sleep), the media player sends OCP transport
messages, and the sensors subscribe to status messages. A read-only or
utterance-only client cannot drive these, so the client key must be admin with the
message types allowlisted.

Concretely, the integration pins the `default` OVOS session so the hub does not
assign a random session per reconnection — and `hivemind-core` only permits the
`default` session for admin clients. A non-admin client is rejected from that
session, so provision the client with `--admin`:

```bash
hivemind-core add-client --admin
```

## The allowlist

The full, exact list of required message types — grouped by OVOS service
(ovos-core, ovos-dinkum-listener, ovos-gui, ovos-audio, OCP, the optional Audio
Service, PHAL and its alsa/system/camera plugins) — is maintained in the
[README "Permissions Required" section](../README.md#permissions-required).

Provision the HiveMind client on the hub with those message types allowed before
adding the integration.

## Security

- Only connect trusted Home Assistant instances to your HiveMind hub.
- The integration directly manipulates OVOS state; scope the client's allowlist to
  what you actually use.
