from typing import Literal

from pydantic import BaseModel


class Recommendation(BaseModel):
    title: str
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    description: str
