from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator


SkillLevel = Literal["beginner", "intermediate", "advanced", "expert"]
TerrainPreference = Literal["groomers", "park", "powder", "backcountry", "hybrid"]
SnowSport = Literal["Skier", "Snowboarder"]


class EquipmentItem(BaseModel):
    name: str = ""       # brand + model, e.g. "Rossignol Experience 88"
    length: str = ""     # e.g. "180" (cm) or "180cm"
    width: str = ""      # e.g. "88" (mm waist) or "88mm"
    bindingType: str = ""  # e.g. "Alpine", "Tech/Pin", "Frame", "Strap"
    age: str = ""        # e.g. "0-1 year", "1-2 years", "2-5 years", "5+ years"
    images: list[str] = []  # list of image URLs; index 0 is the default/cover image


class UserWrite(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=5, max_length=254)
    preferredSport: SnowSport = "Skier"
    skillLevel: SkillLevel = "intermediate"
    equipment: list[EquipmentItem] = Field(default_factory=list)
    preferredTerrain: TerrainPreference = "hybrid"
    skierType: int | None = Field(default=None, ge=1, le=3)
    birthday: date | None = None
    weightLbs: float | None = Field(default=None, gt=0, le=661)
    heightIn: float | None = Field(default=None, gt=0, le=118)
    bootSoleLengthMm: int | None = Field(default=None, ge=200, le=400)
    password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("name", "email")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value must not be blank")
        return cleaned

    @field_validator("email")
    @classmethod
    def validate_email_shape(cls, value: str) -> str:
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("value must be a valid email address")
        return value.lower()

    @field_validator("skierType", "birthday", "weightLbs", "heightIn", "bootSoleLengthMm", mode="before")
    @classmethod
    def empty_profile_value_to_none(cls, value: object) -> object:
        if value == "":
            return None
        return value

    @field_validator("birthday")
    @classmethod
    def validate_birthday(cls, value: date | None) -> date | None:
        if value is None:
            return value
        if value >= date.today():
            raise ValueError("birthday must be in the past")
        return value


class UserResponse(UserWrite):
    id: str
    DIN: float
    createdAt: datetime
    updatedAt: datetime
    password: str | None = Field(default=None, exclude=True)  # never serialized


class UserListResponse(BaseModel):
    users: list[UserResponse]
