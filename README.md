# HiveMind Integration for Home Assistant

This is a **manual install** Home Assistant integration for connecting to an OpenVoiceOS instance via HiveMind

It allows Home Assistant to directly control and interact with an OVOS device at a system level — not just sending voice commands, but also manipulating services like audio playback, volume, and system power.

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

## Permissions Required

Since this integration does **more than just voice queries**, it requires **low-level permissions** to inject and control bus messages directly.  

The client connecting to HiveMind must have **admin privileges** and permission to access the following message types:

### ovos-core
- `mycroft.skills.is_alive`
- `mycroft.skills.is_ready`

### ovos-dinkum-listener
- `mycroft.speech.is_alive`
- `mycroft.speech.is_ready`

### ovos-gui
- `mycroft.gui_service.is_alive`
- `mycroft.gui_service.is_ready`

### ovos-audio
- `speak`
- `mycroft.audio.is_alive`
- `mycroft.audio.is_ready`

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

### PHAL (Personal Home Automation Layer)
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

(**work in progress**)

- `ovos.phal.camera.ping`
- `ovos.phal.camera.get`
- `ovos.phal.camera.open`
- `ovos.phal.camera.close`

---

## Notes

- This integration **directly manipulates OpenVoiceOS** state
- Proper permission management is critical for security.
- Only trusted Home Assistant instances should connect to your HiveMind server.

