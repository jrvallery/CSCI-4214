from datetime import UTC, date, datetime
from typing import Any

import bcrypt
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import UserTable
from backend.models.user import UserListResponse, UserResponse, UserWrite
from backend.services.calculate_DIN import calculate_din

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


async def authenticate_user(db: AsyncSession, email: str, password: str) -> UserResponse | None:
    result = await db.execute(select(UserTable).where(UserTable.email == email.lower()))
    row = result.scalar_one_or_none()
    if row is None or row.password_hash is None:
        return None
    if not verify_password(password, row.password_hash):
        return None
    return _row_to_response(row)


async def list_users(db: AsyncSession) -> UserListResponse:
    result = await db.execute(select(UserTable))
    rows = result.scalars().all()
    return UserListResponse(users=[_row_to_response(row) for row in rows])


async def get_user(db: AsyncSession, user_id: str) -> UserResponse | None:
    row = await db.get(UserTable, user_id)
    return _row_to_response(row) if row else None


async def upsert_user(
    db: AsyncSession, user_id: str, payload: UserWrite, din: float
) -> tuple[UserResponse, bool]:
    existing = await db.get(UserTable, user_id)
    timestamp = datetime.now(UTC)
    created_at = existing.created_at if existing else timestamp

    if existing is None:
        row = UserTable(
            id=user_id,
            din=din,
            created_at=created_at,
            updated_at=timestamp,
            **_payload_to_columns(payload),
        )
        if payload.password is not None:
            row.password_hash = hash_password(payload.password)
        db.add(row)
    else:
        for key, value in _payload_to_columns(payload).items():
            setattr(existing, key, value)
        existing.din = din
        existing.updated_at = timestamp
        if payload.password is not None:
            existing.password_hash = hash_password(payload.password)
        row = existing

    await db.commit()
    await db.refresh(row)
    return _row_to_response(row), existing is None


async def delete_user(db: AsyncSession, user_id: str) -> bool:
    row = await db.get(UserTable, user_id)
    if row is None:
        return False
    await db.delete(row)
    await db.commit()
    return True


def validate_user_write(payload: dict[str, Any]) -> tuple[UserWrite | None, list[dict[str, Any]] | None]:
    try:
        return UserWrite.model_validate(payload), None
    except ValidationError as exc:
        return None, _serialize_validation_error(exc)


_LBS_TO_KG = 0.453592


def assign_din(user: UserWrite) -> tuple[float | None, str | None]:
    if (
        user.skierType is None
        or user.birthday is None
        or user.weightLbs is None
        or user.heightIn is None
        or user.bootSoleLengthMm is None
    ):
        return None, (
            "DIN requires skierType, birthday, weightLbs, heightIn, "
            "and bootSoleLengthMm."
        )
    try:
        return (
            calculate_din(
                weight=user.weightLbs * _LBS_TO_KG,
                boot_sole_length_mm=user.bootSoleLengthMm,
                age=_calculate_age(user.birthday),
                skier_type=user.skierType,
            ),
            None,
        )
    except ValueError as exc:
        return None, str(exc)


def _calculate_age(birthday: date) -> int:
    today = date.today()
    return today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))


def _serialize_validation_error(exc: ValidationError) -> list[dict[str, Any]]:
    return [
        {
            "type": error["type"],
            "loc": error["loc"],
            "msg": error["msg"],
            "input": error.get("input"),
        }
        for error in exc.errors()
    ]


def _payload_to_columns(payload: UserWrite) -> dict:
    return {
        "name": payload.name,
        "email": payload.email,
        "preferred_sport": payload.preferredSport,
        "skill_level": payload.skillLevel,
        "equipment": [item.model_dump() for item in payload.equipment],
        "preferred_terrain": payload.preferredTerrain,
        "skier_type": payload.skierType,
        "birthday": payload.birthday,
        "weight_lbs": payload.weightLbs,
        "height_in": payload.heightIn,
        "boot_sole_length_mm": payload.bootSoleLengthMm,
    }


def _row_to_response(row: UserTable) -> UserResponse:
    return UserResponse.model_validate({
        "id": row.id,
        "name": row.name,
        "email": row.email,
        "preferredSport": row.preferred_sport,
        "skillLevel": row.skill_level,
        "equipment": row.equipment or [],
        "preferredTerrain": row.preferred_terrain,
        "skierType": row.skier_type,
        "birthday": row.birthday,
        "weightLbs": row.weight_lbs,
        "heightIn": row.height_in,
        "bootSoleLengthMm": row.boot_sole_length_mm,
        "DIN": row.din,
        "createdAt": row.created_at,
        "updatedAt": row.updated_at,
    })
