import hashlib
import json
import logging

import pg8000

logger = logging.getLogger(__name__)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def upsert_chunks(conn: pg8000.Connection, chunks: list[dict], embeddings: list[list[float]]) -> None:
    if not chunks:
        return

    cursor = conn.cursor()

    # Compute content hashes for all incoming chunks
    hashed = [(_hash(c["text"]), c, e) for c, e in zip(chunks, embeddings)]

    # Bulk fetch existing hashes for all source_urls in this batch
    source_urls = list({c["source_url"] for c in chunks})
    placeholders = ",".join(["%s"] * len(source_urls))
    cursor.execute(
        f"SELECT content_hash FROM ski_knowledge_chunks WHERE source_url IN ({placeholders})",
        source_urls,
    )
    existing_hashes = {row[0] for row in cursor.fetchall()}

    # Filter to new chunks only
    to_insert = [(h, c, e) for h, c, e in hashed if h not in existing_hashes]

    if not to_insert:
        logger.info("All chunks already exist — nothing to upsert")
        conn.commit()
        cursor.close()
        return

    # Delete stale rows (same source_url + chunk_index, different content hash)
    stale_params = [(c["source_url"], c["chunk_index"], h) for h, c, e in to_insert]
    cursor.executemany(
        "DELETE FROM ski_knowledge_chunks WHERE source_url = %s AND chunk_index = %s AND content_hash != %s",
        stale_params,
    )

    # Insert new rows in one batch
    insert_params = [
        (
            h,
            c["source_type"],
            c["source_url"],
            c["source_title"],
            c["chunk_index"],
            c["text"],
            json.dumps(c["metadata"]),
            "[" + ",".join(str(x) for x in e) + "]",
        )
        for h, c, e in to_insert
    ]
    cursor.executemany(
        """
        INSERT INTO ski_knowledge_chunks
            (content_hash, source_type, source_url, source_title,
             chunk_index, chunk_text, metadata, embedding)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector)
        ON CONFLICT (content_hash) DO NOTHING
        """,
        insert_params,
    )

    conn.commit()
    cursor.close()
    logger.info(
        f"Upserted {len(to_insert)} new chunks, skipped {len(hashed) - len(to_insert)} duplicates"
    )
