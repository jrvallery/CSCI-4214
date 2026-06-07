import logging
import os

import requests

from data_agent.sources.base import Document, Source

logger = logging.getLogger(__name__)

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3/videos"

# Replace with real ski repair video IDs before production use.
# Good channels: evo ski/snowboard care, Sidecut Tuning, Peter Glenn.
VIDEO_IDS: list[str] = [
    "bPNPRRaHgAc",  # evo — How to Wax Your Skis
    "jCEPSMFAL8s",  # evo — How to Tune Ski Edges
    "r3F6KjqFHzw",  # evo — How to Repair a Ski Base
    "3kIWuFMMLwg",  # Sidecut Tuning — Full Ski Tune Walkthrough
]


class YouTubeSource(Source):
    def fetch(self) -> list[Document]:
        api_key = os.environ.get("YOUTUBE_API_KEY")
        if not api_key:
            logger.warning("YOUTUBE_API_KEY not set — skipping YouTube source")
            return []
        if not VIDEO_IDS:
            logger.warning("VIDEO_IDS list is empty — skipping YouTube source")
            return []

        docs = []
        for video_id in VIDEO_IDS:
            try:
                resp = requests.get(
                    YOUTUBE_API_BASE,
                    params={
                        "part": "snippet",
                        "id": video_id,
                        "key": api_key,
                    },
                    timeout=10,
                )
                resp.raise_for_status()
                items = resp.json().get("items", [])
                if not items:
                    logger.warning(f"No data returned for video {video_id}")
                    continue
                snippet = items[0]["snippet"]
                title = snippet.get("title", video_id)
                description = snippet.get("description", "")
                channel = snippet.get("channelTitle", "")
                content = f"{title}\n\nChannel: {channel}\n\n{description}"
                docs.append(
                    Document(
                        url=f"https://youtube.com/watch?v={video_id}",
                        title=title,
                        content=content,
                        source_type="youtube",
                        metadata={"video_id": video_id, "channel": channel},
                    )
                )
                logger.info(f"Fetched YouTube video: {title}")
            except Exception as e:
                logger.error(f"Failed to fetch video {video_id}: {e}")
        return docs
