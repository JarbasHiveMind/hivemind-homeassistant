DOMAIN = "hivemind"

# Reported to the hub as the satellite useragent. Bumped with manifest.json.
USER_AGENT = "HomeAssistant"

DEVICE_TYPES = {
    "agent": "Agent — text only (OpenVoiceOS, LLM ...)",
    "media_player": "Media Player — audio out only (playback, volume, TTS ...)",
    "voice_assistant": "Voice Assistant — full two-way voice (mic in, speaks back) (Agent + Audio output + Audio input: mic, VAD, wake word, STT ...)"
}