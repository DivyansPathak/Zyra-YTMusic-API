from typing import List, Dict, Any, Optional
from ytmusicapi import YTMusic
import logging

from .schemas import SongDetails, RelatedContent, LyricsResult

ytmusic = YTMusic()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _parse_song_data(entry: Dict[str, Any]) -> Optional[SongDetails]:
    if not entry: return None
    artist_names = ', '.join([artist['name'] for artist in entry.get('artists', []) if artist.get('name')])
    artist_id = entry.get('artists', [{}])[0].get('id')
    album_info = entry.get('album')
    return SongDetails(
        title=entry.get('title', 'N/A'),
        artist_name=artist_names or 'N/A',
        videoId=entry.get('videoId'),
        thumbnail=entry['thumbnails'][-1]['url'] if entry.get('thumbnails') else None,
        duration=entry.get('duration_seconds'),
        artistId=artist_id,
        album_name=album_info.get('name') if album_info else None,
        albumId=album_info.get('id') if album_info else None
    )

def _parse_playlist_data(entries: List[Dict[str, Any]]) -> List[SongDetails]:
    return [_parse_song_data(entry) for entry in entries if entry]

# --- SERVICE FUNCTIONS ---
def search_for_song(query: str, limit: int) -> List[SongDetails]:
    raw_results = ytmusic.search(query=query, filter='songs', limit=limit)
    return [_parse_song_data(entry) for entry in raw_results if entry]

def get_upnext_recommendations(video_id: str, limit: int = 10) -> List[SongDetails]:
    watch_playlist = ytmusic.get_watch_playlist(videoId=video_id, limit=limit + 1)
    return _parse_playlist_data(watch_playlist['tracks'][1:])

# --- FIX is in this function ---
def get_related_content(video_id: str) -> RelatedContent:
    """
    Gets related songs by the same artist and from the same album.
    This version is more robust because it uses the search function to get seed data.
    """
    seed_song = None
    try:
        # FIX: Search for the videoId to get its full, parsed details reliably.
        search_results = search_for_song(query=video_id, limit=1)
        if search_results:
            seed_song = search_results[0]
    except Exception as e:
        logging.error(f"Failed to find seed song for related content with videoId {video_id}: {e}")
        return RelatedContent() # Return empty object on failure

    artist_tracks, album_tracks = [], []
    if seed_song:
        # Get more from the artist if an artistId exists
        if seed_song.artistId:
            try:
                artist_page = ytmusic.get_artist(artistId=seed_song.artistId)
                if artist_page.get('songs', {}).get('results'):
                    artist_tracks = _parse_playlist_data(artist_page['songs']['results'][:10])
            except Exception as e:
                # FIX: Added logging to see the actual error instead of silently failing
                logging.error(f"Could not fetch artist tracks for artistId {seed_song.artistId}: {e}")

        # Get more from the album if an albumId exists
        if seed_song.albumId:
            try:
                album_page = ytmusic.get_album(browseId=seed_song.albumId)
                album_tracks = _parse_playlist_data(album_page['tracks'])
            except Exception as e:
                # FIX: Added logging to see the actual error
                logging.error(f"Could not fetch album tracks for albumId {seed_song.albumId}: {e}")

    return RelatedContent(more_from_artist=artist_tracks, more_from_album=album_tracks)

def get_song_lyrics(video_id: str) -> LyricsResult:
    try:
        # The browseId for lyrics is constructed this way
        lyrics_data = ytmusic.get_lyrics(browseId=f"MPLYt{video_id}")
        if lyrics_data and lyrics_data.get('lyrics'):
            return LyricsResult(lyrics=lyrics_data['lyrics'])
        else:
            return LyricsResult(message="Lyrics not found for this song.")
    except Exception:
        return LyricsResult(message="Could not retrieve lyrics.")