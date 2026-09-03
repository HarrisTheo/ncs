"""Minimal Streamlit UI for the local incident triage copilot."""

from __future__ import annotations

import streamlit as st

from src.llm import (
    LLMConfigurationError,
    LLMError,
    LLMMalformedResponseError,
    LLMTimeoutError,
    LLMUnavailableError,
)
from src.reviewer import ReviewedTriageRun, triage_and_review
from src.triage import (
    InvalidIncidentError,
    NoPolicyContextError,
    TriageError,
    UngroundedAssessmentError,
)


NOTICE = (
    "Demonstration system using fictional policies. AI recommendations require "
    "human judgement."
)


def main() -> None:
    st.set_page_config(
        page_title="AI Incident Triage Copilot",
        page_icon="🔎",
        layout="centered",
    )
    st.title("AI Incident Triage & Investigation Copilot")
    st.write(
        "Describe a security or operational incident. The application retrieves "
        "local guidance, proposes a structured triage assessment, and asks a "
        "separate AI reviewer to challenge it."
    )
    st.info(NOTICE)

    with st.form("incident-form"):
        incident = st.text_area(
            "Incident description",
            height=180,
            placeholder=(
                "Example: An administrator account logged in from an unusual "
                "location, MFA was reset, and approximately 4,000 customer "
                "records were downloaded."
            ),
        )
        submitted = st.form_submit_button("Analyze", type="primary")

    if submitted:
        st.session_state.pop("analysis_run", None)
        st.session_state.pop("analysis_error", None)
        if not incident.strip():
            st.session_state["analysis_error"] = (
                "Empty input: enter an incident description before analyzing."
            )
        else:
            try:
                with st.spinner("Retrieving policies, triaging, and reviewing…"):
                    st.session_state["analysis_run"] = triage_and_review(incident)
            except Exception as exc:  # Converted to a safe, user-facing state below.
                _record_failure(exc)

    if message := st.session_state.get("analysis_error"):
        st.error(message)

    run = st.session_state.get("analysis_run")
    if isinstance(run, ReviewedTriageRun):
        _render_result(run)


def _record_failure(exc: Exception) -> None:
    if isinstance(exc, InvalidIncidentError):
        message = (
            "Insufficient incident detail: provide at least 20 characters and no "
            "more than 5,000 characters."
        )
    elif isinstance(exc, NoPolicyContextError):
        message = (
            "Policy retrieval failed: no relevant local policy context was found. "
            "The assessment was not generated."
        )
    elif isinstance(exc, LLMUnavailableError):
        message = (
            "Ollama is unavailable or the configured local model could not be "
            "used. Start Ollama, verify OLLAMA_MODEL, and try again."
        )
    elif isinstance(exc, LLMTimeoutError):
        message = "Local model inference timed out. No assessment was accepted."
    elif isinstance(exc, LLMConfigurationError):
        message = "Local model configuration is invalid. Verify OLLAMA_MODEL and OLLAMA_HOST."
    elif isinstance(exc, (LLMMalformedResponseError, UngroundedAssessmentError)):
        message = (
            "A model response was invalid or insufficiently grounded and was not "
            "accepted. Review the local logs and try again."
        )
    elif isinstance(exc, (LLMError, TriageError)):
        message = "Analysis failed safely. No assessment was accepted."
    else:
        message = "An unexpected local error prevented analysis. No result was accepted."
    st.session_state["analysis_error"] = message


def _render_result(run: ReviewedTriageRun) -> None:
    assessment = run.triage.assessment
    review = run.review.result

    st.divider()
    st.header("Triage assessment")
    category_column, severity_column, confidence_column = st.columns(3)
    category_column.metric("Category", _display_label(assessment.category))
    severity_column.metric("Severity", _display_label(assessment.severity))
    confidence_column.metric("Confidence", _display_label(assessment.confidence))

    if assessment.confidence == "low":
        st.warning(
            "Insufficient evidence for a confident assessment. Treat the result "
            "as an investigation starting point."
        )

    st.subheader("Reasoning summary")
    st.write(assessment.reasoning_summary)

    st.subheader("Evidence")
    for evidence in assessment.evidence:
        st.write(f"• {evidence.observation}")

    st.subheader("Policies")
    st.caption("Retrieved policy documents and corpus-relative TF-IDF scores")
    for match in run.triage.retrieval_matches:
        st.write(f"• {match.source} — {match.score:.4f}")

    st.caption("Policy sections cited by the assessment")
    sections_by_key = {
        (section.source, section.section_id): section
        for section in run.triage.context_sections
    }
    for reference in assessment.relevant_policies:
        section = sections_by_key[(reference.source_filename, reference.section_id)]
        with st.expander(f"{reference.source_filename} — {section.heading}"):
            st.caption(reference.section_id)
            st.text(section.text)

    st.subheader("Recommended actions")
    if assessment.recommended_actions:
        for action in assessment.recommended_actions:
            st.write(f"• {action.action}")
            st.caption("Policy support: " + ", ".join(action.policy_section_ids))
        st.warning(
            "Human approval required. These are recommendations only; this "
            "application cannot execute remediation."
        )
    else:
        st.write("No policy-supported actions were recommended.")

    st.header("Reviewer result")
    if review.approved:
        st.success("Reviewer accepted the assessment as grounded.")
    else:
        st.error(
            "Reviewer rejected the assessment. The original assessment is shown "
            "unchanged; review the concerns before making a decision."
        )

    check_columns = st.columns(3)
    check_columns[0].metric("Factual grounding", _check_label(review.evidence_grounded))
    check_columns[1].metric("Policy grounding", _check_label(review.policy_grounded))
    check_columns[2].metric(
        "Human approval",
        _check_label(review.human_approval_correct),
    )

    if review.unsupported_claims:
        st.subheader("Unsupported claims")
        for claim in review.unsupported_claims:
            st.write(f"• {claim}")

    st.subheader("Reviewer warnings")
    if review.warnings:
        for warning in review.warnings:
            st.write(f"• {warning}")
    else:
        st.write("No reviewer warnings.")

    st.subheader("Human decision")
    if assessment.human_approval_required:
        st.warning("Human approval is required for every recommended action.")
    else:
        st.info("No actions requiring approval were proposed in this assessment.")
    st.caption(NOTICE)


def _display_label(value: str) -> str:
    return value.replace("_", " ").title()


def _check_label(passed: bool) -> str:
    return "Passed" if passed else "Failed"


if __name__ == "__main__":
    main()
