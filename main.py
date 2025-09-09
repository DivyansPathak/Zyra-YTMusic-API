import asyncio
from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from typing import List


from src.schemas import *
from src.services import *

app = FastAPI(
    title="Music Metadata API",
    description="Provides metadata for searching, recommendations, and lyrics from YouTube Music.",
    version="4.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/search", response_model=List[SongDetails])
async def search(query: str, limit: int = 10):
    if not query:
        raise HTTPException(status_code=400, detail="Search query is required.")
    try:
        return await asyncio.to_thread(search_for_song, query, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

@app.get("/upnext", response_model=List[SongDetails])
async def upnext(
    video_id: str = Query(..., description="The videoId of the currently playing song."),
    limit: int = Query(10, ge=1, le=50, description="Number of recommended songs to fetch (default: 10)")
):
    if not video_id:
        raise HTTPException(status_code=400, detail="A videoId is required.")
    try:
        return await asyncio.to_thread(get_upnext_recommendations, video_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not fetch 'Up Next' queue: {e}")


@app.get("/related", response_model=RelatedContent)
async def related(video_id: str = Query(..., description="The videoId to find related content for.")):
    if not video_id:
        raise HTTPException(status_code=400, detail="A videoId is required.")
    try:
        return await asyncio.to_thread(get_related_content, video_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not fetch related content: {e}")

@app.get("/lyrics", response_model=LyricsResult)
async def lyrics(video_id: str = Query(..., description="The videoId to find lyrics for.")):
    if not video_id:
        raise HTTPException(status_code=400, detail="A videoId is required.")
    try:
        return await asyncio.to_thread(get_song_lyrics, video_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not fetch lyrics: {e}")
    


@app.get("/artist/{artist_id}/songs", response_model=List[SongDetails])
async def get_artist_songs(
    artist_id: str = Path(..., description="The channelId of the artist."),
    limit: int = Query(10, description="Number of songs to return.")
):
    """
    NEW: Gets the top songs for a given artist ID.
    """
    if not artist_id:
        raise HTTPException(status_code=400, detail="An artistId is required.")
    try:
        return await asyncio.to_thread(get_songs_by_artist, artist_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not fetch artist songs: {e}")

@app.get("/album/{album_id}/songs", response_model=List[SongDetails])
async def get_album_songs(album_id: str = Path(..., description="The browseId of the album.")):
    """
    NEW: Gets all songs from a given album ID.
    NOTE: This endpoint may be unstable due to library issues.
    """
    if not album_id:
        raise HTTPException(status_code=400, detail="An albumId is required.")
    try:
        return await asyncio.to_thread(get_songs_by_album, album_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not fetch album songs: {e}")
