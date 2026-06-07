import logging
from datetime import datetime, timezone

from data_agent.sources.base import Document

logger = logging.getLogger(__name__)

CHUNK_SIZE = 3200
CHUNK_OVERLAP = 600
SEPARATORS = ["\n\n", "\n", ". ", " "]


def _split(text: str, sep: str, chunk_size: int) -> list[str]:
    parts = text.split(sep)
    chunks: list[str] = []
    current = ""
    for part in parts:
        candidate = current + (sep if current else "") + part
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            if len(part) > chunk_size:
                # part itself is too large — will be handled by next separator level
                current = part
            else:
                current = part
    if current:
        chunks.append(current)
    return chunks


def _recursive_split(text: str, separators: list[str], chunk_size: int) -> list[str]:
    if not separators or len(text) <= chunk_size:
        return [text] if text.strip() else []

    sep = separators[0]
    remaining = separators[1:]

    raw_chunks = _split(text, sep, chunk_size)
    result: list[str] = []
    for chunk in raw_chunks:
        if len(chunk) > chunk_size:
            result.extend(_recursive_split(chunk, remaining, chunk_size))
        else:
            if chunk.strip():
                result.append(chunk)
    return result


def _add_overlap(chunks: list[str], overlap: int, chunk_size: int) -> list[str]:
    if len(chunks) <= 1:
        return chunks
    result = [chunks[0]]
    for i in range(1, len(chunks)):
        tail = result[-1][-overlap:] if len(result[-1]) > overlap else result[-1]
        combined = tail + chunks[i]
        # Trim from the front if overlap pushes us over the size limit
        if len(combined) > chunk_size:
            combined = combined[-chunk_size:]
        result.append(combined)
    return result


def chunk_document(doc: Document) -> list[dict]:
    raw = _recursive_split(doc.content, SEPARATORS, CHUNK_SIZE)
    overlapped = _add_overlap(raw, CHUNK_OVERLAP, CHUNK_SIZE)
    now = datetime.now(timezone.utc).isoformat()
    chunks = []
    for i, text in enumerate(overlapped):
        if not text.strip():
            continue
        chunks.append({
            "text": text.strip(),
            "chunk_index": i,
            "source_url": doc.url,
            "source_title": doc.title,
            "source_type": doc.source_type,
            "metadata": {
                **doc.metadata,
                "chunk_index": i,
                "scraped_at": now,
            },
        })
    logger.info(f"Chunked '{doc.title}' into {len(chunks)} chunks")
    return chunks
