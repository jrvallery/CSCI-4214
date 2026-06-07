from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import UserListResponse, UserResponse
from backend.services.users import assign_din, authenticate_user, delete_user, get_user, list_users, upsert_user, validate_user_write

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=UserListResponse, response_model_exclude_none=True)
async def get_users(db: AsyncSession = Depends(get_db)) -> UserListResponse:
    return await list_users(db)


@router.get("/{user_id}", response_model=UserResponse, response_model_exclude_none=True)
async def get_user_record(user_id: str, db: AsyncSession = Depends(get_db)) -> UserResponse:
    user = await get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse, response_model_exclude_none=True)
async def upsert_user_record(
    user_id: str,
    payload: dict[str, Any],
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    validated_payload, validation_errors = validate_user_write(payload)
    if validation_errors is not None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=validation_errors)

    assert validated_payload is not None

    if validated_payload.password is None:
        existing = await get_user(db, user_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Password is required to create an account",
            )

    din, din_error = assign_din(validated_payload)
    if din_error is not None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=din_error)

    assert din is not None
    user, created = await upsert_user(db, user_id, validated_payload, din)
    if created:
        response.status_code = status.HTTP_201_CREATED
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_record(user_id: str, db: AsyncSession = Depends(get_db)) -> Response:
    deleted = await delete_user(db, user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
