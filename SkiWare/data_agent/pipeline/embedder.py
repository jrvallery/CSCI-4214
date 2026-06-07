import logging
import os

import vertexai
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel

logger = logging.getLogger(__name__)

BATCH_SIZE = 100
MODEL_NAME = "text-embedding-004"
EMBEDDING_DIM = 768

_model: TextEmbeddingModel | None = None


def _get_model() -> TextEmbeddingModel:
    global _model
    if _model is None:
        vertexai.init(
            project=os.environ["GCP_PROJECT"],
            location=os.environ.get("GCP_REGION", "us-central1"),
        )
        _model = TextEmbeddingModel.from_pretrained(MODEL_NAME)
    return _model


def embed_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    model = _get_model()
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        logger.info(f"Embedding batch {i // BATCH_SIZE + 1} ({len(batch)} texts)")
        inputs = [TextEmbeddingInput(text=t, task_type="RETRIEVAL_DOCUMENT") for t in batch]
        result = model.get_embeddings(inputs)
        all_embeddings.extend([e.values for e in result])

    return all_embeddings
