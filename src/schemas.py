"""Structured contracts for model output and deterministic validation.

The models intentionally contain only user-facing conclusions and citations.
They do not request or store hidden chain-of-thought reasoning.
"""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StringConstraints,
    field_validator,
    model_validator,
)


IncidentCategory = Literal[
    "authentication_security",
    "account_compromise",
    "data_exfiltration",
    "malware",
    "service_outage",
    "other",
]
Severity = Literal["low", "medium", "high", "critical"]

Statement = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=500),
]
ShortSummary = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=600),
]
IncidentDescription = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=20, max_length=5_000),
]
PolicyFilename = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*\.md$",
        max_length=120,
    ),
]
SectionId = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        pattern=r"^[a-z0-9][a-z0-9-]*#[a-z0-9][a-z0-9-]*(?:-[0-9]+)?$",
        max_length=160,
    ),
]
Confidence = Literal["low", "medium", "high"]


class _ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class IncidentInput(_ContractModel):
    """Validated incident text accepted by the triage pipeline."""

    description: IncidentDescription


class EvidenceItem(_ContractModel):
    """A factual observation traceable to the submitted incident text."""

    observation: Statement
    source: Literal["incident_description"]


class PolicyReference(_ContractModel):
    """A citation to one policy section supplied by retrieval."""

    source_filename: PolicyFilename
    section_id: SectionId


class RecommendedAction(_ContractModel):
    """A recommendation for a human to consider, never an executable action."""

    action: Statement
    policy_section_ids: list[SectionId] = Field(min_length=1, max_length=5)
    human_approval_required: Literal[True]


class IncidentAssessment(_ContractModel):
    """Validated, user-facing triage output proposed by the model."""

    category: IncidentCategory
    severity: Severity
    confidence: Confidence
    evidence: list[EvidenceItem] = Field(min_length=1, max_length=20)
    reasoning_summary: ShortSummary = Field(
        description=(
            "Short user-facing explanation of the conclusion; never hidden "
            "chain-of-thought reasoning."
        )
    )
    relevant_policies: list[PolicyReference] = Field(min_length=1, max_length=10)
    recommended_actions: list[RecommendedAction] = Field(max_length=10)
    human_approval_required: StrictBool

    @field_validator("reasoning_summary")
    @classmethod
    def validate_complete_summary(cls, summary: str) -> str:
        if summary[-1] not in ".!?":
            raise ValueError("reasoning_summary must end with terminal punctuation")
        return summary

    @model_validator(mode="after")
    def validate_grounding_and_approval(self) -> Self:
        section_ids = [reference.section_id for reference in self.relevant_policies]
        if len(section_ids) != len(set(section_ids)):
            raise ValueError("relevant policy section IDs must be unique")

        if any(not action.human_approval_required for action in self.recommended_actions):
            raise ValueError("every recommended action requires human approval")

        for action in self.recommended_actions:
            if len(action.policy_section_ids) != len(set(action.policy_section_ids)):
                raise ValueError("action policy section IDs must be unique")

        expected_approval = bool(self.recommended_actions)
        if self.human_approval_required is not expected_approval:
            raise ValueError(
                "human_approval_required must be true exactly when actions are "
                "recommended"
            )
        return self


class ReviewerResult(_ContractModel):
    """Structured advisory review of a validated incident assessment."""

    approved: StrictBool
    policy_grounded: StrictBool
    evidence_grounded: StrictBool
    human_approval_correct: StrictBool
    unsupported_claims: list[Statement] = Field(max_length=20)
    warnings: list[Statement] = Field(max_length=20)

    @model_validator(mode="after")
    def validate_approval(self) -> Self:
        checks_pass = (
            self.policy_grounded
            and self.evidence_grounded
            and self.human_approval_correct
        )
        if self.approved and not checks_pass:
            raise ValueError("approved cannot be true when a grounding check failed")
        if self.approved and self.unsupported_claims:
            raise ValueError("approved cannot be true when unsupported claims exist")
        if not self.approved and checks_pass and not (
            self.unsupported_claims or self.warnings
        ):
            raise ValueError("a rejected review must identify a concern")
        return self
