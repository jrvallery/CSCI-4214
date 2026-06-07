import logging
import os
from unittest.mock import MagicMock, patch

import pytest

from data_agent.sources.reddit import (
    MIN_COMMENT_LENGTH,
    MIN_COMMENT_SCORE,
    MIN_POST_SCORE,
    MIN_TEXT_LENGTH,
    RedditSource,
    _comment_limit,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_post(
    id: str = "abc",
    title: str = "How to fix base scratch",
    selftext: str = "x" * 200,
    score: int = 50,
    url: str = None,
    subreddit: str = "skiing",
    num_comments: int = 0,
) -> MagicMock:
    post = MagicMock()
    post.id = id
    post.title = title
    post.selftext = selftext
    post.score = score
    post.url = url if url is not None else f"https://reddit.com/r/skiing/comments/{id}/"
    post.subreddit.display_name = subreddit
    post.num_comments = num_comments
    post.comments.replace_more.return_value = None
    post.comments.list.return_value = []
    return post


def _make_comment(
    id: str = "c1",
    body: str = "y" * 100,
    score: int = 10,
    parent_id: str = "t3_abc",
) -> MagicMock:
    comment = MagicMock()
    comment.id = id
    comment.body = body
    comment.score = score
    comment.parent_id = parent_id
    return comment


def _patch_reddit(posts_by_subreddit=None):
    """Return a context manager that patches praw.Reddit with the given posts."""
    posts_by_subreddit = posts_by_subreddit or {}

    def make_reddit(*args, **kwargs):
        reddit = MagicMock()

        def make_subreddit(name):
            sub = MagicMock()
            sub.search.side_effect = lambda *a, **kw: iter(
                posts_by_subreddit.get(name, [])
            )
            return sub

        reddit.subreddit.side_effect = make_subreddit
        return reddit

    return patch("data_agent.sources.reddit.praw.Reddit", side_effect=make_reddit)


_CREDS = {"REDDIT_CLIENT_ID": "id", "REDDIT_CLIENT_SECRET": "secret"}


# ---------------------------------------------------------------------------
# _comment_limit
# ---------------------------------------------------------------------------

def test_comment_limit_low_score():
    assert _comment_limit(5) == 5


def test_comment_limit_mid_score():
    assert _comment_limit(100) == 10


def test_comment_limit_high_score():
    assert _comment_limit(500) == 15


def test_comment_limit_boundary_100():
    assert _comment_limit(99) == 5
    assert _comment_limit(100) == 10


def test_comment_limit_boundary_500():
    assert _comment_limit(499) == 10
    assert _comment_limit(500) == 15


# ---------------------------------------------------------------------------
# Credential check
# ---------------------------------------------------------------------------

def test_missing_client_id_returns_empty_and_logs(caplog):
    env = {"REDDIT_CLIENT_SECRET": "secret"}
    with patch.dict(os.environ, env, clear=True), \
         caplog.at_level(logging.WARNING, logger="data_agent.sources.reddit"):
        docs = RedditSource().fetch()
    assert docs == []
    assert any("REDDIT_CLIENT_ID" in r.message for r in caplog.records)


def test_missing_client_secret_returns_empty_and_logs(caplog):
    env = {"REDDIT_CLIENT_ID": "id"}
    with patch.dict(os.environ, env, clear=True), \
         caplog.at_level(logging.WARNING, logger="data_agent.sources.reddit"):
        docs = RedditSource().fetch()
    assert docs == []
    assert any("REDDIT_CLIENT_SECRET" in r.message for r in caplog.records)


def test_missing_both_credentials_returns_empty(caplog):
    with patch.dict(os.environ, {}, clear=True), \
         caplog.at_level(logging.WARNING, logger="data_agent.sources.reddit"):
        docs = RedditSource().fetch()
    assert docs == []


# ---------------------------------------------------------------------------
# Post filtering
# ---------------------------------------------------------------------------

def test_post_below_min_score_excluded():
    low_score_post = _make_post(score=MIN_POST_SCORE - 1)
    with patch.dict(os.environ, _CREDS), \
         _patch_reddit({"skiing": [low_score_post]}):
        docs = RedditSource().fetch()
    assert docs == []


def test_post_at_min_score_included():
    post = _make_post(score=MIN_POST_SCORE, selftext="z" * MIN_TEXT_LENGTH)
    with patch.dict(os.environ, _CREDS), \
         _patch_reddit({"skiing": [post]}):
        docs = RedditSource().fetch()
    assert len(docs) >= 1


def test_post_below_min_text_length_excluded():
    short_post = _make_post(score=50, selftext="short")
    with patch.dict(os.environ, _CREDS), \
         _patch_reddit({"skiing": [short_post]}):
        docs = RedditSource().fetch()
    assert docs == []


def test_post_at_min_text_length_included():
    post = _make_post(score=50, selftext="x" * MIN_TEXT_LENGTH)
    with patch.dict(os.environ, _CREDS), \
         _patch_reddit({"skiing": [post]}):
        docs = RedditSource().fetch()
    assert len(docs) >= 1


# ---------------------------------------------------------------------------
# Post document shape
# ---------------------------------------------------------------------------

def test_post_document_fields():
    post = _make_post(
        id="xyz",
        title="Deep scratch repair",
        selftext="x" * 200,
        score=80,
        url="https://reddit.com/r/skiing/comments/xyz/",
        subreddit="skiing",
    )
    with patch.dict(os.environ, _CREDS), \
         _patch_reddit({"skiing": [post]}):
        docs = RedditSource().fetch()

    post_docs = [d for d in docs if "comment_id" not in d.metadata and "xyz" in d.url]
    assert len(post_docs) == 1
    doc = post_docs[0]
    assert doc.source_type == "reddit"
    assert "Deep scratch repair" in doc.title
    assert "x" * 200 in doc.content
    assert doc.metadata["upvotes"] == 80
    assert doc.metadata["subreddit"] == "skiing"


# ---------------------------------------------------------------------------
# Comment ingestion
# ---------------------------------------------------------------------------

def test_qualifying_comment_produces_document():
    comment = _make_comment(body="y" * MIN_COMMENT_LENGTH, score=MIN_COMMENT_SCORE)
    post = _make_post(id="p1", score=50, selftext="x" * 200)
    post.comments.list.return_value = [comment]

    with patch.dict(os.environ, _CREDS), \
         _patch_reddit({"skiing": [post]}):
        docs = RedditSource().fetch()

    comment_docs = [d for d in docs if "comment_id" in d.metadata]
    assert len(comment_docs) >= 1


def test_comment_below_score_excluded():
    comment = _make_comment(body="y" * MIN_COMMENT_LENGTH, score=MIN_COMMENT_SCORE - 1)
    post = _make_post(id="p1", score=50, selftext="x" * 200)
    post.comments.list.return_value = [comment]

    with patch.dict(os.environ, _CREDS), \
         _patch_reddit({"skiing": [post]}):
        docs = RedditSource().fetch()

    comment_docs = [d for d in docs if "comment_id" in d.metadata]
    assert len(comment_docs) == 0


def test_comment_below_length_excluded():
    comment = _make_comment(body="short", score=10)
    post = _make_post(id="p1", score=50, selftext="x" * 200)
    post.comments.list.return_value = [comment]

    with patch.dict(os.environ, _CREDS), \
         _patch_reddit({"skiing": [post]}):
        docs = RedditSource().fetch()

    comment_docs = [d for d in docs if "comment_id" in d.metadata]
    assert len(comment_docs) == 0


def test_comment_document_fields():
    body = "You should use p-tex candle to fill base gouges properly."
    comment = _make_comment(id="c99", body=body, score=25, parent_id="t3_p1")
    post = _make_post(id="p1", score=50, selftext="x" * 200, url="https://reddit.com/r/skiing/comments/p1/")
    post.comments.list.return_value = [comment]

    with patch.dict(os.environ, _CREDS), \
         _patch_reddit({"skiing": [post]}):
        docs = RedditSource().fetch()

    comment_docs = [d for d in docs if d.metadata.get("comment_id") == "c99"]
    assert len(comment_docs) == 1
    doc = comment_docs[0]
    assert doc.source_type == "reddit"
    assert body in doc.content
    assert doc.metadata["upvotes"] == 25
    assert doc.metadata["reply_count"] == 0


# ---------------------------------------------------------------------------
# Comment limit enforcement
# ---------------------------------------------------------------------------

def test_comment_limit_applied_to_high_score_post():
    # Post score 500 → limit 15; give 20 qualifying comments, expect max 15
    comments = [
        _make_comment(id=f"c{i}", body="y" * MIN_COMMENT_LENGTH, score=MIN_COMMENT_SCORE)
        for i in range(20)
    ]
    post = _make_post(id="p1", score=500, selftext="x" * 200)
    post.comments.list.return_value = comments

    with patch.dict(os.environ, _CREDS), \
         _patch_reddit({"skiing": [post]}):
        docs = RedditSource().fetch()

    comment_docs = [d for d in docs if "comment_id" in d.metadata]
    assert len(comment_docs) <= 15


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def test_duplicate_posts_deduplicated():
    # Same post returned by two different queries
    post = _make_post(id="dup1", score=50, selftext="x" * 200)
    # skiing subreddit returns the same post twice (simulating two query hits)
    with patch.dict(os.environ, _CREDS), \
         _patch_reddit({"skiing": [post, post]}):
        docs = RedditSource().fetch()

    post_docs = [d for d in docs if "dup1" in d.url and "comment_id" not in d.metadata]
    assert len(post_docs) == 1


def test_duplicate_comments_deduplicated():
    comment = _make_comment(id="dc1", body="y" * MIN_COMMENT_LENGTH, score=10)
    post = _make_post(id="p1", score=50, selftext="x" * 200)
    post.comments.list.return_value = [comment, comment]

    with patch.dict(os.environ, _CREDS), \
         _patch_reddit({"skiing": [post]}):
        docs = RedditSource().fetch()

    comment_docs = [d for d in docs if d.metadata.get("comment_id") == "dc1"]
    assert len(comment_docs) == 1


# ---------------------------------------------------------------------------
# Source type and metadata
# ---------------------------------------------------------------------------

def test_documents_have_reddit_source_type():
    post = _make_post(score=50, selftext="x" * 200)
    with patch.dict(os.environ, _CREDS), \
         _patch_reddit({"skiing": [post]}):
        docs = RedditSource().fetch()
    assert all(d.source_type == "reddit" for d in docs)


def test_post_metadata_contains_reply_count():
    post = _make_post(score=50, selftext="x" * 200, num_comments=7)
    with patch.dict(os.environ, _CREDS), \
         _patch_reddit({"skiing": [post]}):
        docs = RedditSource().fetch()
    post_docs = [d for d in docs if "comment_id" not in d.metadata]
    assert len(post_docs) >= 1
    assert post_docs[0].metadata["reply_count"] == 7
