import os
from unittest.mock import MagicMock, patch
from data_agent.sources.youtube import YouTubeSource, YOUTUBE_API_BASE


def _mock_youtube_resp(title: str, description: str, channel: str) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = {
        "items": [{
            "snippet": {
                "title": title,
                "description": description,
                "channelTitle": channel,
            }
        }]
    }
    resp.raise_for_status = MagicMock()
    return resp


def test_fetch_skips_when_no_api_key():
    with patch.dict(os.environ, {}, clear=True):
        docs = YouTubeSource().fetch()
    assert docs == []


def test_fetch_skips_when_video_ids_empty():
    with patch.dict(os.environ, {"YOUTUBE_API_KEY": "fake-key"}), \
         patch("data_agent.sources.youtube.VIDEO_IDS", []):
        docs = YouTubeSource().fetch()
    assert docs == []


def test_fetch_returns_document_for_valid_video():
    mock_resp = _mock_youtube_resp("How to wax skis", "Step by step wax guide.", "evo")
    with patch.dict(os.environ, {"YOUTUBE_API_KEY": "fake-key"}), \
         patch("data_agent.sources.youtube.VIDEO_IDS", ["abc123"]), \
         patch("data_agent.sources.youtube.requests.get", return_value=mock_resp) as mock_get:
        docs = YouTubeSource().fetch()
    assert len(docs) == 1
    assert docs[0].title == "How to wax skis"
    assert "evo" in docs[0].content
    assert "Step by step wax guide." in docs[0].content
    mock_get.assert_called_once_with(
        YOUTUBE_API_BASE,
        params={"part": "snippet", "id": "abc123", "key": "fake-key"},
        timeout=10,
    )


def test_fetch_skips_video_with_empty_items():
    resp = MagicMock()
    resp.json.return_value = {"items": []}
    resp.raise_for_status = MagicMock()
    with patch.dict(os.environ, {"YOUTUBE_API_KEY": "fake-key"}), \
         patch("data_agent.sources.youtube.VIDEO_IDS", ["missing123"]), \
         patch("data_agent.sources.youtube.requests.get", return_value=resp):
        docs = YouTubeSource().fetch()
    assert docs == []
