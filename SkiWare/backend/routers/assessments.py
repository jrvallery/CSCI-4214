from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.assesment import (
    AssessmentHistoryResponse,
    AssessmentRequest,
    AssessmentResponse,
    SavedAssessmentDetail,
)
from backend.services.assessment import build_assessment_response
from backend.services.assessment_history import (
    get_assessment_detail,
    get_user_assessments,
    save_assessment,
)

router = APIRouter(prefix="/api", tags=["assessments"])


@router.post("/assess", response_model=AssessmentResponse)
async def assess(
    payload: AssessmentRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str | None = Query(default=None, alias="userId"),
) -> AssessmentResponse:
    response = await build_assessment_response(payload, db)
    if user_id:
        await save_assessment(db, user_id, payload, response)
    return response


@router.get("/assessments", response_model=AssessmentHistoryResponse)
async def list_assessments(
    user_id: str = Query(alias="userId"),
    db: AsyncSession = Depends(get_db),
) -> AssessmentHistoryResponse:
    return await get_user_assessments(db, user_id)


@router.get("/assessments/{assessment_id}", response_model=SavedAssessmentDetail)
async def get_assessment(
    assessment_id: int,
    db: AsyncSession = Depends(get_db),
) -> SavedAssessmentDetail:
    detail = await get_assessment_detail(db, assessment_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    return detail
