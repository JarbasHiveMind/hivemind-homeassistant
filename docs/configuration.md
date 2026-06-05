# Configuration

Configuration is done entirely through the Home Assistant config flow when adding
the integration; there is no YAML.

## Fields

| Field | Default | Description |
| --- | --- | --- |
| `device_type` | `voice_assistant` | Which OVOS capabilities to expose. |
| `name` | — | Friendly name for the device in Home Assistant. |
| `host` | — | HiveMind hub host (e.g. `ws://192.168.1.10`). |
| `access_key` | — | HiveMind client access key. |
| `password` | — | HiveMind client password. |
| `port` | `5678` | HiveMind WebSocket port. |
| `legacy_audio` | `false` | Use the legacy Audio Service instead of OCP for playback. |
| `site_id` | `unknown` | OVOS site id. |
| `allow_self_signed` | `false` | Accept a self-signed TLS certificate from the hub. |

## Device types

`device_type` selects which platforms are set up for the device:

| Type | Description | Platforms |
| --- | --- | --- |
| `agent` | Text input/output only (e.g. an LLM-backed OVOS). | binary_sensor, button, switch |
| `media_player` | Audio output (playback, volume, TTS). | the above + notify + media_player |
| `voice_assistant` | Full device: agent + audio out + audio in (mic, VAD, wake word, STT). | the above + select + sensor |

## Identity storage

The integration writes its HiveMind node identity to `_identity.json` inside the
installed `custom_components/hivemind/` package directory. The bus uses a fixed
session id (`default`) so the hub does not assign a random session per connection.
