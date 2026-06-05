# Entities

Which entities appear depends on the configured `device_type` (see
[configuration](configuration.md)). The table notes the minimum device type that
exposes each.

## Always (all device types)

| Entity | Platform | Purpose |
| --- | --- | --- |
| Connection | binary_sensor | Whether the HiveMind link is up. |
| Alive / Ready | binary_sensor | OVOS service liveness/readiness. |
| Speaking | binary_sensor | Whether OVOS is currently speaking. |
| Reconnect | button | Re-establish the HiveMind connection. |
| Reboot / Shutdown | button | System power control (via PHAL). |
| Restart service | button | Restart the OVOS service. |
| Mic listen | button | Trigger a listening cycle. |
| Stop | button | `mycroft.stop`. |
| SSH | switch | Toggle SSH (PHAL system plugin). |
| Volume mute | switch | Mute/unmute output volume. |
| Mic mute | switch | Mute/unmute the microphone. |
| Sleep mode | switch | Put OVOS to sleep / wake it. |

## `media_player` and `voice_assistant`

| Entity | Platform | Purpose |
| --- | --- | --- |
| Media player | media_player | OCP-backed playback, volume, transport controls. |
| Notify | notify | Send text to OVOS to speak (TTS). |

The media player maps Home Assistant `MediaType` values to OVOS OCP media types
(music, video, movie, episode, TV channel, game, …). With `legacy_audio` enabled it
drives the legacy Audio Service instead of OCP.

## `voice_assistant` only

| Entity | Platform | Purpose |
| --- | --- | --- |
| Listener state | sensor | Current listener/recognizer state. |
| Listening mode | select | Switch the listening mode. |

These cover the microphone / VAD / STT side that only a full voice assistant device
exposes.
