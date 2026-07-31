# Setup

## 1. Provision a HiveMind client on the hub

The integration needs an **admin** client key and password on the
`hivemind-core` hub, with the message-type allowlist from
[permissions](permissions.md). Add the client on the hub before you configure
Home Assistant.

## 2. Install the integration

Copy the `hivemind` folder into your Home Assistant `custom_components`
directory:

```bash
mkdir -p /config/custom_components
cp -r custom_components/hivemind /config/custom_components/
```

Restart Home Assistant.

## 3. Add the integration

In Home Assistant, go to **Settings → Devices & Services → Add Integration →
HiveMind**.

Fill in the config flow:

- **Device type**: `agent`, `media_player`, or `voice_assistant` (see
  [configuration](configuration.md)).
- **Name**: a friendly name for the device.
- **Host / Port**: the HiveMind hub address (e.g. `ws://192.168.1.10`, port
  `5678`).
- **Access key / Password**: the client credentials you provisioned in step 1.
- **Site id**, **legacy audio**, **allow self-signed**: optional.

The form checks the connection before it saves the entry. If the hub is
unreachable you get **"cannot connect"**. If it rejects the credentials you
get **"invalid auth"**. Either way, you find out immediately instead of from a
silent failure later.

## 4. Verify

Once added, the entities for the chosen device type appear under the new
HiveMind device: a connection sensor, buttons, switches, and, depending on
device type, a media player, notify, status sensors, and a listening-mode
select. See [entities](entities.md).

If the connection sensor stays off, check that the hub is reachable, the
client key is admin-privileged, and the required message types are allowed.

---
[Home](index.md) · [Configuration →](configuration.md)
