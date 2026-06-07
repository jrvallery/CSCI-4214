from unittest.mock import MagicMock
from data_agent.pipeline.store import upsert_chunks, _hash


def _chunk(text: str = "hello", url: str = "file://a.md", idx: int = 0) -> dict:
    return {
        "text": text,
        "source_url": url,
        "chunk_index": idx,
        "source_type": "static",
        "source_title": "Test",
        "metadata": {},
    }


def _mock_conn(existing_hashes: list[str] | None = None) -> tuple:
    cursor = MagicMock()
    cursor.fetchall.return_value = [(h,) for h in (existing_hashes or [])]
    conn = MagicMock()
    conn.cursor.return_value = cursor
    return conn, cursor


def test_noop_on_empty_chunks():
    conn, cursor = _mock_conn()
    upsert_chunks(conn, [], [])
    cursor.execute.assert_not_called()
    conn.commit.assert_not_called()


def test_skips_chunk_whose_hash_already_exists():
    text = "already stored content"
    h = _hash(text)
    conn, cursor = _mock_conn(existing_hashes=[h])

    upsert_chunks(conn, [_chunk(text)], [[0.1, 0.2]])

    for c in cursor.executemany.call_args_list:
        assert "INSERT" not in str(c), "INSERT called for a duplicate chunk"
    conn.commit.assert_called_once()


def test_inserts_new_chunk():
    conn, cursor = _mock_conn(existing_hashes=[])
    upsert_chunks(conn, [_chunk("brand new content")], [[0.1, 0.2]])

    # Two executemany calls: DELETE stale rows, then INSERT new rows
    assert cursor.executemany.call_count == 2
    conn.commit.assert_called_once()


def test_single_commit_for_multiple_chunks():
    conn, cursor = _mock_conn(existing_hashes=[])
    chunks = [_chunk(f"chunk {i}", idx=i) for i in range(5)]
    embeddings = [[float(i)] * 3 for i in range(5)]

    upsert_chunks(conn, chunks, embeddings)

    conn.commit.assert_called_once()
