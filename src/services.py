# services.py

from typing import List, Dict, Any, Optional
from ytmusicapi import YTMusic
import logging
import traceback

from .schemas import SongDetails, RelatedContent, LyricsResult

ytmusic = YTMusic()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Helper function to convert duration strings to seconds ---
def _convert_duration_to_seconds(duration_str: Optional[str]) -> Optional[int]:
    """Converts MM:SS or HH:MM:SS strings to an integer of seconds."""
    if not isinstance(duration_str, str): return None
    try:
        parts = list(map(int, duration_str.split(':')))
        seconds = sum(part * 60**i for i, part in enumerate(reversed(parts)))
        return seconds
    except (ValueError, IndexError):
        return None

# --- Specialized Parsers for different data sources ---

def _parse_search_result_item(entry: Dict[str, Any]) -> Optional[SongDetails]:
    """Specialized parser for songs from search results."""
    if not entry: return None
    return SongDetails(
        title=entry.get('title'),
        artist_name=', '.join([artist['name'] for artist in entry.get('artists', [])]),
        videoId=entry.get('videoId'),
        thumbnail=entry['thumbnails'][-1]['url'] if entry.get('thumbnails') else None,
        duration=entry.get('duration_seconds'),
        artistId=entry.get('artists', [{}])[0].get('id'),
        album_name=entry.get('album', {}).get('name') if entry.get('album') else None,
        albumId=entry.get('album', {}).get('id') if entry.get('album') else None
    )

def _parse_watch_playlist_item(entry: Dict[str, Any]) -> Optional[SongDetails]:
    """Specialized parser for songs from a 'watch playlist' (Up Next)."""
    if not entry: return None
    return SongDetails(
        title=entry.get('title'),
        artist_name=', '.join([artist['name'] for artist in entry.get('artists', [])]),
        videoId=entry.get('videoId'),
        thumbnail=entry['thumbnail'][-1]['url'] if entry.get('thumbnail') else None,
        duration=_convert_duration_to_seconds(entry.get('length')),
        artistId=entry.get('artists', [{}])[0].get('id'),
        album_name=entry.get('album', {}).get('name') if entry.get('album') else None,
        albumId=entry.get('album', {}).get('id') if entry.get('album') else None
    )

def _parse_artist_page_song(entry: Dict[str, Any]) -> Optional[SongDetails]:
    """
    Specialized parser for songs from an artist's page.
    NOTE: This data source does NOT provide duration.
    """
    if not entry: return None
    return SongDetails(
        title=entry.get('title'),
        artist_name=', '.join([artist['name'] for artist in entry.get('artists', [])]),
        videoId=entry.get('videoId'),
        thumbnail=entry['thumbnails'][-1]['url'] if entry.get('thumbnails') else None,
        duration=None, # Duration is not provided by the API in this context
        artistId=entry.get('artists', [{}])[0].get('id'),
        album_name=entry.get('album', {}).get('name') if entry.get('album') else None,
        albumId=entry.get('album', {}).get('id') if entry.get('album') else None
    )

# --- SERVICE FUNCTIONS (Cleaned and Corrected) ---

def search_for_song(query: str, limit: int) -> List[SongDetails]:
    raw_results = ytmusic.search(query=query, filter='songs', limit=limit)
    return [_parse_search_result_item(entry) for entry in raw_results if entry]

def get_upnext_recommendations(video_id: str, limit: int = 10) -> List[SongDetails]:
    watch_playlist = ytmusic.get_watch_playlist(videoId=video_id, limit=limit + 1)
    # Skip the first track because it's the currently playing one
    return [_parse_watch_playlist_item(track) for track in watch_playlist['tracks'][1:limit+1]]

def get_songs_by_artist(artist_id: str, limit: int = 10) -> List[SongDetails]:
    try:
        artist_page = ytmusic.get_artist(channelId=artist_id)
        song_results = artist_page.get('songs', {}).get('results', [])
        if song_results:
            return [_parse_artist_page_song(song) for song in song_results[:limit]]
        return []
    except Exception as e:
        logging.error(f"Could not fetch artist tracks for artistId {artist_id}: {e}")
        return []

def get_songs_by_album(album_id: str) -> List[SongDetails]:
    """NOTE: This may be unstable due to issues in the ytmusicapi library."""
    try:
        album_page = ytmusic.get_album(browseId=album_id)
        return [_parse_watch_playlist_item(track) for track in album_page.get('tracks', [])]
    except Exception as e:
        logging.error(f"Could not fetch album tracks for albumId {album_id}: {e}")
        return []

def get_related_content(video_id: str) -> RelatedContent:
    """Gets related content by calling the new, dedicated service functions."""
    seed_song = None
    try:
        search_results = search_for_song(query=video_id, limit=1)
        if search_results:
            seed_song = search_results[0]
    except Exception as e:
        logging.error(f"Failed to find seed song for related content with videoId {video_id}: {e}")
        return RelatedContent()

    artist_tracks, album_tracks = [], []
    if seed_song:
        if seed_song.artistId:
            artist_tracks = get_songs_by_artist(seed_song.artistId, limit=10)
        if seed_song.albumId:
            album_tracks = get_songs_by_album(seed_song.albumId)

    return RelatedContent(more_from_artist=artist_tracks, more_from_album=album_tracks)

def get_song_lyrics(video_id: str) -> LyricsResult:
    try:
        lyrics_data = ytmusic.get_lyrics(browseId=f"MPLYt{video_id}")
        if lyrics_data and lyrics_data.get('lyrics'):
            return LyricsResult(lyrics=lyrics_data['lyrics'])
        else:
            return LyricsResult(message="Lyrics not found for this song.")
    except Exception:
        return LyricsResult(message="Could not retrieve lyrics.")