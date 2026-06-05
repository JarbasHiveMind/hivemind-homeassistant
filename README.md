# HiveMind Integration for Home Assistant

A **manual-install** Home Assistant custom integration (`domain: hivemind`) that
connects Home Assistant to an [OpenVoiceOS](https://openvoiceos.com) instance over
the [HiveMind](https://github.com/JarbasHiveMind/HiveMind-core) protocol and
exposes OVOS as Home Assistant entities.

It does more than send voice commands: it controls the OVOS device at a system
level — audio playback, volume, microphone, sleep/wake, and system power — by
injecting low-level bus messages over the HiveMind link.

## Where it sits

Home Assistant connects to a HiveMind hub
([hivemind-core](https://github.com/JarbasHiveMind/HiveMind-core)) running
alongside an OVOS instance, using a HiveMind **client key**. Because the
integration injects low-level bus messages rather than just utterances, that client
must have **admin** privileges and the message-type allowlist described under
[Permissions Required](#permissions-required).

## Prerequisites

- A running HiveMind hub (`hivemind-core`) reachable from Home Assistant.
- An admin-privileged HiveMind client key + password registered on the hub for
  Home Assistant (see [Permissions Required](#permissions-required)).
- Home Assistant with access to its `config/custom_components/` directory.
- The integration declares the runtime requirement `hivemind_bus_client>=0.4.3`
  (pulled in by Home Assistant on first load).

## Configuration fields

When you add the integration (Settings → Devices & Services → Add Integration →
HiveMind), the config flow asks for:

| Field | Default | Description |
| --- | --- | --- |
| `device_type` | `voice_assistant` | Which OVOS capabilities to expose (see below). |
| `name` | — | Friendly name for the device in Home Assistant. |
| `host` | — | HiveMind hub host (e.g. `ws://192.168.1.10`). |
| `access_key` | — | HiveMind client access key. |
| `password` | — | HiveMind client password. |
| `port` | `5678` | HiveMind WebSocket port. |
| `legacy_audio` | `false` | Use the legacy Audio Service instead of OCP. |
| `site_id` | `unknown` | OVOS site id. |
| `allow_self_signed` | `false` | Accept a self-signed TLS certificate. |

### Device types

The `device_type` controls which platforms are set up:

| Type | Exposes |
| --- | --- |
| `agent` | binary sensors, buttons, switches (text I/O only). |
| `media_player` | the above + `notify` + `media_player`. |
| `voice_assistant` | the above + `select` + `sensor` (full mic/VAD/STT device). |

See [`docs/`](docs/index.md) for the full setup, entity, and permissions walkthrough.

---

## Related Projects:

- [hivemind-homeassistant](https://github.com/JarbasHiveMind/hivemind-homeassistant) (this repo) allows HiveMind to show up as a player in Home Assistant
- [hivemind-player-protocol](https://github.com/HiveMindInsiders/hivemind-player-protocol) turn any device into a standalone HiveMind OCP player
- [ovos-skill-music-assistant](https://github.com/HiveMindInsiders/ovos-skill-music-assistant) allows OVOS to search media in MA sources
- [ovos-media-plugin-mass](https://github.com/HiveMindInsiders/ovos-media-plugin-mass) allows OVOS to control MA players
  
---

## Manual Installation

1. Copy the `hivemind` folder into your Home Assistant `custom_components` directory:

   ```bash
   mkdir -p /config/custom_components
   cp -r custom_components/hivemind /config/custom_components/
   ```

2. Restart Home Assistant.

3. Add the HiveMind integration via the Home Assistant UI:  
   **Settings → Devices & Services → Add Integration → HiveMind**

---

## Home Assistant Setup

![setup](https://github.com/user-attachments/assets/5b34c714-3faa-4c8b-8c84-e438c20085fb)

Once a HiveMind device is added to HomeAssistant you will have several entities available

![image](https://github.com/user-attachments/assets/f4a56e28-96e1-470e-99cc-0f9e8707b37f)

controls

![image](https://github.com/user-attachments/assets/d76cd0a6-7dc1-4af8-93d3-73668e11a405)

media player

![image](https://github.com/user-attachments/assets/9bb3bdba-bce0-47f5-b837-6f934eff67ef)

notify

![image](https://github.com/user-attachments/assets/57a797f7-06a6-4d12-9eb0-a3496fe32748)

status sensors

![image](https://github.com/user-attachments/assets/5f98232b-1243-445f-98ed-bb03e23a50b5)


## Music Assistant

![image](https://github.com/user-attachments/assets/1b0adcb0-bb92-4125-82ee-36367ce2bf60)


---

## Permissions Required

Since this integration does **more than just voice queries**, it requires **low-level permissions** to inject and control bus messages directly.  

The client connecting to HiveMind must have **admin privileges** and permission to access the following message types:

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
*(only if enabled manually — for systems without the OCP Audio Plugin)*

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

(*work in progress*)

- `ovos.phal.camera.ping`
- `ovos.phal.camera.get`
- `ovos.phal.camera.open`
- `ovos.phal.camera.close`

---

## Notes

- This integration **directly manipulates OpenVoiceOS** state
- Proper permission management is critical for security.
- Only trusted Home Assistant instances should connect to your HiveMind server.

