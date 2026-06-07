import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from backend.db.connection import init_connection, get_db
from data_agent.pipeline.chunker import chunk_document
from data_agent.pipeline.embedder import embed_batch
from data_agent.pipeline.store import upsert_chunks
from data_agent.sources.reddit import RedditSource
from data_agent.sources.static_docs import StaticDocsSource
from data_agent.sources.web_scraper import WebScraperSource
from data_agent.sources.youtube import YouTubeSource

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

SOURCES = [
    StaticDocsSource(),
    WebScraperSource(),
    YouTubeSource(),
    RedditSource(),
]


def run() -> None:
    init_connection()
    conn = get_db()

    # Fetch all sources in parallel
    all_docs = []
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(source.fetch): source for source in SOURCES}
        for future in as_completed(futures):
            source = futures[future]
            try:
                docs = future.result()
                all_docs.extend(docs)
                logger.info(f"{source.__class__.__name__} fetched {len(docs)} docs")
            except Exception as e:
                logger.error(f"Source {source.__class__.__name__} failed: {e}")

    # Chunk all docs
    all_chunks = []
    for doc in all_docs:
        try:
            chunks = chunk_document(doc)
            if not chunks:
                logger.warning(f"No chunks produced for {doc.url}")
                continue
            all_chunks.extend(chunks)
            logger.info(f"Chunked {doc.url} — {len(chunks)} chunks")
        except Exception as e:
            logger.error(f"Failed chunking {doc.url}: {e}")

    if not all_chunks:
        logger.warning("No chunks produced across all sources — nothing to embed or store")
        conn.close()
        return

    # Single embed call across all chunks
    try:
        embeddings = embed_batch([c["text"] for c in all_chunks])
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        conn.close()
        return

    # Single store call
    try:
        upsert_chunks(conn, all_chunks, embeddings)
        logger.info(f"Run complete. Total chunks processed: {len(all_chunks)}")
    except Exception as e:
        logger.error(f"Store failed: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
    finally:
        conn.close()


if __name__ == "__main__":
    run()
