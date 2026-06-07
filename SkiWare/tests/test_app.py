from datetime import date

from fastapi.testclient import TestClient

from backend.main import app
from backend.models.assesment import AssessmentResponse, Part
from backend.services.calculate_DIN import calculate_din


client = TestClient(app)


def _age_for_birthday(birthday: date) -> int:
    today = date.today()
    return today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))


def _valid_user_payload(*, name: str, email: str, weight_lbs: float = 151.0, height_in: float = 67.7) -> dict[str, object]:
    return {
        "name": name,
        "email": email,
        "preferredSport": "Skier",
        "skillLevel": "advanced",
        "equipment": [{"name": "Rossignol Experience 88", "length": "180", "width": "88"}],
        "preferredTerrain": "powder",
        "skierType": 3,
        "birthday": "1998-02-14",
        "weightLbs": weight_lbs,
        "heightIn": height_in,
        "bootSoleLengthMm": 295,
        "password": "TestPass123!",
    }


def _mock_llm_response(equipmentType: str = "skis", brand: str = "Rossignol") -> AssessmentResponse:
    return AssessmentResponse(
        equipmentType=equipmentType,
        brand=brand,
        safeToSki=True,
        severity=2,
        verdict="DIY",
        shopCostEstimate="$20-$40",
        timeEstimate="30 minutes",
        skillLevel="beginner",
        repairSteps=["Clean the base with base cleaner", "Melt P-tex into the gouge"],
        partsList=[Part(name="P-tex candle", searchQuery="Swix P-tex ski base repair candle")],
        youtubeSuggestions=["how to patch ski base gouge DIY"],
        recommendations=[],
    )


def test_assess_endpoint_returns_full_mvp_response():
    from unittest.mock import AsyncMock, patch

    with patch("backend.services.assessment.retrieve_relevant_chunks", new_callable=AsyncMock) as mock_retrieve, \
         patch("backend.services.assessment.generate_assessment", new_callable=AsyncMock) as mock_generate:

        mock_retrieve.return_value = []
        mock_generate.return_value = _mock_llm_response()

        response = client.post(
            "/api/assess",
            json={
                "equipmentType": "skis",
                "brand": "Rossignol",
                "terrain": "ice-hardpack",
                "style": "both",
                "daysSinceWax": 14,
                "daysSinceEdgeWork": 12,
                "coreShots": 2,
                "issueDescription": "A few scratches underfoot after early-season rocks.",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["equipmentType"] == "skis"
    assert payload["brand"] == "Rossignol"
    assert payload["safeToSki"] is True
    assert 1 <= payload["severity"] <= 5
    assert payload["verdict"] in ("DIY", "SHOP")
    assert len(payload["repairSteps"]) > 0
    assert len(payload["partsList"]) > 0
    assert len(payload["youtubeSuggestions"]) > 0
    # daysSinceWax=14 and coreShots=2 both trigger rule-based recommendations
    assert len(payload["recommendations"]) >= 2
    assert all("title" in r for r in payload["recommendations"])


def test_assess_endpoint_accepts_blank_optional_numeric_fields():
    from unittest.mock import AsyncMock, patch

    with patch("backend.services.assessment.retrieve_relevant_chunks", new_callable=AsyncMock) as mock_retrieve, \
         patch("backend.services.assessment.generate_assessment", new_callable=AsyncMock) as mock_generate:

        mock_retrieve.return_value = []
        mock_generate.return_value = _mock_llm_response(equipmentType="snowboard", brand="Burton")

        response = client.post(
            "/api/assess",
            json={
                "equipmentType": "snowboard",
                "brand": "Burton",
                "length": "",
                "height": "",
                "weight": "",
                "terrain": "powder",
                "style": "off-piste",
                "daysSinceWax": 2,
                "daysSinceEdgeWork": 3,
                "coreShots": 0,
                "issueDescription": "",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["equipmentType"] == "snowboard"
    # daysSinceWax=2 and coreShots=0 produce no rule-based recommendations
    assert payload["recommendations"] == []


def test_assess_endpoint_rejects_invalid_equipment_type():
    response = client.post(
        "/api/assess",
        json={
            "equipmentType": "toboggan",
        },
    )

    assert response.status_code == 422


def test_assess_endpoint_uses_default_equipment_type():
    from unittest.mock import AsyncMock, patch

    with patch("backend.services.assessment.retrieve_relevant_chunks", new_callable=AsyncMock) as mock_retrieve, \
         patch("backend.services.assessment.generate_assessment", new_callable=AsyncMock) as mock_generate:

        mock_retrieve.return_value = []
        mock_generate.return_value = _mock_llm_response(equipmentType="skis", brand="")

        response = client.post("/api/assess", json={})

    assert response.status_code == 200
    assert response.json()["equipmentType"] == "skis"


def test_user_router_supports_crud_flow():
    birthday = date(1998, 2, 14)
    create_response = client.put(
        "/api/users/ava-sender",
        json={
            "name": "Ava Sender",
            "email": "AVA@EXAMPLE.COM",
            "preferredSport": "Skier",
            "skillLevel": "advanced",
            "equipment": [{"name": "Rossignol Experience 88", "length": "180", "width": "88"}],
            "preferredTerrain": "powder",
            "skierType": 3,
            "birthday": birthday.isoformat(),
            "weightLbs": 151.0,
            "heightIn": 67.7,
            "bootSoleLengthMm": 295,
            "password": "TestPass123!",
        },
    )

    assert create_response.status_code == 201

    created_user = create_response.json()
    user_id = "ava-sender"

    assert created_user["email"] == "ava@example.com"
    assert created_user["preferredSport"] == "Skier"
    assert created_user["skillLevel"] == "advanced"
    assert created_user["skierType"] == 3
    assert created_user["birthday"] == birthday.isoformat()
    assert created_user["weightLbs"] == 151.0
    assert created_user["heightIn"] == 67.7
    assert created_user["bootSoleLengthMm"] == 295
    assert created_user["DIN"] == calculate_din(
        weight=151.0 * 0.453592,
        boot_sole_length_mm=295,
        age=_age_for_birthday(birthday),
        skier_type=3,
    )

    list_response = client.get("/api/users")
    assert list_response.status_code == 200
    assert list_response.json()["users"][0]["id"] == user_id

    detail_response = client.get(f"/api/users/{user_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["name"] == "Ava Sender"

    update_response = client.put(
        f"/api/users/{user_id}",
        json={
            "name": "Ava Sender",
            "email": "ava@example.com",
            "preferredSport": "Skier",
            "skillLevel": "advanced",
            "equipment": [
                {"name": "Rossignol Experience 88", "length": "180", "width": "88"},
                {"name": "K2 Mindbender 108Ti", "length": "184", "width": "108"},
            ],
            "preferredTerrain": "backcountry",
            "skierType": 3,
            "birthday": birthday.isoformat(),
            "weightLbs": 158.7,
            "heightIn": 68.5,
            "bootSoleLengthMm": 295,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["preferredSport"] == "Skier"
    assert update_response.json()["equipment"] == [
        {"name": "Rossignol Experience 88", "length": "180", "width": "88", "bindingType": "", "age": "", "images": []},
        {"name": "K2 Mindbender 108Ti", "length": "184", "width": "108", "bindingType": "", "age": "", "images": []},
    ]
    assert update_response.json()["preferredTerrain"] == "backcountry"
    assert update_response.json()["weightLbs"] == 158.7
    assert update_response.json()["heightIn"] == 68.5
    assert update_response.json()["DIN"] == calculate_din(
        weight=158.7 * 0.453592,
        boot_sole_length_mm=295,
        age=_age_for_birthday(birthday),
        skier_type=3,
    )

    updated_detail_response = client.get(f"/api/users/{user_id}")
    assert updated_detail_response.status_code == 200
    assert updated_detail_response.json()["DIN"] == calculate_din(
        weight=158.7 * 0.453592,
        boot_sole_length_mm=295,
        age=_age_for_birthday(birthday),
        skier_type=3,
    )

    delete_response = client.delete(f"/api/users/{user_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/users/{user_id}")
    assert missing_response.status_code == 404
    assert missing_response.json() == {"detail": "User not found"}


def test_user_router_rejects_invalid_email():
    response = client.put(
        "/api/users/taylor-ridge",
        json={
            "name": "Taylor Ridge",
            "email": "not-an-email",
            "skierType": 2,
            "birthday": "1996-08-09",
            "weightKg": 70,
            "heightCm": 175,
            "bootSoleLengthMm": 300,
        },
    )

    assert response.status_code == 422


def test_user_router_rejects_future_birthday():
    response = client.put(
        "/api/users/mika-summit",
        json={
            "name": "Mika Summit",
            "email": "mika@example.com",
            "preferredSport": "Skier",
            "skillLevel": "intermediate",
            "equipment": [{"name": "Rossignol Experience 88", "length": "180", "width": "88"}],
            "preferredTerrain": "hybrid",
            "skierType": 2,
            "birthday": "2999-01-01",
            "weightKg": 70,
            "heightCm": 175,
            "bootSoleLengthMm": 300,
        },
    )

    assert response.status_code == 422


def test_user_router_requires_din_inputs_on_upsert():
    response = client.put(
        "/api/users/casey-hill",
        json={
            "name": "Casey Hill",
            "email": "casey@example.com",
            "preferredSport": "Skier",
            "skillLevel": "intermediate",
            "equipment": [{"name": "Rossignol Experience 88", "length": "180", "width": "88"}],
            "preferredTerrain": "hybrid",
        },
    )

    assert response.status_code == 422


def test_get_missing_user_returns_404():
    response = client.get("/api/users/missing-user")

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


def test_delete_missing_user_returns_404():
    response = client.delete("/api/users/missing-user")

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


def test_user_router_rejects_din_inputs_outside_supported_chart():
    response = client.put(
        "/api/users/out-of-range-user",
        json={
            **_valid_user_payload(name="Out Range", email="range@example.com"),
            "weightLbs": 11.0,
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "weight is outside the supported DIN chart range"


def test_user_router_keeps_current_snowboarder_din_behavior():
    birthday = date(1998, 2, 14)
    response = client.put(
        "/api/users/snowboarder-user",
        json={
            **_valid_user_payload(name="Board Rider", email="board@example.com"),
            "preferredSport": "Snowboarder",
        },
    )

    assert response.status_code == 201
    assert response.json()["preferredSport"] == "Snowboarder"
    assert response.json()["DIN"] == calculate_din(
        weight=151.0 * 0.453592,
        boot_sole_length_mm=295,
        age=_age_for_birthday(birthday),
        skier_type=3,
    )


def test_user_router_normalizes_blank_profile_inputs_before_din_validation():
    response = client.put(
        "/api/users/blank-profile-user",
        json={
            **_valid_user_payload(name="Blank Profile", email="blank@example.com"),
            "skierType": "",
            "birthday": "",
            "weightLbs": "",
            "heightIn": "",
            "bootSoleLengthMm": "",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "DIN requires skierType, birthday, weightLbs, heightIn, and bootSoleLengthMm."
    )


def test_list_users_returns_multiple_users():
    first_response = client.put(
        "/api/users/user-one",
        json=_valid_user_payload(name="User One", email="one@example.com"),
    )
    second_response = client.put(
        "/api/users/user-two",
        json=_valid_user_payload(name="User Two", email="two@example.com", weight_lbs=158.7, height_in=70.9),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = client.get("/api/users")

    assert response.status_code == 200
    payload = response.json()
    returned_ids = {user["id"] for user in payload["users"]}

    assert returned_ids == {"user-one", "user-two"}


def test_assess_response_model_has_required_fields():
    from backend.models.recommendation import Recommendation

    r = AssessmentResponse(
        equipmentType="skis",
        brand="Rossignol",
        safeToSki=True,
        severity=2,
        verdict="DIY",
        shopCostEstimate="$20-$40",
        timeEstimate="30 minutes",
        skillLevel="beginner",
        repairSteps=["Clean the base", "Apply P-tex"],
        partsList=[Part(name="P-tex candle", searchQuery="Swix P-tex ski base repair candle")],
        youtubeSuggestions=["how to patch ski base gouge DIY"],
    )

    assert r.safeToSki is True
    assert r.severity == 2
    assert r.verdict == "DIY"
    assert r.recommendations == []
    assert r.partsList[0].searchQuery == "Swix P-tex ski base repair candle"


def test_retriever_returns_chunks_above_threshold():
    import asyncio
    from unittest.mock import AsyncMock, MagicMock, patch

    from backend.services.retriever import retrieve_relevant_chunks

    mock_db = AsyncMock()
    mock_rows = [
        MagicMock(chunk_text="P-tex candles work for surface scratches", metadata={"upvotes": 45}),
        MagicMock(chunk_text="Clean base before applying any filler", metadata=None),
    ]
    mock_result = MagicMock()
    mock_result.fetchall.return_value = mock_rows
    mock_db.execute.return_value = mock_result

    with patch("backend.services.retriever.TextEmbeddingModel") as mock_model_cls:
        mock_model = MagicMock()
        mock_model_cls.from_pretrained.return_value = mock_model
        mock_model.get_embeddings.return_value = [MagicMock(values=[0.1] * 768)]

        with patch("backend.services.retriever.vertexai.init"):
            chunks = asyncio.run(retrieve_relevant_chunks(mock_db, "base gouge rossignol skis"))

    assert len(chunks) == 2
    assert chunks[0]["chunk_text"] == "P-tex candles work for surface scratches"
    assert chunks[0]["metadata"] == {"upvotes": 45}
    assert chunks[1]["metadata"] is None


def test_retriever_returns_empty_when_no_rows():
    import asyncio
    from unittest.mock import AsyncMock, MagicMock, patch

    from backend.services.retriever import retrieve_relevant_chunks

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_db.execute.return_value = mock_result

    with patch("backend.services.retriever.TextEmbeddingModel") as mock_model_cls:
        mock_model = MagicMock()
        mock_model_cls.from_pretrained.return_value = mock_model
        mock_model.get_embeddings.return_value = [MagicMock(values=[0.1] * 768)]

        with patch("backend.services.retriever.vertexai.init"):
            chunks = asyncio.run(retrieve_relevant_chunks(mock_db, "general ski question"))

    assert chunks == []


def test_generator_returns_assessment_response():
    import asyncio
    import json
    from unittest.mock import AsyncMock, MagicMock, patch

    from backend.models.assesment import AssessmentRequest, AssessmentResponse
    from backend.services.generator import generate_assessment

    fake_llm_output = {
        "safeToSki": True,
        "severity": 2,
        "verdict": "DIY",
        "shopCostEstimate": "$20-$40",
        "timeEstimate": "30 minutes",
        "skillLevel": "beginner",
        "repairSteps": ["Clean the base with base cleaner", "Melt P-tex into the gouge"],
        "partsList": [{"name": "P-tex candle", "searchQuery": "Swix P-tex ski base repair candle"}],
        "youtubeSuggestions": ["how to patch ski base gouge DIY"],
    }

    request = AssessmentRequest(
        equipmentType="skis",
        brand="Rossignol",
        terrain="hardpack",
        issueDescription="small base gouge",
        daysSinceWax=8,
        daysSinceEdgeWork=5,
        coreShots=1,
    )

    mock_response = MagicMock()
    mock_response.text = json.dumps(fake_llm_output)

    with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}), \
         patch("backend.services.generator.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        result = asyncio.run(generate_assessment(request, []))

    assert isinstance(result, AssessmentResponse)
    assert result.safeToSki is True
    assert result.severity == 2
    assert result.verdict == "DIY"
    assert result.recommendations == []
    assert result.partsList[0].name == "P-tex candle"


def test_generator_includes_engagement_metadata_in_prompt():
    import asyncio
    import json
    from unittest.mock import AsyncMock, MagicMock, patch

    from backend.models.assesment import AssessmentRequest
    from backend.services.generator import generate_assessment

    fake_llm_output = {
        "safeToSki": True, "severity": 1, "verdict": "DIY",
        "shopCostEstimate": "$0", "timeEstimate": "10 minutes",
        "skillLevel": "beginner", "repairSteps": ["Wax it"],
        "partsList": [], "youtubeSuggestions": [],
    }

    request = AssessmentRequest(equipmentType="skis", brand="K2", issueDescription="needs wax")
    chunks = [
        {"chunk_text": "Hot wax lasts longer than rub-on", "metadata": {"upvotes": 200, "reply_count": 15, "reply_sentiment": "mostly agreeing"}},
        {"chunk_text": "Use a wax appropriate for snow temperature", "metadata": None},
    ]

    mock_response = MagicMock()
    mock_response.text = json.dumps(fake_llm_output)

    captured_contents = []

    async def fake_generate(**kwargs):
        captured_contents.append(kwargs.get("contents", ""))
        return mock_response

    with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}), \
         patch("backend.services.generator.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.aio.models.generate_content = fake_generate

        asyncio.run(generate_assessment(request, chunks))

    prompt = captured_contents[0]
    assert "200 upvotes" in prompt
    assert "15 replies" in prompt
    assert "mostly agreeing" in prompt
    assert "Authoritative reference" in prompt


def test_assess_saves_to_history_when_user_id_provided():
    from unittest.mock import AsyncMock, patch

    client.put(
        "/api/users/history-user",
        json=_valid_user_payload(name="History User", email="history@example.com"),
    )

    with patch("backend.services.assessment.retrieve_relevant_chunks", new_callable=AsyncMock) as mock_retrieve, \
         patch("backend.services.assessment.generate_assessment", new_callable=AsyncMock) as mock_generate:

        mock_retrieve.return_value = []
        mock_generate.return_value = _mock_llm_response()

        response = client.post(
            "/api/assess?userId=history-user",
            json={"equipmentType": "skis", "brand": "Rossignol", "daysSinceWax": 5, "daysSinceEdgeWork": 3, "coreShots": 0},
        )

    assert response.status_code == 200

    history = client.get("/api/assessments?userId=history-user")
    assert history.status_code == 200
    assessments = history.json()["assessments"]
    assert len(assessments) == 1
    assert assessments[0]["brand"] == "Rossignol"
    assert assessments[0]["safeToSki"] is True

    detail = client.get(f"/api/assessments/{assessments[0]['id']}")
    assert detail.status_code == 200
    assert detail.json()["response"]["verdict"] == "DIY"
    assert detail.json()["request"]["equipmentType"] == "skis"


def test_assess_without_user_id_does_not_save():
    from unittest.mock import AsyncMock, patch

    with patch("backend.services.assessment.retrieve_relevant_chunks", new_callable=AsyncMock) as mock_retrieve, \
         patch("backend.services.assessment.generate_assessment", new_callable=AsyncMock) as mock_generate:

        mock_retrieve.return_value = []
        mock_generate.return_value = _mock_llm_response()

        response = client.post("/api/assess", json={"equipmentType": "skis"})

    assert response.status_code == 200

    history = client.get("/api/assessments?userId=nonexistent")
    assert history.status_code == 200
    assert history.json()["assessments"] == []


def test_assessment_detail_returns_404_for_missing():
    response = client.get("/api/assessments/99999")
    assert response.status_code == 404


def test_assessment_history_returns_multiple_sorted_by_date():
    from unittest.mock import AsyncMock, patch

    client.put(
        "/api/users/multi-history",
        json=_valid_user_payload(name="Multi History", email="multi@example.com"),
    )

    with patch("backend.services.assessment.retrieve_relevant_chunks", new_callable=AsyncMock) as mock_retrieve, \
         patch("backend.services.assessment.generate_assessment", new_callable=AsyncMock) as mock_generate:

        mock_retrieve.return_value = []

        mock_generate.return_value = _mock_llm_response(brand="K2")
        client.post("/api/assess?userId=multi-history", json={"equipmentType": "skis", "brand": "K2"})

        mock_generate.return_value = _mock_llm_response(brand="Burton")
        client.post("/api/assess?userId=multi-history", json={"equipmentType": "snowboard", "brand": "Burton"})

    history = client.get("/api/assessments?userId=multi-history")
    assessments = history.json()["assessments"]
    assert len(assessments) == 2
    assert assessments[0]["brand"] == "Burton"
    assert assessments[1]["brand"] == "K2"


def test_orchestrator_merges_rule_based_recommendations():
    import asyncio
    from unittest.mock import AsyncMock, patch

    from backend.models.assesment import AssessmentRequest, AssessmentResponse, Part
    from backend.services.assessment import build_assessment_response

    mock_llm_response = AssessmentResponse(
        equipmentType="skis",
        brand="Rossignol",
        safeToSki=True,
        severity=2,
        verdict="DIY",
        shopCostEstimate="$20-$40",
        timeEstimate="30 minutes",
        skillLevel="beginner",
        repairSteps=["Clean the base", "Apply P-tex"],
        partsList=[Part(name="P-tex candle", searchQuery="Swix P-tex ski base repair candle")],
        youtubeSuggestions=["how to patch ski base gouge DIY"],
        recommendations=[],
    )

    request = AssessmentRequest(
        equipmentType="skis",
        brand="Rossignol",
        terrain="hardpack",
        issueDescription="base gouge",
        daysSinceWax=14,
        daysSinceEdgeWork=5,
        coreShots=0,
    )

    mock_db = AsyncMock()

    with patch("backend.services.assessment.retrieve_relevant_chunks", new_callable=AsyncMock) as mock_retrieve, \
         patch("backend.services.assessment.generate_assessment", new_callable=AsyncMock) as mock_generate:

        mock_retrieve.return_value = []
        mock_generate.return_value = mock_llm_response

        result = asyncio.run(build_assessment_response(request, mock_db))

    assert result.safeToSki is True
    assert result.severity == 2
    assert any("Wax" in r.title for r in result.recommendations)
