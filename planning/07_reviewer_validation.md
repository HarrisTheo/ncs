# Reviewer Validation

## Implemented backend flow

The backend now supports:

> Incident → Retrieval → Triage Agent → Pydantic and deterministic validation → Reviewer Agent → `ReviewerResult`

`triage_and_review()` performs two distinct structured model requests through
the same replaceable LLM interface. The second request receives:

- The original validated incident description.
- Every retrieved policy passage seen by triage.
- The already validated `IncidentAssessment` serialized without modification.

The reviewer returns a separate `ReviewRun`. The original assessment remains
available and unchanged; reviewer disagreement is never merged into it or used
to silently generate a replacement.

## Reviewer responsibilities

The reviewer checks:

- Whether evidence observations and factual claims elsewhere in the assessment
  are supported by the incident or clearly labelled as inference.
- Whether policy filenames and section IDs exist in the retrieved context.
- Whether selected policy sections are relevant to the assessment.
- Whether each recommended action appears in its cited policy action section
  and retains policy conditions.
- Whether recommendations and the top-level result require human approval.
- Whether high-impact actions comply with the retrieved approval requirements
  and are not presented as automatic or completed.

`ReviewerResult` prevents approval when a grounding check is false or an
unsupported claim exists. Any rejected review must contain at least one explicit
unsupported claim or warning.

## Deterministic deliberately bad case

The test fixture manually constructs a Pydantic-valid `IncidentAssessment`.
Its schema, category, severity, confidence, references, and approval flags are
valid, but it seeds two semantic failures:

1. Fabricated factual claim:

   > The attacker exported the records to a confirmed external recipient.

   The incident reports only a download; it does not identify an attacker,
   external transfer, recipient, or confirmation.

2. Unsupported recommendation:

   > Delete the account immediately and notify every customer.

   This text is not present in the cited authentication policy action section.
   It also collapses technical containment and external notification into one
   unsupported instruction.

The deterministic test passes this exact assessment to `review_assessment()`,
uses a controlled reviewer response, and verifies that:

- `approved` is `false`.
- Factual and policy grounding failures are explicit.
- Both seeded problems appear in `unsupported_claims`.
- The exact submitted assessment is returned unchanged.
- The reviewer request contains the original incident, retrieved policy text,
  and bad assessment.

This unit test validates orchestration and non-mutation deterministically. It
does not pretend to prove that a probabilistic model will always detect the
same issue.

## Real local-model demonstration

The same deliberately bad fixture was submitted to local Ollama using
`qwen3.5:9b`, temperature zero, thinking disabled, and the Pydantic-generated
`ReviewerResult` schema.

The reviewer returned:

- `approved`: `false`
- `policy_grounded`: `false`
- `evidence_grounded`: `false`
- `human_approval_correct`: `false`

It explicitly caught:

- The unsupported claim that records went to a confirmed external recipient.
- The invalid jump from downloaded records to confirmed export/disclosure.
- The invented immediate account-deletion action.
- The unsupported instruction to notify every customer.
- The fact that the recommendation was not present in its cited policy action
  section.

Therefore, the reviewer caught the deliberately seeded failures in this run.

## Critical interpretation of the reviewer result

The reviewer was useful, but its own prose was not flawless:

- It inferred that an MFA reset meant the account remained active or usable;
  the incident does not establish that.
- It loosely described the MFA reset as satisfying unauthorized-change
  guidance even though authorization is unknown.
- It introduced a hypothetical critical-severity discussion that was not
  needed to identify the seeded failures.
- It marked `human_approval_correct` false. This is conservatively explainable
  because “immediately” can imply bypassing approval, but the bad assessment's
  structured action and top-level approval flags were both `true`.

The demonstration supports keeping the reviewer as an advisory second pass,
but not treating it as independent assurance or a truth oracle. The same local
model family can introduce new unsupported commentary while detecting errors.
The UI must show the original assessment, reviewer findings, and source material
separately for human judgment.

## Tests

The reviewer tests cover:

- Exact reviewer context construction.
- Use of the `ReviewerResult` response contract.
- Preservation of the original assessment object.
- Explicit rejection of the deliberately bad fixture.
- Separate triage and reviewer model calls in the complete backend flow.
- Rejection of unexplained negative reviewer decisions.

Full test command:

```text
.venv/bin/python -m pytest -q
```

Expected result after this change: **86 passed**.

## Remaining limitations

- A single successful bad-case run is evidence of usefulness, not a detection
  rate or reliability guarantee.
- Temperature zero improves repeatability but does not make local inference a
  formal deterministic verifier.
- The reviewer shares the triage model's likely blind spots.
- Deterministic validation still provides the strongest guarantees for exact
  evidence, policy identifiers, verbatim actions, and approval invariants.
- Broader claims in category, severity, and summary remain semantic judgments
  requiring reviewer and human scrutiny.
