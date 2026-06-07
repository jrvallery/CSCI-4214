import inspect
from data_agent.pipeline.chunker import CHUNK_SIZE, CHUNK_OVERLAP, chunk_document, _recursive_split
from data_agent.sources.base import Document


def _doc(content: str) -> Document:
    return Document(url="file://test.md", title="Test Doc", content=content, source_type="static")


def test_chunk_document_returns_metadata_fields():
    doc = _doc("Hello world, this is a ski repair guide.")
    chunks = chunk_document(doc)
    assert len(chunks) >= 1
    c = chunks[0]
    assert c["source_url"] == "file://test.md"
    assert c["source_title"] == "Test Doc"
    assert c["source_type"] == "static"
    assert "chunk_index" in c
    assert "text" in c


def test_chunk_document_splits_long_text():
    content = "Ski wax is important. " * 300  # ~6600 chars
    chunks = chunk_document(_doc(content))
    assert len(chunks) > 1
    for chunk in chunks:
        # overlap can add up to CHUNK_OVERLAP chars on top of CHUNK_SIZE
        assert len(chunk["text"]) <= CHUNK_SIZE + CHUNK_OVERLAP


def test_chunk_document_returns_empty_for_blank_content():
    chunks = chunk_document(_doc("   \n\n   "))
    assert chunks == []


def test_recursive_split_has_no_overlap_parameter():
    sig = inspect.signature(_recursive_split)
    assert "overlap" not in sig.parameters, (
        "_recursive_split should not have an 'overlap' param — it is unused"
    )
