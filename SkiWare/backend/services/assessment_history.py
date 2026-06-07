from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.assesment import (
    AssessmentHistoryResponse,
    AssessmentRequest,
    AssessmentResponse,
    SavedAssessment,
    SavedAssessmentDetail,
)
from backend.models.tables import AssessmentTable


async def save_assessment(
    db: AsyncSession,
    user_id: str,
    request: AssessmentRequest,
    response: AssessmentResponse,
) -> None:
    row = AssessmentTable(
        user_id=user_id,
        equipment_type=response.equipmentType,
        brand=response.brand,
        safe_to_ski=response.safeToSki,
        severity=response.severity,
        verdict=response.verdict,
        request_data=request.model_dump(),
        response_data=response.model_dump(),
        created_at=datetime.now(UTC),
    )
    db.add(row)
    await db.commit()


async def get_user_assessments(db: AsyncSession, user_id: str) -> AssessmentHistoryResponse:
    result = await db.execute(
        select(AssessmentTable)
        .where(AssessmentTable.user_id == user_id)
        .order_by(AssessmentTable.created_at.desc())
    )
    rows = result.scalars().all()
    return AssessmentHistoryResponse(
        assessments=[_row_to_summary(row) for row in rows]
    )


async def get_assessment_detail(db: AsyncSession, assessment_id: int) -> SavedAssessmentDetail | None:
    row = await db.get(AssessmentTable, assessment_id)
    if row is None:
        return None
    return SavedAssessmentDetail(
        id=row.id,
        equipmentType=row.equipment_type,
        brand=row.brand,
        safeToSki=row.safe_to_ski,
        severity=row.severity,
        verdict=row.verdict,
        createdAt=row.created_at,
        request=AssessmentRequest.model_validate(row.request_data),
        response=AssessmentResponse.model_validate(row.response_data),
    )


def _row_to_summary(row: AssessmentTable) -> SavedAssessment:
    return SavedAssessment(
        id=row.id,
        equipmentType=row.equipment_type,
        brand=row.brand,
        safeToSki=row.safe_to_ski,
        severity=row.severity,
        verdict=row.verdict,
        createdAt=row.created_at,
    )
