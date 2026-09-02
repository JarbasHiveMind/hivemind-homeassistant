# HiveMind Integration for Home Assistant

A Home Assistant custom integration (`domain: hivemind`) that connects Home
Assistant to an [OpenVoiceOS](https://openvoiceos.com) instance over the
[HiveMind](https://github.com/JarbasHiveMind/HiveMind-core) protocol and exposes
OVOS as Home Assistant entities. You can install it through HACS (as a custom
repository) or by hand.

The integration does more than send voice commands. It controls the OVOS device
at a system level: audio playback, volume, microphone, sleep and wake, and
system power. It does this by injecting low-level bus messages over the
HiveMind link.

## Where it sits

Home Assistant connects to a HiveMind hub
([hivemind-core](https://github.com/JarbasHiveMind/HiveMind-core)) that runs
alongside an OVOS instance, using a HiveMind **client key**. Because the
integration injects low-level bus messages instead of only utterances, that
client must have **admin** privileges and the message-type allowlist described
under [Permissions Required](#permissions-required).

## Prerequisites

- A running HiveMind hub (`hivemind-core`) reachable from Home Assistant.
- An admin-privileged HiveMind client key and password registered on the hub
  for Home Assistant (see [Permissions Required](#permissions-required)).
- Home Assistant with access to its `config/custom_components/` directory.
- The integration declares the runtime requirement `hivemind_bus_client>=0.4.3`,
  which Home Assistant installs on first load.

## Installation

### HACS (custom repository)

1. Add `https://github.com/JarbasHiveMind/hivemind-homeassistant` as a custom
   repository (category *Integration*).
2. Install **HiveMind**.
3. Restart Home Assistant.

### Manual

1. Copy the `hivemind` folder into your Home Assistant
   `custom_components` directory:

   ```bash
   mkdir -p /config/custom_components
   cp -r custom_components/hivemind /config/custom_components/
   ```

2. Restart Home Assistant.

### Prerelease requirement

This integration depends on prerelease packages. Its dependency closure pulls in
`poorman-handshake`, whose required version is a prerelease, so the integration
must be installed in an environment where prerelease resolution is enabled. A
stock Home Assistant add flow, or a plain `pip install` that does not enable
prereleases, fails to resolve the dependencies and reports `RequirementsNotFound`.

Install into an environment that allows prereleases, for example:

```bash
uv pip install --prerelease=allow hivemind_bus_client
# or
pip install --pre hivemind_bus_client
```

This requirement stands until the HiveMind stack ships stable releases, at which
point stock resolution succeeds without the prerelease flag.

### Add the integration

Go to **Settings → Devices & Services → Add Integration → HiveMind**. The
config flow checks the hub connection before it saves the entry, so a bad host
or credential shows a clear `cannot connect` or `invalid auth` error instead of
a silent failure.

## Configuration fields

The config flow asks for these fields when you add the integration:

| Field | Default | Description |
| --- | --- | --- |
| `device_type` | `voice_assistant` | Which OVOS capabilities to expose (see below). |
| `name` | n/a | Friendly name for the device in Home Assistant. |
| `host` | n/a | HiveMind hub host (e.g. `ws://192.168.1.10`). |
| `access_key` | n/a | HiveMind client access key. |
| `password` | n/a | HiveMind client password. |
| `port` | `5678` | HiveMind WebSocket port. |
| `legacy_audio` | `false` | Use the legacy Audio Service instead of OCP. |
| `site_id` | `unknown` | OVOS site id. |
| `allow_self_signed` | `false` | Accept a self-signed TLS certificate. |

### Device types

The `device_type` field controls which platforms Home Assistant sets up:

| Type | Exposes |
| --- | --- |
| `agent` | binary sensors, buttons, switches (text input and output only). |
| `media_player` | the above, plus `notify` and `media_player`. |
| `voice_assistant` | the above, plus `select` and `sensor` (full mic, VAD, and STT device). |

See [`docs/`](docs/index.md) for the full setup, entity, and permissions guide.

## Usage

Once you add a HiveMind device, its entities appear in Home Assistant: a
connection sensor, control buttons and switches, and — depending on
`device_type` — a media player, a notify service, status sensors, and a
listening-mode selector.

![Home Assistant entities](https://github.com/user-attachments/assets/f4a56e28-96e1-470e-99cc-0f9e8707b37f)

Send text to the OVOS instance with the `notify` service so it speaks the text
through TTS. Control playback with the `media_player` entity, which maps Home
Assistant `MediaType` values to OVOS OCP media types (music, video, movie,
episode, TV channel, game, and others). It also works with sources exposed by
[ovos-skill-music-assistant](https://github.com/HiveMindInsiders/ovos-skill-music-assistant).

![Media player entity](https://github.com/user-attachments/assets/9bb3bdba-bce0-47f5-b837-6f934eff67ef)

## Permissions Required

This integration does more than send voice queries: it injects and controls
bus messages directly. The client connecting to HiveMind must have **admin**
privileges and permission to use the following message types.

### ovos-core
- `mycroft.stop`
- `mycroft.skills.is_alive`
- `mycroft.skills.is_ready`

### ovos-dinkum-listener
- `mycroft.voice.is_alive`
- `mycroft.voice.is_ready`
- `mycroft.mic.listen`
- `mycroft.mic.mute`
- `mycroft.mic.unmute`
- `mycroft.mic.get_status`
- `recognizer_loop:sleep`
- `recognizer_loop:wake_up`
- `recognizer_loop:state.get`
- `recognizer_loop:state.set`

### ovos-gui
- `mycroft.gui_service.is_alive`
- `mycroft.gui_service.is_ready`

### ovos-audio
- `speak`
- `mycroft.audio.is_alive`
- `mycroft.audio.is_ready`
- `mycroft.audio.speak.status`

#### OCP (OpenVoiceOS Common Play)
- `ovos.common_play.player.status`
- `ovos.common_play.track_info`
- `ovos.common_play.get_track_length`
- `ovos.common_play.get_track_position`
- `ovos.common_play.playlist.queue`
- `ovos.common_play.resume`
- `ovos.common_play.pause`
- `ovos.common_play.stop`
- `ovos.common_play.previous`
- `ovos.common_play.next`
- `ovos.common_play.set_track_position`
- `ovos.common_play.playlist.clear`
- `ovos.common_play.shuffle.set`
- `ovos.common_play.shuffle.unset`
- `ovos.common_play.repeat.set`
- `ovos.common_play.repeat.unset`
- `ovos.common_play.repeat.one`

#### Audio Service
*(only if you enable it manually, for systems without the OCP Audio Plugin)*

- `mycroft.audio.service.play`
- `mycroft.audio.service.resume`
- `mycroft.audio.service.pause`
- `mycroft.audio.service.stop`
- `mycroft.audio.service.prev`
- `mycroft.audio.service.next`
- `mycroft.audio.service.set_track_position`

### PHAL
- `mycroft.phal.is_alive`
- `mycroft.phal.is_ready`

#### ovos-phal-plugin-alsa
- `mycroft.volume.get`
- `mycroft.volume.increase`
- `mycroft.volume.decrease`
- `mycroft.volume.mute`
- `mycroft.volume.unmute`

#### ovos-phal-plugin-system
- `system.reboot`
- `system.shutdown`
- `system.mycroft.service.restart`
- `system.ssh.status`

#### ovos-phal-plugin-camera

*(work in progress)*

- `ovos.phal.camera.ping`
- `ovos.phal.camera.get`
- `ovos.phal.camera.open`
- `ovos.phal.camera.close`

### Security notes

- This integration directly manipulates OpenVoiceOS state.
- Proper permission management is critical for security.
- Only connect trusted Home Assistant instances to your HiveMind hub.

## Related Projects

- [hivemind-homeassistant](https://github.com/JarbasHiveMind/hivemind-homeassistant) (this repo) lets HiveMind show up as a player in Home Assistant.
- [hivemind-player-protocol](https://github.com/HiveMindInsiders/hivemind-player-protocol) turns any device into a standalone HiveMind OCP player.
- [ovos-skill-music-assistant](https://github.com/HiveMindInsiders/ovos-skill-music-assistant) lets OVOS search media in Music Assistant sources.
- [ovos-media-plugin-mass](https://github.com/HiveMindInsiders/ovos-media-plugin-mass) lets OVOS control Music Assistant players.

## License

[MIT](LICENSE)
