from unittest.mock import MagicMock, patch
from data_agent.sources.base import Document

_CHUNK = {
    "text": "ski repair tip",
    "source_url": "file://x.md",
    "chunk_index": 0,
    "source_type": "static",
    "source_title": "T",
    "metadata": {},
}


def _doc(url: str) -> Document:
    return Document(url=url, title="Test", content="content about skiing", source_type="static")


def _make_source(docs: list[Document]) -> MagicMock:
    source = MagicMock()
    source.fetch.return_value = docs
    return source


def test_all_sources_are_called():
    s1 = _make_source([_doc("file://a.md")])
    s2 = _make_source([_doc("file://b.md")])
    s3 = _make_source([_doc("file://c.md")])

    with patch("data_agent.main.SOURCES", [s1, s2, s3]), \
         patch("data_agent.main.chunk_document", return_value=[_CHUNK]), \
         patch("data_agent.main.embed_batch", return_value=[[0.1]]), \
         patch("data_agent.main.upsert_chunks"), \
         patch("data_agent.main.init_connection"), \
         patch("data_agent.main.get_db", return_value=MagicMock()):
        from data_agent.main import run
        run()

    s1.fetch.assert_called_once()
    s2.fetch.assert_called_once()
    s3.fetch.assert_called_once()


def test_failed_source_does_not_abort_others():
    failing = MagicMock()
    failing.fetch.side_effect = RuntimeError("network error")
    good = _make_source([_doc("file://good.md")])

    with patch("data_agent.main.SOURCES", [failing, good]), \
         patch("data_agent.main.chunk_document", return_value=[_CHUNK]), \
         patch("data_agent.main.embed_batch", return_value=[[0.1]]), \
         patch("data_agent.main.upsert_chunks"), \
         patch("data_agent.main.init_connection"), \
         patch("data_agent.main.get_db", return_value=MagicMock()):
        from data_agent.main import run
        run()  # must not raise

    good.fetch.assert_called_once()


def test_embed_batch_called_once():
    s1 = _make_source([_doc("file://a.md")])
    s2 = _make_source([_doc("file://b.md")])

    with patch("data_agent.main.SOURCES", [s1, s2]), \
         patch("data_agent.main.chunk_document", return_value=[_CHUNK]), \
         patch("data_agent.main.embed_batch", return_value=[[0.1]]) as mock_embed, \
         patch("data_agent.main.upsert_chunks"), \
         patch("data_agent.main.init_connection"), \
         patch("data_agent.main.get_db", return_value=MagicMock()):
        from data_agent.main import run
        run()

    assert mock_embed.call_count == 1


def test_skips_embed_and_store_when_no_chunks():
    s1 = _make_source([_doc("file://a.md")])

    with patch("data_agent.main.SOURCES", [s1]), \
         patch("data_agent.main.chunk_document", return_value=[]), \
         patch("data_agent.main.embed_batch") as mock_embed, \
         patch("data_agent.main.upsert_chunks") as mock_store, \
         patch("data_agent.main.init_connection"), \
         patch("data_agent.main.get_db", return_value=MagicMock()):
        from data_agent.main import run
        run()

    mock_embed.assert_not_called()
    mock_store.assert_not_called()
