from copy import deepcopy

import pytest
from pydantic import ValidationError

from src.schemas import IncidentAssessment, ReviewerResult


def valid_assessment_data() -> dict:
    return {
        "category": "data_exfiltration",
        "severity": "high",
        "confidence": 0.82,
        "evidence": [
            {
                "observation": "Approximately 4,000 customer records were downloaded.",
                "source": "incident_description",
            }
        ],
        "reasoning_summary": (
            "The unusual privileged access and large customer-data download match "
            "the high-severity guidance, but external disclosure is not confirmed."
        ),
        "relevant_policies": [
            {
                "source_filename": "data-exfiltration.md",
                "section_id": "data-exfiltration#severity-guidance",
                "relevance": "The policy treats an unexplained export of at least "
                "1,000 customer records as high severity.",
            }
        ],
        "recommended_actions": [
            {
                "action": "Review export and outbound-transfer audit records.",
                "rationale": "This can distinguish download from confirmed transfer.",
                "human_approval_required": True,
            }
        ],
        "human_approval_required": True,
    }


def valid_reviewer_data() -> dict:
    return {
        "approved": True,
        "policy_grounded": True,
        "evidence_grounded": True,
        "human_approval_correct": True,
        "unsupported_claims": [],
        "warnings": [],
    }


def test_valid_incident_assessment_is_accepted() -> None:
    assessment = IncidentAssessment.model_validate(valid_assessment_data())

    assert assessment.severity == "high"
    assert assessment.confidence == 0.82
    assert assessment.relevant_policies[0].source_filename == "data-exfiltration.md"


@pytest.mark.parametrize("severity", ["informational", "severe", "HIGH", 3])
def test_invalid_severity_is_rejected(severity: object) -> None:
    data = valid_assessment_data()
    data["severity"] = severity

    with pytest.raises(ValidationError):
        IncidentAssessment.model_validate(data)


@pytest.mark.parametrize("confidence", [-0.01, 1.01, float("nan"), float("inf"), "0.8"])
def test_invalid_confidence_is_rejected(confidence: object) -> None:
    data = valid_assessment_data()
    data["confidence"] = confidence

    with pytest.raises(ValidationError):
        IncidentAssessment.model_validate(data)


def test_empty_evidence_is_rejected() -> None:
    data = valid_assessment_data()
    data["evidence"] = []

    with pytest.raises(ValidationError):
        IncidentAssessment.model_validate(data)


@pytest.mark.parametrize("summary", ["   ", "x" * 601])
def test_invalid_reasoning_summary_is_rejected(summary: str) -> None:
    data = valid_assessment_data()
    data["reasoning_summary"] = summary

    with pytest.raises(ValidationError):
        IncidentAssessment.model_validate(data)


def test_hidden_chain_of_thought_field_is_rejected() -> None:
    data = valid_assessment_data()
    data["chain_of_thought"] = "Private step-by-step reasoning"

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        IncidentAssessment.model_validate(data)


def test_policy_source_path_is_rejected() -> None:
    data = valid_assessment_data()
    data["relevant_policies"][0]["source_filename"] = "../private/policy.md"

    with pytest.raises(ValidationError):
        IncidentAssessment.model_validate(data)


def test_duplicate_policy_references_are_rejected() -> None:
    data = valid_assessment_data()
    data["relevant_policies"].append(deepcopy(data["relevant_policies"][0]))

    with pytest.raises(ValidationError, match="section IDs must be unique"):
        IncidentAssessment.model_validate(data)


def test_action_without_human_approval_is_rejected() -> None:
    data = valid_assessment_data()
    data["recommended_actions"][0]["human_approval_required"] = False

    with pytest.raises(ValidationError, match="every recommended action"):
        IncidentAssessment.model_validate(data)


def test_inconsistent_top_level_approval_is_rejected() -> None:
    data = valid_assessment_data()
    data["human_approval_required"] = False

    with pytest.raises(ValidationError, match="true exactly when actions"):
        IncidentAssessment.model_validate(data)


def test_assessment_without_actions_must_not_claim_approval_is_required() -> None:
    data = valid_assessment_data()
    data["recommended_actions"] = []

    with pytest.raises(ValidationError, match="true exactly when actions"):
        IncidentAssessment.model_validate(data)


def test_valid_reviewer_result_is_accepted() -> None:
    result = ReviewerResult.model_validate(valid_reviewer_data())

    assert result.approved is True


def test_reviewer_cannot_approve_failed_grounding() -> None:
    data = valid_reviewer_data()
    data["policy_grounded"] = False

    with pytest.raises(ValidationError, match="grounding check failed"):
        ReviewerResult.model_validate(data)


def test_reviewer_cannot_approve_unsupported_claims() -> None:
    data = valid_reviewer_data()
    data["unsupported_claims"] = ["External disclosure was asserted without evidence."]

    with pytest.raises(ValidationError, match="unsupported claims exist"):
        ReviewerResult.model_validate(data)


def test_rejected_review_must_explain_concern() -> None:
    data = valid_reviewer_data()
    data["approved"] = False

    with pytest.raises(ValidationError, match="must identify a concern"):
        ReviewerResult.model_validate(data)


def test_string_boolean_is_rejected() -> None:
    data = valid_reviewer_data()
    data["approved"] = "true"

    with pytest.raises(ValidationError):
        ReviewerResult.model_validate(data)


def test_unknown_reviewer_field_is_rejected() -> None:
    data = valid_reviewer_data()
    data["private_reasoning"] = "Not part of the contract"

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ReviewerResult.model_validate(data)
