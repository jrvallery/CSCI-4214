from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from backend.models.recommendation import Recommendation


class Part(BaseModel):
    name: str
    searchQuery: str  # generic product string — frontend builds links for Amazon, REI, evo, Backcountry, Peter Glenn


class AssessmentRequest(BaseModel):
    equipmentType: Literal["skis", "snowboard"] = "skis"
    brand: str = ""
    length: int | None = None
    age: str = "1-2 years"
    terrain: str = "hybrid"
    style: str = "both"
    daysSinceWax: int = Field(default=5, ge=0, le=30)
    daysSinceEdgeWork: int = Field(default=10, ge=0, le=30)
    coreShots: int = Field(default=0, ge=0, le=10)
    height: int | None = None
    weight: int | None = None
    issueDescription: str = ""

    @field_validator("length", "height", "weight", mode="before")
    @classmethod
    def empty_string_to_none(cls, value: object) -> object:
        if value == "":
            return None
        return value


class AssessmentResponse(BaseModel):
    equipmentType: str
    brand: str
    safeToSki: bool
    severity: int = Field(ge=1, le=5)
    verdict: Literal["DIY", "SHOP"]
    shopCostEstimate: str
    timeEstimate: str
    skillLevel: Literal["beginner", "intermediate", "advanced"]
    repairSteps: list[str]
    partsList: list[Part]
    youtubeSuggestions: list[str]
    recommendations: list[Recommendation] = []  # set by orchestrator, not Gemini


class SavedAssessment(BaseModel):
    id: int
    equipmentType: str
    brand: str
    safeToSki: bool
    severity: int
    verdict: str
    createdAt: datetime


class SavedAssessmentDetail(SavedAssessment):
    request: AssessmentRequest
    response: AssessmentResponse


class AssessmentHistoryResponse(BaseModel):
    assessments: list[SavedAssessment]
