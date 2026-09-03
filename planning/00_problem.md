# AI Incident Triage & Investigation Copilot

## Problem statement

Security and operational incidents are commonly reported as incomplete, unstructured narratives. A human investigator must turn that narrative into a usable initial assessment: identify the known facts, recognize what remains uncertain, find the relevant internal guidance, estimate severity, and decide what to investigate or recommend next.

This work is time-sensitive and cognitively demanding. Important details can be missed, conclusions can be stated with more confidence than the evidence supports, and policy guidance may be difficult to locate quickly.

The AI Incident Triage & Investigation Copilot is a local-first decision-support application that converts an incident description into a structured, policy-grounded triage brief for human review. It assists investigation and triage; it does not make the final decision or perform remediation.

The core product flow is:

> Incident → retrieval → triage → verification → human decision

## Target user

The primary user is a technical practitioner responsible for the initial handling of a security or operational incident, such as:

- A security operations analyst.
- An incident responder or security engineer.
- An IT or operations engineer handling a suspected compromise.
- A technically capable administrator in a smaller organization without a dedicated incident-response team.

The MVP is designed for one user investigating one incident at a time. It is not intended to simulate or replace a complete Security Operations Center.

## User pain point

At the start of an incident, the user must rapidly answer several questions:

- What facts are actually present in the report?
- What might those facts indicate, without confusing inference with evidence?
- Which internal policies or playbooks apply?
- How urgent could the incident be?
- What information or evidence should be collected next?
- Which actions should be considered, and which require explicit approval?

Today, the user often answers these questions manually while switching between an incident report and multiple policy documents. The result may be slow, inconsistent, difficult to audit, or overly dependent on individual experience.

## Product hypothesis

If the application retrieves relevant passages from approved local policies and uses a local language model to transform the incident narrative into a constrained, validated triage brief, then a human investigator can reach a more consistent and well-grounded initial decision with less search and synthesis effort.

This hypothesis depends on four conditions:

1. Retrieved sources are visible and traceable.
2. Observed facts, model inferences, and unknowns are kept distinct.
3. Deterministic validation constrains model output and enforces approval boundaries.
4. A human remains responsible for severity, escalation, and action decisions.

## Example user journey

1. The user enters: “An administrator account logged in from an unusual location, MFA was reset, and approximately 4,000 customer records were downloaded.”
2. The application searches local Markdown policies and playbooks and selects relevant passages about privileged-account compromise, MFA changes, suspected data exfiltration, severity, and approval requirements.
3. The triage step produces a structured draft that separates reported facts from possible interpretations, identifies missing information, recommends a severity with rationale, and suggests investigation and containment actions.
4. Deterministic verification checks the output schema, allowed values, citation references, approval flags, and a small set of explicit safety or minimum-severity rules.
5. An AI review pass identifies unsupported conclusions, missing considerations, inconsistent severity, citation problems, or unsafe recommendations.
6. The user inspects the incident, retrieved passages, triage result, validation results, and review findings in one place.
7. The user accepts or overrides the proposed severity, approves, rejects, or defers each recommendation, records notes, and optionally exports the resulting brief.
8. The application does not execute any recommended action.

## Why AI is appropriate

A language model is useful for tasks that require interpreting varied natural language and synthesizing several pieces of contextual guidance:

- Extracting events, entities, assets, accounts, and possible impact from an incident narrative.
- Classifying the likely incident type when the wording is inconsistent or incomplete.
- Relating retrieved policy passages to the reported situation.
- Separating stated facts from reasonable hypotheses and open questions.
- Generating focused investigation questions and suggested next steps.
- Explaining a proposed severity or recommendation in language a human can review.
- Reviewing a draft for omissions, overconfidence, unsupported claims, and policy inconsistencies.

AI is used as a constrained reasoning and synthesis component, not as an authority. Its output is expected to be fallible and must remain inspectable.

## What should remain deterministic

Conventional application logic should own tasks where correctness, permissions, or traceability can be expressed explicitly:

- Pydantic schema and type validation.
- Required fields, enumerations, ranges, and cross-field constraints.
- Policy document loading, metadata parsing, and passage identifiers.
- Retrieval ranking and selection for the MVP.
- Verification that every cited identifier refers to a retrieved passage.
- Explicit approval requirements for high-impact recommendations.
- A small set of clear severity and safety rules.
- Incident state and the user's final recorded decision.
- Configuration checks, error handling, and model availability checks.
- Export of the reviewed result.
- Tests and evaluation assertions.

The model must not grant authorization, execute remediation, silently modify policy, or determine that an incident is definitively resolved.

## Expected value of the MVP

The MVP should demonstrate that a small local system can:

- Turn an unstructured report into a consistent and reviewable triage artifact.
- Reduce the effort required to find relevant internal guidance.
- Make the evidence behind recommendations visible.
- Surface missing information early in the investigation.
- Reduce unsupported or unsafe recommendations through structured validation and review.
- Preserve human control over severity, escalation, and high-impact actions.
- Provide an evaluation baseline for deciding whether further investment is justified.

The MVP is successful if it proves this decision-support pattern on a small curated set of policies and representative synthetic incidents. It does not need to automate the broader incident-response lifecycle.
