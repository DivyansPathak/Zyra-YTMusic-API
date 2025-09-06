from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class SongDetails(BaseModel):
    """Detailed model for a song, used in search and recommendations."""
    title: str
    artist_name: str
    videoId: str
    thumbnail: Optional[str] = None
    duration: Optional[int] = None
    artistId: Optional[str] = None
    album_name: Optional[str] = None
    albumId: Optional[str] = None

class RelatedContent(BaseModel):
    """Model to bundle related content for a seed song."""
    more_from_artist: List[SongDetails] = Field(default_factory=list)
    more_from_album: List[SongDetails] = Field(default_factory=list)

class LyricsResult(BaseModel):
    """Model for returning lyrics or a message if not found."""
    lyrics: Optional[str] = None
    message: Optional[str] = None

class BatchSearchRequest(BaseModel):
    """Request body for searching multiple songs at once."""
    queries: List[str]