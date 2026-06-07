import logging
from pathlib import Path

from data_agent.sources.base import Document, Source

logger = logging.getLogger(__name__)

KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"


class StaticDocsSource(Source):
    def fetch(self) -> list[Document]:
        docs = []
        for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
            content = path.read_text(encoding="utf-8")
            docs.append(
                Document(
                    url=f"file://{path.name}",
                    title=path.stem.replace("_", " ").title(),
                    content=content,
                    source_type="static",
                    metadata={"filename": path.name},
                )
            )
            logger.info(f"Loaded static doc: {path.name} ({len(content)} chars)")
        return docs
