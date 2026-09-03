"""Run the small synthetic evaluation set against the real local pipeline."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.llm import OllamaLLM  # noqa: E402
from src.retrieval import retrieve_policy_documents  # noqa: E402
from src.reviewer import review_assessment  # noqa: E402
from src.triage import triage_incident  # noqa: E402


DEFAULT_CASES_PATH = PROJECT_ROOT / "evals" / "cases.json"
DEFAULT_POLICY_PATH = PROJECT_ROOT / "data" / "policies"
DEFAULT_EVAL_MODEL = "qwen3.5:9b"


@dataclass(slots=True)
class CaseOutcome:
    case_id: str
    retrieval_hit: bool
    retrieved_sources: list[str]
    triage_success: bool = False
    review_success: bool = False
    category_correct: bool | None = None
    severity_correct: bool | None = None
    approval_compliant: bool | None = None
    insufficiency_detected: bool | None = None
    actual_category: str | None = None
    actual_severity: str | None = None
    actual_confidence: str | None = None
    reviewer_outcome: str = "not_run"
    failed_reasons: list[str] = field(default_factory=list)


def load_cases(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"No evaluation cases found in {path}")
    return cases


def evaluate_case(
    case: dict[str, Any],
    *,
    llm: OllamaLLM,
    policy_directory: Path,
) -> CaseOutcome:
    expected = case["expected"]
    retrieved = retrieve_policy_documents(case["description"], policy_directory)
    retrieved_sources = [document.source for document in retrieved]
    required_sources = set(expected["required_policy_sources"])
    retrieval_hit = required_sources.issubset(retrieved_sources)
    outcome = CaseOutcome(
        case_id=case["id"],
        retrieval_hit=retrieval_hit,
        retrieved_sources=retrieved_sources,
    )
    if not retrieval_hit:
        missing = sorted(required_sources.difference(retrieved_sources))
        outcome.failed_reasons.append(
            "retrieval missed required policy source(s): " + ", ".join(missing)
        )

    try:
        triage = triage_incident(
            case["description"],
            llm=llm,
            policy_directory=policy_directory,
        )
    except Exception as exc:  # Evaluation continues and reports each failed case.
        outcome.failed_reasons.append(
            f"triage failed: {type(exc).__name__}: {exc}"
        )
        return outcome

    outcome.triage_success = True
    assessment = triage.assessment
    outcome.actual_category = assessment.category
    outcome.actual_severity = assessment.severity
    outcome.actual_confidence = assessment.confidence

    outcome.category_correct = assessment.category == expected["category"]
    if not outcome.category_correct:
        outcome.failed_reasons.append(
            f"category was {assessment.category}; expected {expected['category']}"
        )

    acceptable_severities = set(expected["acceptable_severities"])
    outcome.severity_correct = assessment.severity in acceptable_severities
    if not outcome.severity_correct:
        outcome.failed_reasons.append(
            f"severity was {assessment.severity}; expected one of "
            f"{sorted(acceptable_severities)}"
        )

    action_approvals_valid = all(
        action.human_approval_required for action in assessment.recommended_actions
    )
    outcome.approval_compliant = (
        assessment.human_approval_required
        == expected["human_approval_required"]
        and action_approvals_valid
    )
    if not outcome.approval_compliant:
        outcome.failed_reasons.append(
            "human approval was "
            f"{assessment.human_approval_required}; expected "
            f"{expected['human_approval_required']}"
        )

    if expected["insufficient_information_expected"]:
        outcome.insufficiency_detected = assessment.confidence == "low"
        if not outcome.insufficiency_detected:
            outcome.failed_reasons.append(
                "insufficient information was expected, but confidence was "
                f"{assessment.confidence} rather than low"
            )

    try:
        review = review_assessment(
            incident=triage.incident,
            policy_sections=triage.context_sections,
            assessment=assessment,
            llm=llm,
        )
    except Exception as exc:  # Preserve the valid triage metrics if review fails.
        outcome.failed_reasons.append(
            f"review failed: {type(exc).__name__}: {exc}"
        )
        outcome.reviewer_outcome = "failed"
        return outcome

    outcome.review_success = True
    result = review.result
    outcome.reviewer_outcome = "approved" if result.approved else "rejected"
    if not result.approved:
        concerns = result.unsupported_claims + result.warnings
        reason = " | ".join(concerns) if concerns else "no concern supplied"
        outcome.failed_reasons.append("reviewer rejected assessment: " + reason)
    return outcome


def print_report(outcomes: Sequence[CaseOutcome], *, model: str) -> None:
    total = len(outcomes)
    retrieval_hits = sum(outcome.retrieval_hit for outcome in outcomes)
    triage_successes = [outcome for outcome in outcomes if outcome.triage_success]
    structured_successes = [
        outcome
        for outcome in outcomes
        if outcome.triage_success and outcome.review_success
    ]

    print("\nEvaluation summary")
    print(f"Model: {model}")
    print(f"Total cases: {total}")
    print(
        "Successful structured outputs: "
        f"{len(structured_successes)}/{total}"
    )
    print(
        "Structured-output success rate: "
        f"{_percentage(len(structured_successes), total)}"
    )
    print(
        "Triage structured outputs: "
        f"{len(triage_successes)}/{total}"
    )
    print(
        "Category accuracy: "
        + _metric("category_correct", denominator=triage_successes)
    )
    print(
        "Severity accuracy: "
        + _metric("severity_correct", denominator=triage_successes)
    )
    print(
        "Policy retrieval hit rate: "
        f"{retrieval_hits}/{total} ({_percentage(retrieval_hits, total)})"
    )
    print(
        "Human-approval compliance: "
        + _metric("approval_compliant", denominator=triage_successes)
    )

    insufficiency_cases = [
        outcome
        for outcome in outcomes
        if outcome.insufficiency_detected is not None
    ]
    print(
        "Insufficient-information handling: "
        + _metric(
            "insufficiency_detected",
            denominator=insufficiency_cases,
        )
    )

    approved = sum(outcome.reviewer_outcome == "approved" for outcome in outcomes)
    rejected = sum(outcome.reviewer_outcome == "rejected" for outcome in outcomes)
    failed = sum(outcome.reviewer_outcome == "failed" for outcome in outcomes)
    not_run = sum(outcome.reviewer_outcome == "not_run" for outcome in outcomes)
    print(
        "Reviewer outcomes: "
        f"approved={approved}, rejected={rejected}, failed={failed}, not_run={not_run}"
    )

    failed_cases = [outcome for outcome in outcomes if outcome.failed_reasons]
    print(f"Failed cases: {len(failed_cases)}/{total}")
    if not failed_cases:
        print("- None")
        return
    for outcome in failed_cases:
        print(f"- {outcome.case_id}")
        for reason in outcome.failed_reasons:
            print(f"  - {reason}")


def _metric(
    attribute: str,
    *,
    denominator: Sequence[CaseOutcome],
) -> str:
    count = sum(getattr(outcome, attribute) is True for outcome in denominator)
    total = len(denominator)
    return f"{count}/{total} ({_percentage(count, total)})"


def _percentage(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "n/a"
    return f"{numerator / denominator:.1%}"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the local incident-pipeline evaluation set."
    )
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--policy-dir", type=Path, default=DEFAULT_POLICY_PATH)
    parser.add_argument(
        "--model",
        default=os.getenv("OLLAMA_MODEL", DEFAULT_EVAL_MODEL),
        help="Ollama model name (default: OLLAMA_MODEL or qwen3.5:9b)",
    )
    args = parser.parse_args(argv)

    try:
        cases = load_cases(args.cases)
        llm = OllamaLLM(model=args.model)
    except Exception as exc:
        print(f"Evaluation setup failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    outcomes: list[CaseOutcome] = []
    for index, case in enumerate(cases, start=1):
        print(f"[{index}/{len(cases)}] {case['id']}", flush=True)
        outcome = evaluate_case(
            case,
            llm=llm,
            policy_directory=args.policy_dir,
        )
        outcomes.append(outcome)
        state = (
            "structured"
            if outcome.triage_success and outcome.review_success
            else "failed"
        )
        print(
            f"  {state}; category={outcome.actual_category}; "
            f"severity={outcome.actual_severity}; "
            f"reviewer={outcome.reviewer_outcome}",
            flush=True,
        )

    print_report(outcomes, model=args.model)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
