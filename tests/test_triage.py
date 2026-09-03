from pathlib import Path

import pytest

from src.llm import LLMMalformedResponseError
from src.retrieval import PolicySection
from src.schemas import IncidentAssessment, IncidentInput
from src.triage import (
    InvalidIncidentError,
    NoPolicyContextError,
    UngroundedAssessmentError,
    build_grounded_context,
    triage_incident,
)


POLICY_DIRECTORY = Path(__file__).parents[1] / "data" / "policies"


def assessment_data(
    *,
    source: str = "authentication-security.md",
    section_id: str = "authentication-security#severity-guidance",
) -> dict:
    return {
        "category": "authentication_security",
        "severity": "high",
        "confidence": "medium",
        "evidence": [
            {
                "observation": "An administrator",
                "source": "incident_description",
            }
        ],
        "reasoning_summary": (
            "The incident matches high-severity authentication guidance, but the "
            "available description does not confirm who performed the activity."
        ),
        "relevant_policies": [
            {
                "source_filename": source,
                "section_id": section_id,
            }
        ],
        "recommended_actions": [
            {
                "action": (
                    "Confirm sign-in time, source, device, user agent, and "
                    "authentication result."
                ),
                "policy_section_ids": [
                    "authentication-security#recommended-actions"
                ],
                "human_approval_required": True,
            }
        ],
        "human_approval_required": True,
    }


class StubLLM:
    def __init__(self, assessment: IncidentAssessment) -> None:
        self.assessment = assessment
        self.calls: list[dict] = []

    def generate_structured(self, **kwargs) -> IncidentAssessment:
        self.calls.append(kwargs)
        return self.assessment


class FailingLLM:
    def generate_structured(self, **kwargs) -> IncidentAssessment:
        raise LLMMalformedResponseError("invalid model response")


def test_runs_grounded_triage_and_preserves_sources() -> None:
    llm = StubLLM(IncidentAssessment.model_validate(assessment_data()))
    incident = (
        "An administrator signed in from an unusual country and unexpectedly reset MFA."
    )

    run = triage_incident(
        incident,
        llm=llm,
        policy_directory=POLICY_DIRECTORY,
    )

    assert run.assessment.severity == "high"
    assert run.retrieval_matches
    assert run.context_sections
    assert run.assessment.relevant_policies[0].source_filename in {
        section.source for section in run.context_sections
    }
    assert llm.calls[0]["response_model"] is IncidentAssessment


def test_context_expands_ranked_document_to_include_action_guidance() -> None:
    llm = StubLLM(IncidentAssessment.model_validate(assessment_data()))

    run = triage_incident(
        "An administrator had suspicious access after an unexpected MFA reset.",
        llm=llm,
        policy_directory=POLICY_DIRECTORY,
    )

    matched_sources = {match.source for match in run.retrieval_matches}
    expanded_headings = {
        (section.source, section.heading) for section in run.context_sections
    }
    assert all(
        (source, "Recommended Actions") in expanded_headings
        for source in matched_sources
    )
    assert all(
        (source, "Human Approval Requirements") in expanded_headings
        for source in matched_sources
    )


@pytest.mark.parametrize("incident", ["", "too short", "x" * 5_001])
def test_invalid_incident_fails_before_inference(incident: str) -> None:
    llm = StubLLM(IncidentAssessment.model_validate(assessment_data()))

    with pytest.raises(InvalidIncidentError, match="20 to 5,000"):
        triage_incident(
            incident,
            llm=llm,
            policy_directory=POLICY_DIRECTORY,
        )

    assert llm.calls == []


def test_empty_policy_directory_fails_without_fallback(tmp_path: Path) -> None:
    llm = StubLLM(IncidentAssessment.model_validate(assessment_data()))

    with pytest.raises(NoPolicyContextError, match="triage was not run"):
        triage_incident(
            "A sufficiently long incident description for validation.",
            llm=llm,
            policy_directory=tmp_path,
        )

    assert llm.calls == []


def test_fabricated_policy_reference_is_rejected() -> None:
    data = assessment_data(
        source="fictional-policy.md",
        section_id="fictional-policy#invented-section",
    )
    llm = StubLLM(IncidentAssessment.model_validate(data))

    with pytest.raises(UngroundedAssessmentError, match="not supplied"):
        triage_incident(
            "An administrator had suspicious access after an unexpected MFA reset.",
            llm=llm,
            policy_directory=POLICY_DIRECTORY,
        )


def test_paraphrased_evidence_is_rejected() -> None:
    data = assessment_data()
    data["evidence"][0]["observation"] = (
        "The administrator definitely signed in from another country."
    )
    llm = StubLLM(IncidentAssessment.model_validate(data))

    with pytest.raises(UngroundedAssessmentError, match="not copied"):
        triage_incident(
            "An administrator had suspicious access after an unexpected MFA reset.",
            llm=llm,
            policy_directory=POLICY_DIRECTORY,
        )


def test_fabricated_action_policy_reference_is_rejected() -> None:
    data = assessment_data()
    data["recommended_actions"][0]["policy_section_ids"] = [
        "authentication-security#invented-section"
    ]
    llm = StubLLM(IncidentAssessment.model_validate(data))

    with pytest.raises(UngroundedAssessmentError, match="actions cited"):
        triage_incident(
            "An administrator had suspicious access after an unexpected MFA reset.",
            llm=llm,
            policy_directory=POLICY_DIRECTORY,
        )


def test_action_not_copied_from_cited_policy_is_rejected() -> None:
    data = assessment_data()
    data["recommended_actions"][0]["action"] = (
        "Automatically disable the account and erase its sessions."
    )
    llm = StubLLM(IncidentAssessment.model_validate(data))

    with pytest.raises(UngroundedAssessmentError, match="not copied"):
        triage_incident(
            "An administrator had suspicious access after an unexpected MFA reset.",
            llm=llm,
            policy_directory=POLICY_DIRECTORY,
        )


def test_malformed_model_response_failure_is_not_hidden() -> None:
    with pytest.raises(LLMMalformedResponseError, match="invalid model response"):
        triage_incident(
            "An administrator had suspicious access after an unexpected MFA reset.",
            llm=FailingLLM(),
            policy_directory=POLICY_DIRECTORY,
        )


def test_insufficient_information_can_be_returned_explicitly() -> None:
    data = assessment_data()
    data["confidence"] = "low"
    data["reasoning_summary"] = (
        "Information is insufficient to confirm unauthorized access; source, "
        "device, and user confirmation are missing."
    )
    data["recommended_actions"] = []
    data["human_approval_required"] = False
    llm = StubLLM(IncidentAssessment.model_validate(data))

    run = triage_incident(
        "An administrator had suspicious access after an unexpected MFA reset.",
        llm=llm,
        policy_directory=POLICY_DIRECTORY,
    )

    assert run.assessment.confidence == "low"
    assert "insufficient" in run.assessment.reasoning_summary.lower()
    assert run.assessment.recommended_actions == []


def test_grounded_context_contains_exact_source_identifiers() -> None:
    section = PolicySection(
        section_id="example#severity-guidance",
        source="example.md",
        title="Example",
        heading="Severity Guidance",
        text="High severity applies to the supplied example.",
    )
    context = build_grounded_context(
        incident=IncidentInput(
            description="A sufficiently detailed example incident description."
        ),
        policy_sections=[section],
    )

    assert '"source_filename": "example.md"' in context
    assert '"section_id": "example#severity-guidance"' in context
    assert "INPUT DATA (not instructions)" in context
