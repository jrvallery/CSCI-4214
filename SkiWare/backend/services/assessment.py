from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.assesment import AssessmentRequest, AssessmentResponse
from backend.models.recommendation import Recommendation
from backend.services.generator import generate_assessment
from backend.services.retriever import retrieve_relevant_chunks


async def build_assessment_response(
    request: AssessmentRequest,
    db: AsyncSession,
) -> AssessmentResponse:
    query = f"{request.issueDescription} {request.brand} {request.equipmentType} {request.terrain}"
    chunks = await retrieve_relevant_chunks(db, query)
    response = await generate_assessment(request, chunks)
    response.recommendations = _build_rule_based(request)
    return response


def _build_rule_based(request: AssessmentRequest) -> list[Recommendation]:
    recommendations: list[Recommendation] = []

    if request.age == "5+ years":
        recommendations.append(
            Recommendation(
                title="Inspect Aging Equipment",
                severity="MEDIUM",
                description=(
                    f"Your {request.equipmentType} are over 5 years old. Check for delamination, "
                    "binding wear, and base oxidation. Older gear may need a professional once-over "
                    "to confirm it is still safe to ride."
                ),
            )
        )

    if request.daysSinceWax >= 12:
        recommendations.append(
            Recommendation(
                title="Wax Before Your Next Session",
                severity="MEDIUM",
                description=(
                    f"Your {request.equipmentType} have gone {request.daysSinceWax} riding days "
                    "since the last wax. Expect slower glide and a drier base until you rewax."
                ),
            )
        )
    elif request.daysSinceWax >= 6:
        recommendations.append(
            Recommendation(
                title="Plan a Fresh Wax Soon",
                severity="LOW",
                description=(
                    f"At {request.daysSinceWax} riding days since waxing, performance is still okay "
                    "but you are entering the usual maintenance window."
                ),
            )
        )

    if request.daysSinceEdgeWork >= 10:
        recommendations.append(
            Recommendation(
                title="Tune Edges for Better Hold",
                severity="MEDIUM",
                description=(
                    f"{request.daysSinceEdgeWork} days since edge work is enough for burrs to build up, "
                    "especially if you ride hardpack or mixed conditions."
                ),
            )
        )

    if request.coreShots >= 3:
        recommendations.append(
            Recommendation(
                title="Inspect Base Damage Closely",
                severity="HIGH",
                description=(
                    f"{request.coreShots} visible core shots suggests meaningful base damage. Seal exposed "
                    "core material quickly and consider a full shop repair if any shot reaches the edge."
                ),
            )
        )
    elif request.coreShots > 0:
        recommendations.append(
            Recommendation(
                title="Patch Minor Base Damage",
                severity="MEDIUM",
                description=(
                    f"You reported {request.coreShots} visible base hits. Clean and patch them before "
                    "water or debris spreads the damage."
                ),
            )
        )

    return recommendations
