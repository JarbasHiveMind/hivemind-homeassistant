
import logging
from typing import Any, Dict
from hivemind_bus_client.client import HiveMessageBusClient
from hivemind_bus_client.message import HiveMessageType, HiveMessage
from ovos_utils.log import LOG
from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerDeviceClass,
    MediaPlayerEnqueue
)
from homeassistant.components.media_player.const import (
    MediaType, MediaPlayerEntityFeature, RepeatMode, MediaPlayerState, MediaClass
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_IDLE, STATE_PLAYING, STATE_PAUSED
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from ovos_bus_client.message import Message
from homeassistant.components import media_source
from homeassistant.components.media_player.browse_media import (
    async_process_play_media_url #, BrowseMedia, SearchMediaQuery, SearchMedia
)

from ovos_utils.ocp import (MediaType as OCPMediaType, MediaEntry, TrackState,
                            PlaybackType, PlaybackMode, PlayerState, MediaState, LoopState)


from .const import DOMAIN

mapping = {
    MediaType.MUSIC.value: OCPMediaType.MUSIC,
    MediaType.TVSHOW.value: OCPMediaType.VIDEO_EPISODES,
    MediaType.EPISODE.value: OCPMediaType.VIDEO_EPISODES,
    MediaType.MOVIE.value: OCPMediaType.MOVIE,
    MediaType.CHANNEL.value: OCPMediaType.TV,
    MediaType.GAME.value: OCPMediaType.GAME,
    MediaType.VIDEO.value: OCPMediaType.VIDEO

}


_LOGGER = logging.getLogger(__name__)
SUPPORT_HIVEMIND = (
        MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.STOP
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.PLAY_MEDIA
        | MediaPlayerEntityFeature.NEXT_TRACK
        | MediaPlayerEntityFeature.PREVIOUS_TRACK
        | MediaPlayerEntityFeature.REPEAT_SET
        | MediaPlayerEntityFeature.SHUFFLE_SET
        | MediaPlayerEntityFeature.SEEK
      #  | MediaPlayerEntityFeature.BROWSE_MEDIA
        | MediaPlayerEntityFeature.CLEAR_PLAYLIST
        | MediaPlayerEntityFeature.MEDIA_ANNOUNCE
        | MediaPlayerEntityFeature.MEDIA_ENQUEUE
      #  | MediaPlayerEntityFeature.GROUPING
      #  | MediaPlayerEntityFeature.SELECT_SOUND_MODE
      #  | MediaPlayerEntityFeature.SELECT_SOURCE
      #  | MediaPlayerEntityFeature.TURN_ON
      #  | MediaPlayerEntityFeature.TURN_OFF
)


class HiveMindMediaPlayer(MediaPlayerEntity):
    def __init__(self, bus: HiveMessageBusClient, site_id: str, name: str, legacy_audio:bool=False,**kwargs) -> None:
        """Initialize the service."""
        self._name = name.replace(" ", "-")
        self.site_id = site_id
        self.bus = bus
        self.legacy_audioservice = legacy_audio

        self._state = MediaPlayerState.ON
        self._volume_level = 0.5
        self._is_muted = False
        self._is_shuffle = False
        self._repeat = RepeatMode.OFF

        self._track_len = 0
        self._playback_pos = 0
        self._track_title = ""
        self._track_artist = ""
        self._track_album = ""
        self._image = ""
        self._uri = ""

        self._media_content_type = MediaType.MUSIC

        self.register_events()

    def handle_ocp_track_state(self, message: Message):
        LOG.info(f"track data: {message.data}")

    def handle_ocp_media_state(self, message: Message):
        LOG.info(f"media state: {message.data}")
        state = message.data["state"]
        if state == MediaState.END_OF_MEDIA:
            self._state = MediaPlayerState.IDLE
            self.schedule_update_ha_state()

    def handle_ocp_player_state(self, message: Message):
        LOG.info(f"player state: {message.data}")
        state = message.data["state"]
        if state == PlayerState.PAUSED:
            self._state = MediaPlayerState.PAUSED
        elif state == PlayerState.PLAYING:
            self._state = MediaPlayerState.PLAYING
        elif state == PlayerState.STOPPED:
            self._state = MediaPlayerState.IDLE
        self.schedule_update_ha_state()

    def handle_volume_update(self, message: Message):
        LOG.info(f"volume state: {message.data}")
        self._volume_level = message.data["percent"]
        self._is_muted = message.data["muted"]
        self.schedule_update_ha_state()

    def handle_track_info(self, message: Message):
        LOG.info(f"track info: {message.data}")
        self._track_title = message.data.get("title") or message.data.get("track")
        self._track_artist = message.data.get("artist")
        self._track_artist = message.data.get("album")
        self._image = message.data.get("image")
        self.schedule_update_ha_state()

    def handle_track_len(self, message: Message):
        LOG.info(f"track info: {message.data}")
        self._track_len = message.data["length"]
        self.schedule_update_ha_state()

    def handle_track_pos(self, message: Message):
        LOG.info(f"track info: {message.data}")
        self._playback_pos = message.data["position"]
        if "length" in message.data:
            self._track_len = message.data["length"]
        self.schedule_update_ha_state()

    def handle_status(self, message: Message):
        LOG.info(f"OCP status: {message.data}")
        player = message.data["state"]
        media = message.data["media_state"]
        repeat = message.data["repeat"]
        self._is_shuffle = message.data["shuffle"]

        if repeat == LoopState.REPEAT:
            self._repeat = RepeatMode.ALL
        elif repeat == LoopState.REPEAT_TRACK:
            self._repeat = RepeatMode.ONE
        else:
            self._repeat = RepeatMode.OFF

        if player == PlayerState.PAUSED:
            self._state = MediaPlayerState.PAUSED
        elif player == PlayerState.PLAYING:
            self._state = MediaPlayerState.PLAYING
        elif player == PlayerState.STOPPED:
            self._state = MediaPlayerState.IDLE

        if media == MediaState.END_OF_MEDIA:
            self._state = MediaPlayerState.IDLE
            self._playback_pos = self._track_len

        self.schedule_update_ha_state()

    def register_events(self):
        self.bus.on_mycroft("ovos.common_play.track_info.response",
                            self.handle_track_info)
        self.bus.on_mycroft("ovos.common_play.get_track_length.response",
                            self.handle_track_len)
        self.bus.on_mycroft("ovos.common_play.get_track_position.response",
                            self.handle_track_pos)
        self.bus.on_mycroft("mycroft.volume.get.response",
                            self.handle_volume_update)
        self.bus.on_mycroft("ovos.common_play.playback_time",
                            self.handle_track_pos)

        self.bus.on_mycroft("ovos.common_play.track.state",
                            self.handle_ocp_track_state)
        self.bus.on_mycroft("ovos.common_play.player.state",
                            self.handle_ocp_player_state)
        self.bus.on_mycroft("ovos.common_play.media.state",
                            self.handle_ocp_media_state)
        self.bus.on_mycroft("ovos.common_play.player.status.response",
                            self.handle_status)

    async def async_update(self):
        self.bus.emit_mycroft(Message("mycroft.volume.get"))
        self.bus.emit_mycroft(Message("ovos.common_play.track_info"))
        self.bus.emit_mycroft(Message("ovos.common_play.get_track_length"))
        self.bus.emit_mycroft(Message("ovos.common_play.get_track_position"))
        self.bus.emit_mycroft(Message("ovos.common_play.player.status"))

    @property
    def available(self) -> bool:
        return self.bus.handshake_event.is_set()

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, f"{self._name}-{self.site_id}-{self.bus._host}")
            },
            name=self._name,
            manufacturer="JarbasAI",
            model="HiveMindBus"
        )

    @property
    def name(self):
        """Name of the entity."""
        return f"hm-ocp-{self._name}"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID for this entity."""
        return f"{self.name}-{self.site_id}".replace(" ", "")

    def send_to_ovos(self, message: Message):
        payload = HiveMessage(HiveMessageType.BUS, message)
        try:
            LOG.info(f"HiveMind Message: {payload.serialize()}")
            self.bus.emit(payload)
        except Exception as e:
            LOG.error(f"Error from HiveMind messagebus: {e}")

    ######

    @property
    def app_name(self) -> str:
        """Name of the current running app."""
        return "OCP"

    @property
    def state(self) -> MediaPlayerState:
        if not self.bus.handshake_event.is_set():
            return MediaPlayerState.OFF
        return self._state

    @property
    def volume_level(self) -> float:
        return self._volume_level

    @property
    def is_volume_muted(self) -> bool:
        return self._is_muted

    @property
    def shuffle(self) -> bool:
        """True if shuffle is enabled."""
        return self._is_shuffle

    @property
    def repeat(self) -> RepeatMode:
        """Current repeat mode."""
        return self._repeat

    @property
    def media_album_artist(self) -> str:
        """	Album artist of current playing media, music track only."""
        return self._track_title

    @property
    def media_album_name(self) -> str:
        """Album name of current playing media, music track only."""
        return self._track_album

    @property
    def media_artist(self) -> str:
        """Artist of current playing media, music track only."""
        return self._track_artist

    @property
    def media_channel(self) -> str:
        """Channel currently playing."""
        return self._track_title

    @property
    def media_content_id(self) -> str:
        """Content ID of current playing media.."""
        return self._uri

    @property
    def media_content_type(self) -> MediaType:
        """Content type of current playing media."""
        return self._media_content_type

    @property
    def media_duration(self) ->int:
        """Duration of current playing media in seconds."""
        return self._track_len

    @property
    def media_episode(self) -> str:
        """Episode of current playing media, TV show only."""
        return self._track_title

    @property
    def media_image_remotely_accessible(self) -> bool:
        """True if property media_image_url is accessible outside of the home network."""
        return False

    @property
    def media_image_url(self) -> str:
        """	Image URL of current playing media."""
        return self._image

    @property
    def media_playlist(self) -> str:
        """	Title of Playlist currently playing."""
        return "OCP Now Playing"

    @property
    def media_position(self) -> int:
        """Position of current playing media in seconds."""
        return self._playback_pos

    @property
    def media_season(self) -> str:
        """Season of current playing media, TV show only."""
        return ""

    @property
    def media_series_title(self) -> str:
        """Title of series of current playing media, TV show only."""
        return self._track_title

    @property
    def media_title(self) -> str:
        """Title of current playing media."""
        return self._track_title

    @property
    def media_track(self) -> int:
        """Track number of current playing media, music track only."""
        return 0

    @property
    def supported_features(self):
        return SUPPORT_HIVEMIND

    async def async_play_media(
            self,
            media_type: str,
            media_id: str,
            enqueue: MediaPlayerEnqueue | None = None,
            announce: bool | None = None, **kwargs: Any
    ) -> None:
        """Play a piece of media."""
        if media_source.is_media_source_id(media_id):
            media_type = MediaType.MUSIC
            play_item = await media_source.async_resolve_media(self.hass, media_id, self.entity_id)
            # play_item returns a relative URL if it has to be resolved on the Home Assistant host
            # This call will turn it into a full URL
            media_id = async_process_play_media_url(self.hass, play_item.url)

        # Replace this with calling your media player play media function.
        #await self._media_player.play_url(media_id)
        LOG.info(f"media_type: {media_type}")
        LOG.info(f"media_id: {media_id}")
        LOG.info(f"enqueue: {enqueue}")
        LOG.info(f"announce: {announce}")

        if enqueue == MediaPlayerEnqueue.ADD:
            m = "ovos.common_play.playlist.queue"
        else: # REPLACE / PLAY / NEXT
            m = "ovos.common_play.play"

        if self.legacy_audioservice:
            message = Message('mycroft.audio.service.play',
                              {'tracks': [media_id]})
        else:
            entry = MediaEntry(
                uri=media_id,
                title="",
                artist="",
                length=0,
                match_confidence=100,
                skill_id="homeassistant.hivemind",
                skill_icon="https://raw.githubusercontent.com/home-assistant/brands/refs/heads/master/core_integrations/music_assistant/icon.png",
                image="",
                status=TrackState.QUEUED_AUDIO,
                media_type=mapping.get(media_type, OCPMediaType.MUSIC),
                playback=PlaybackType.AUDIO,
            )
            message = Message(m, {"media": entry.as_dict})
        self.send_to_ovos(message)


    async def async_media_play(self):
        """Send play command."""
        self._state = STATE_PLAYING
        if self.legacy_audioservice:
            message = Message('mycroft.audio.service.resume')
        else:
            message = Message('ovos.common_play.resume')
        LOG.info(f"play")
        self.send_to_ovos(message)
        self.async_write_ha_state()

    async def async_media_pause(self):
        self._state = STATE_PAUSED
        LOG.info(f"pause")
        if self.legacy_audioservice:
            message = Message('mycroft.audio.service.pause')
        else:
            message = Message('ovos.common_play.pause')

        self.send_to_ovos(message)
        self.async_write_ha_state()

    async def async_media_stop(self):
        self._state = STATE_IDLE
        LOG.info(f"stop")
        if self.legacy_audioservice:
            message = Message('mycroft.audio.service.stop')
        else:
            message = Message('ovos.common_play.stop')

        self.send_to_ovos(message)
        self.async_write_ha_state()

    async def async_set_volume_level(self, volume):
        self._volume_level = volume
        LOG.info(f"volume: {volume}")
        message = Message("mycroft.volume.set",
                          {"percent": volume})

        self.send_to_ovos(message)
        self.async_write_ha_state()

    async def async_volume_up(self, volume):
        self._volume_level += 0.1
        self._volume_level = min(self._volume_level, 1.0)
        LOG.info(f"volume: {volume}")
        message = Message("mycroft.volume.increase")

        self.send_to_ovos(message)
        self.async_write_ha_state()

    async def async_volume_down(self, volume):
        self._volume_level -= 0.1
        self._volume_level = max(self._volume_level, 0)
        LOG.info(f"volume: {volume}")
        message = Message("mycroft.volume.decrease")

        self.send_to_ovos(message)
        self.async_write_ha_state()

    async def async_mute_volume(self, mute):
        self._is_muted = mute
        LOG.info(f"set mute: {mute}")
        if mute:
            message = Message("mycroft.volume.mute")
        else:
            message = Message("mycroft.volume.unmute")

        self.send_to_ovos(message)
        self.async_write_ha_state()

    async def async_media_previous_track(self) -> None:
        """Send previous track command."""
        if self.legacy_audioservice:
            message = Message('mycroft.audio.service.prev')
        else:
            message = Message('ovos.common_play.previous')
        LOG.info("previous track")
        self.send_to_ovos(message)
        self.async_write_ha_state()

    async def async_media_next_track(self) -> None:
        """Send next track command."""
        LOG.info("next track")

        if self.legacy_audioservice:
            message = Message('mycroft.audio.service.next')
        else:
            message = Message('ovos.common_play.next')
        self.send_to_ovos(message)
        self.async_write_ha_state()

    async def async_media_seek(self, position: float) -> None:
        """Send seek command."""
        if self.legacy_audioservice:
            message = Message('mycroft.audio.service.set_track_position',
                              {"position": int(position * 1000)})
        else:
            message = Message('ovos.common_play.service.set_track_position',
                              {"position": position})
        self.send_to_ovos(message)
        LOG.info(f"seek: {position}")
        self._playback_pos = position
        self.async_write_ha_state()

    async def async_clear_playlist(self) -> None:
        """Clear players playlist."""
        message = Message('ovos.common_play.playlist.clear')
        self.send_to_ovos(message)
        LOG.info(f"clear playlist")
        self.async_write_ha_state()

    async def async_set_shuffle(self, shuffle: bool) -> None:
        """Enable/disable shuffle mode."""
        if shuffle:
            message = Message('ovos.common_play.shuffle.set')
        else:
            message = Message('ovos.common_play.shuffle.unset')

        LOG.info(f"set shuffle: {shuffle}")
        self.send_to_ovos(message)
        self._is_shuffle = shuffle
        self.async_write_ha_state()

    async def async_set_repeat(self, repeat: RepeatMode) -> None:
        """Set repeat mode."""
        if repeat == RepeatMode.OFF:
            message = Message('ovos.common_play.repeat.unset')
        elif repeat == RepeatMode.ALL:
            message = Message('ovos.common_play.repeat.set')
        else:
            # TODO - not exposed in bus, only via gui....
            message = Message('ovos.common_play.repeat.set')

        LOG.info(f"set repeat: {repeat}")
        self._repeat = repeat
        self.send_to_ovos(message)
        self.async_write_ha_state()

async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities
):
    """Set up notify service from a config entry."""
    # Get config values
    name = entry.data.get("name", "unnamed device")
    site_id = entry.data.get("site_id", "unknown")
    legacy_audio = entry.data.get("legacy_audio", False)

    # Create the connection button entity
    connection_button = HiveMindMediaPlayer(
        bus=entry.hm_bus,
        name=name,
        site_id=site_id,
        legacy_audio=legacy_audio
    )

    # Add it to Home Assistant
    async_add_entities([connection_button])
