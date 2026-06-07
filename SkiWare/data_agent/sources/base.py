from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Document:
    url: str
    title: str
    content: str
    source_type: str
    metadata: dict = field(default_factory=dict)


class Source(ABC):
    @abstractmethod
    def fetch(self) -> list[Document]:
        ...
