import json
import os

import google.genai as genai
from google.genai import types as genai_types

from backend.models.assesment import AssessmentRequest, AssessmentResponse, Part

_SYSTEM_INSTRUCTION = """You are a ski and snowboard repair expert.
Given equipment details, an issue description, and any retrieved repair knowledge, produce a structured repair assessment.

Rules:
- safeToSki: true only if there is no structural or safety risk
- severity: 1 (cosmetic only) to 5 (dangerous/unrideable)
- verdict: DIY if home repair is feasible for the stated skill level, SHOP if professional help is needed
- repairSteps: concrete numbered steps — not vague advice
- partsList: real products with specific, searchable product names
- youtubeSuggestions: search query strings only — never fabricate URLs or video IDs
- If no context chunks are provided, reason from general ski repair knowledge
- Community sources with high upvotes and agreeing replies carry more weight than low-engagement sources
"""

_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "safeToSki": {"type": "boolean"},
        "severity": {"type": "integer", "minimum": 1, "maximum": 5},
        "verdict": {"type": "string", "enum": ["DIY", "SHOP"]},
        "shopCostEstimate": {"type": "string"},
        "timeEstimate": {"type": "string"},
        "skillLevel": {"type": "string", "enum": ["beginner", "intermediate", "advanced"]},
        "repairSteps": {"type": "array", "items": {"type": "string"}},
        "partsList": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "searchQuery": {"type": "string"},
                },
                "required": ["name", "searchQuery"],
            },
        },
        "youtubeSuggestions": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "safeToSki", "severity", "verdict", "shopCostEstimate",
        "timeEstimate", "skillLevel", "repairSteps", "partsList", "youtubeSuggestions",
    ],
}


async def generate_assessment(
    request: AssessmentRequest,
    context_chunks: list[dict],
) -> AssessmentResponse:
    """
    Calls Vertex AI Gemini with request fields + retrieved context chunks.
    Returns a populated AssessmentResponse. recommendations field is empty —
    the orchestrator sets it after this call.
    """
    gcp_project = os.environ.get("GCP_PROJECT")
    if gcp_project:
        client = genai.Client(
            vertexai=True,
            project=gcp_project,
            location=os.environ.get("GCP_REGION", "us-central1"),
        )
    else:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    contents = f"""Equipment: {request.equipmentType} — {request.brand}
Equipment age: {request.age}
Terrain: {request.terrain}
Days since wax: {request.daysSinceWax}
Days since edge work: {request.daysSinceEdgeWork}
Core shots: {request.coreShots}
Issue: {request.issueDescription or "No specific issue described"}

Repair knowledge:
{_build_context_section(context_chunks)}"""

    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-pro",
            contents=contents,
            config=genai_types.GenerateContentConfig(
                system_instruction=_SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=_RESPONSE_SCHEMA,
            ),
        )
    except Exception as exc:
        import logging
        from fastapi import HTTPException
        logging.error("Gemini generate_content failed: %s", exc)
        raise HTTPException(status_code=503, detail=f"Gemini service unavailable: {exc}") from exc

    data = json.loads(response.text)

    return AssessmentResponse(
        equipmentType=request.equipmentType,
        brand=request.brand,
        safeToSki=data["safeToSki"],
        severity=data["severity"],
        verdict=data["verdict"],
        shopCostEstimate=data["shopCostEstimate"],
        timeEstimate=data["timeEstimate"],
        skillLevel=data["skillLevel"],
        repairSteps=data["repairSteps"],
        partsList=[Part(**p) for p in data["partsList"]],
        youtubeSuggestions=data["youtubeSuggestions"],
        recommendations=[],
    )


def _build_context_section(chunks: list[dict]) -> str:
    if not chunks:
        return "No specific knowledge chunks retrieved — use general ski repair expertise."

    lines = []
    for chunk in chunks:
        meta = chunk.get("metadata")
        if meta and meta.get("upvotes"):
            label = f"Community tip ({meta['upvotes']} upvotes"
            if meta.get("reply_count"):
                label += f", {meta['reply_count']} replies"
                if meta.get("reply_sentiment"):
                    label += f" — {meta['reply_sentiment']}"
            label += ")"
        else:
            label = "Authoritative reference"
        lines.append(f'Source: {label}:\n"{chunk["chunk_text"]}"')

    return "\n\n".join(lines)
