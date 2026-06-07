import asyncio
import os

import vertexai
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel

SIMILARITY_THRESHOLD = 0.75
TOP_K = 5
_EMBEDDING_MODEL = "text-embedding-004"


async def retrieve_relevant_chunks(db: AsyncSession, query: str) -> list[dict]:
    """
    Embeds query via Vertex AI text-embedding-004, queries pgvector with cosine
    similarity, returns chunks where similarity >= SIMILARITY_THRESHOLD.
    Returns [] if nothing clears the threshold or if embedding/DB fails.

    Each returned dict: {"chunk_text": str, "metadata": dict | None}
    """
    try:
        embedding = await asyncio.to_thread(_embed_query, query)
    except Exception:
        return []
    embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"

    sql = text("""
        SELECT chunk_text, metadata,
               1 - (embedding <=> CAST(:query_vec AS vector)) AS similarity
        FROM ski_knowledge_chunks
        WHERE 1 - (embedding <=> CAST(:query_vec AS vector)) >= :threshold
        ORDER BY similarity DESC
        LIMIT :top_k
    """)

    try:
        result = await db.execute(sql, {
            "query_vec": embedding_str,
            "threshold": SIMILARITY_THRESHOLD,
            "top_k": TOP_K,
        })
        rows = result.fetchall()
    except Exception:
        await db.rollback()
        return []

    return [{"chunk_text": row.chunk_text, "metadata": row.metadata} for row in rows]


def _embed_query(query: str) -> list[float]:
    try:
        vertexai.init(
            project=os.environ.get("GCP_PROJECT", ""),
            location=os.environ.get("GCP_REGION", "us-central1"),
        )
        model = TextEmbeddingModel.from_pretrained(_EMBEDDING_MODEL)
        inputs = [TextEmbeddingInput(text=query, task_type="RETRIEVAL_QUERY")]
        result = model.get_embeddings(inputs)
        return result[0].values
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Embedding service unavailable: {exc}") from exc
