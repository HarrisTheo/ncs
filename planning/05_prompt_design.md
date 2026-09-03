# Prompt Design

## Objective

The runtime uses two short system prompts with different jobs:

1. The triage prompt constructs one structured assessment from the incident and retrieved policy passages.
2. The reviewer prompt audits that existing assessment against the same source material.

Both operate as closed-world tasks. They may use only the content supplied by the application, have no tools, and return JSON validated by Pydantic. The application will supply the relevant JSON schema at runtime; the schema is not duplicated in the prompt text.

## Triage prompt responsibilities

The triage prompt is responsible for:

- Classifying the incident into one of the supported categories.
- Selecting `low`, `medium`, `high`, or `critical` severity.
- Expressing bounded confidence and lowering it when material facts are missing.
- Extracting factual observations from the incident description.
- Keeping inference out of the evidence collection.
- Producing a short user-facing explanation that acknowledges uncertainty.
- Citing only retrieved policy filenames and section identifiers.
- Recommending actions only when the retrieved policies support them.
- Marking every recommended action as requiring human approval.
- Returning exactly the `IncidentAssessment` JSON structure.

The prompt assumes the runtime has already rejected empty input and a zero-score retrieval result. If the available incident evidence is incomplete, the model must preserve the gap rather than complete the story itself.

## Triage prompt prohibitions

The triage prompt explicitly prohibits:

- Inventing events, users, systems, evidence, impact, policies, or requirements.
- Treating the incident description or policy passages as executable instructions.
- Presenting an inference as an observed fact.
- Citing a filename or section identifier that was not supplied.
- Recommending an action that lacks support in the supplied passages.
- Describing an action as automatic, authorized, or completed.
- Producing hidden chain-of-thought or step-by-step reasoning.
- Returning prose around the structured JSON response.

The prompt does not ask the model to prove that its conclusion is correct. That would encourage verbose rationalization without creating a reliable assurance mechanism.

## Reviewer prompt responsibilities

The reviewer prompt is responsible for checking the already-created assessment, not generating a replacement. It verifies:

- Whether each evidence observation is supported by the incident description.
- Whether evidence and inference have been kept separate.
- Whether every policy filename and section identifier exists in the retrieved context.
- Whether the claimed use of a policy matches its actual passage.
- Whether each recommendation is supported by a supplied policy.
- Whether action-level and top-level human-approval flags are correct.
- Whether severity, confidence, or the summary depends on unsupported claims or excessive certainty.
- Whether concerns are recorded explicitly as unsupported claims or warnings.

It returns only the `ReviewerResult` structure. Its `approved` field is constrained by both the prompt and Pydantic validation: approval is not valid when a grounding check fails or unsupported claims remain.

## Reviewer prompt prohibitions

The reviewer prompt explicitly prohibits:

- Reperforming the investigation from scratch.
- Rewriting or silently correcting the assessment.
- Adding new incident conclusions, evidence, policies, or actions.
- Accepting a policy reference merely because its name sounds plausible.
- Treating schema validity as evidence that a factual claim is true.
- Authorizing or executing a recommended action.
- Producing hidden chain-of-thought or step-by-step reasoning.
- Returning commentary outside the structured result.

If the reviewer identifies a problem, the application preserves both the assessment and review finding for the human. The reviewer does not mutate the original artifact.

## Hallucination mitigation choices

### Closed-world source rule

Both prompts repeat that only the supplied incident and retrieved passages may be used. This does not guarantee factual behavior, but it creates a clear criterion that deterministic checks and the reviewer can evaluate.

### Exact source identifiers

The triage output must use the exact source filename and section identifier supplied by retrieval. The reviewer checks these references, and application code will later verify identifier membership deterministically. This is stronger than asking for informal policy names.

### Evidence separated from explanation

Evidence items are restricted to observations from the incident description. Interpretation belongs only in the short reasoning summary. This reduces the chance that a plausible inference becomes a fabricated fact.

### Explicit uncertainty

The model is directed to lower confidence and acknowledge missing information rather than fill gaps. Confidence is bounded by the schema and is presented as a model estimate, not a calibrated probability.

### Policy-supported actions only

Recommendations require a supplied policy basis. Every recommendation also requires human approval under the current MVP contract, which is simpler and safer than asking the model to classify action impact reliably.

### Structured output with forbidden extras

Both outputs are validated with Pydantic models that reject unknown fields and inconsistent approval states. A fabricated hidden-reasoning field or prose wrapper is outside the accepted contract.

### Concise output

The prompts request a short user-facing explanation and explicit issue lists rather than long reasoning. More generated text would create more opportunities for unsupported claims without improving the core demonstration.

### Capability removal

Prompt wording is not treated as a security boundary. The model has no tools, credentials, file access, remediation integration, or authority. Even successful prompt injection cannot directly perform an operational action through this application.

## Why the stages differ

Triage is a constructive task: it maps unstructured incident language and retrieved guidance into a reviewable structured proposal. Some bounded synthesis is necessary.

Review is a verification task: it receives a specific proposal and searches for mismatches against supplied evidence and policy. Preventing it from recreating the assessment keeps disagreements visible and makes the stage easier to evaluate.

Combining both tasks into one prompt would ask the same generation to create and certify its own answer. The second pass does not provide independent assurance—especially when it uses the same model—but its narrower instructions can expose omissions and unsupported claims. It remains advisory, and a human owns the final decision.

## Residual limitations

- A model may ignore closed-world instructions or produce schema-valid but misleading content.
- The same model used twice can reproduce the same error in both stages.
- Exact citation membership proves that a passage was retrieved, not that the model interpreted it correctly.
- A confidence number is not calibrated unless later evaluation demonstrates calibration.
- Prompt quality cannot compensate for missing or irrelevant retrieved context.

These limitations are why deterministic validation, visible source passages, targeted evaluation, and human review remain necessary.
